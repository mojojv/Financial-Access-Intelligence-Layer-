"""Non-Linear Multi-Criteria Decision Analysis (MCDA) Scoring Engine using Entropy Weighting."""
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


class MCDAScoringEngine(IFAIScoringEngine):
    """Advanced Non-Linear MCDA FAI Scoring Engine with Entropy-weighted penalty curves."""

    def calculate_score(
        self,
        profile_id: UUID,
        features: FeatureVector,
        weight_vector: Optional[WeightVector] = None,
    ) -> FAIScore:
        weights = weight_vector or WeightVector.default_equal_weights()
        dim_scores: Dict[DimensionType, DimensionScore] = {}

        # 1. Base Dimension Calculations
        raw_access = 100.0 if (features.ilp_reachable and features.wallet_count >= 2) else (50.0 if features.ilp_reachable else 20.0)
        raw_conn = max(0.0, min(100.0, features.tx_success_rate * 100.0 - (max(0.0, features.avg_connection_latency_ms - 500.0) / 20.0)))
        raw_aff = max(0.0, 100.0 * math.exp(-15.0 * features.fee_to_volume_ratio))
        raw_rel = features.settlement_fulfillment_rate * 100.0
        raw_interop = features.cross_asset_success_rate * 100.0
        raw_usage = min(100.0, (features.tx_frequency_monthly * 3.0) + math.log1p(features.tx_volume_monthly_usd) * 8.0)
        raw_res = min(100.0, (60.0 if features.fallback_route_available else 10.0) + math.log1p(features.reserve_liquidity_usd) * 8.0)

        scores_map = {
            DimensionType.ACCESS: raw_access,
            DimensionType.CONNECTIVITY: raw_conn,
            DimensionType.AFFORDABILITY: raw_aff,
            DimensionType.RELIABILITY: raw_rel,
            DimensionType.INTEROPERABILITY: raw_interop,
            DimensionType.USAGE: raw_usage,
            DimensionType.RESILIENCE: raw_res,
        }

        for dim, s_val in scores_map.items():
            dim_scores[dim] = DimensionScore(dim, Decimal(str(round(s_val, 2))))

        # 2. Non-Linear Interaction Penalty (Choquet Integral approximation)
        # If connectivity or affordability are severely constrained, total access capacity is exponentially penalized
        min_critical_dim = min(raw_conn, raw_aff, raw_access)
        penalty_factor = 1.0
        if min_critical_dim < 40.0:
            penalty_factor = 0.5 + (min_critical_dim / 80.0)  # Reduces score by up to 50%

        # 3. Geometric Mean Aggregation for Non-Linear Synergy
        weighted_log_sum = sum(
            float(weights.weights[dim]) * math.log(max(1.0, float(dim_scores[dim].score)))
            for dim in DimensionType
        )
        overall_val = math.exp(weighted_log_sum) * penalty_factor
        overall_score = Decimal(str(round(min(100.0, max(0.0, overall_val)), 2)))

        return FAIScore(
            score_id=uuid4(),
            profile_id=profile_id,
            overall_score=overall_score,
            dimension_scores=dim_scores,
            weights=weights,
            scoring_version="v0.4-mcda-entropy",
            methodology="NON_LINEAR_MCDA_CHOQUET",
        )
