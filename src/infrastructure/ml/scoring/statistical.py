"""Statistical Cohort Scoring Engine Implementation for FAI (Phase 2 Evolution)."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Optional
from uuid import UUID, uuid4
import math

from src.domain.access_index.dimensions import (
    DimensionScore,
    DimensionType,
    WeightVector,
)
from src.domain.access_index.scoring import (
    FAIScore,
    FeatureVector,
    IFAIScoringEngine,
)


@dataclass(frozen=True)
class CohortBenchmark:
    """Statistical distribution parameters (mean and std dev) for cohort normalization."""
    mean: float
    std_dev: float


class StatisticalScoringEngine(IFAIScoringEngine):
    """Statistical FAI Scoring Engine using Z-score normalization against cohort benchmarks."""

    def __init__(self, benchmarks: Optional[Dict[DimensionType, CohortBenchmark]] = None) -> None:
        # Default global cohort benchmarks
        self._benchmarks = benchmarks or {
            DimensionType.ACCESS: CohortBenchmark(mean=50.0, std_dev=20.0),
            DimensionType.CONNECTIVITY: CohortBenchmark(mean=75.0, std_dev=15.0),
            DimensionType.AFFORDABILITY: CohortBenchmark(mean=60.0, std_dev=25.0),
            DimensionType.RELIABILITY: CohortBenchmark(mean=80.0, std_dev=10.0),
            DimensionType.INTEROPERABILITY: CohortBenchmark(mean=65.0, std_dev=20.0),
            DimensionType.USAGE: CohortBenchmark(mean=40.0, std_dev=20.0),
            DimensionType.RESILIENCE: CohortBenchmark(mean=45.0, std_dev=22.0),
        }

    def _z_to_score(self, raw_val: float, benchmark: CohortBenchmark) -> Decimal:
        """Converts raw metric to Z-score and maps to 0-100 percentile score using Sigmoid distribution."""
        if benchmark.std_dev == 0:
            z = 0.0
        else:
            z = (raw_val - benchmark.mean) / benchmark.std_dev

        # Sigmoid mapping: 1 / (1 + e^-z) -> scaled to 0-100
        sigmoid_val = 1.0 / (1.0 + math.exp(-z))
        score_val = round(sigmoid_val * 100.0, 2)
        return Decimal(str(score_val))

    def calculate_score(
        self,
        profile_id: UUID,
        features: FeatureVector,
        weight_vector: Optional[WeightVector] = None,
    ) -> FAIScore:
        weights = weight_vector or WeightVector.default_equal_weights()
        dim_scores: Dict[DimensionType, DimensionScore] = {}

        # Raw dimension values
        raw_access = float(features.wallet_count * 25 + (50 if features.ilp_reachable else 0))
        raw_conn = features.tx_success_rate * 100.0
        raw_aff = max(0.0, 100.0 - (features.fee_to_volume_ratio * 1000.0))
        raw_rel = features.settlement_fulfillment_rate * 100.0
        raw_interop = features.cross_asset_success_rate * 100.0
        raw_usage = float(features.tx_frequency_monthly * 5 + int(features.tx_volume_monthly_usd / 10))
        raw_res = (40.0 if features.fallback_route_available else 0.0) + (features.reserve_liquidity_usd / 10.0)

        raw_map = {
            DimensionType.ACCESS: raw_access,
            DimensionType.CONNECTIVITY: raw_conn,
            DimensionType.AFFORDABILITY: raw_aff,
            DimensionType.RELIABILITY: raw_rel,
            DimensionType.INTEROPERABILITY: raw_interop,
            DimensionType.USAGE: raw_usage,
            DimensionType.RESILIENCE: raw_res,
        }

        for dim, raw_v in raw_map.items():
            bm = self._benchmarks[dim]
            score_dec = self._z_to_score(raw_v, bm)
            dim_scores[dim] = DimensionScore(dim, score_dec)

        overall = sum(dim_scores[dim].score * weights.weights[dim] for dim in DimensionType)

        return FAIScore(
            score_id=uuid4(),
            profile_id=profile_id,
            overall_score=overall.quantize(Decimal("0.01")),
            dimension_scores=dim_scores,
            weights=weights,
            scoring_version="v0.2-statistical-zscore",
            methodology="STATISTICAL_COHORT_NORMALIZATION",
        )
