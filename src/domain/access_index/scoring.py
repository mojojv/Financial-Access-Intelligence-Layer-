"""Financial Access Index Scoring Architecture and Strategy Interfaces."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from src.domain.access_index.dimensions import (
    DimensionScore,
    DimensionType,
    WeightVector,
)
from src.domain.shared.exceptions import InvalidValueObjectError


@dataclass(frozen=True)
class FeatureVector:
    """Normalized feature vector extracted from raw financial profile telemetry."""
    wallet_count: int                        # Access
    ilp_reachable: bool                     # Access
    tx_success_rate: float                   # Connectivity (0.0 - 1.0)
    avg_connection_latency_ms: float         # Connectivity
    fee_to_volume_ratio: float               # Affordability (e.g., 0.02 = 2%)
    settlement_fulfillment_rate: float       # Reliability (0.0 - 1.0)
    cross_asset_success_rate: float          # Interoperability (0.0 - 1.0)
    tx_frequency_monthly: int                # Usage
    tx_volume_monthly_usd: float             # Usage
    reserve_liquidity_usd: float             # Resilience
    fallback_route_available: bool           # Resilience


@dataclass
class FAIScore:
    """FAIScore Entity representing a calculated point-in-time Financial Access Index snapshot."""
    score_id: UUID
    profile_id: UUID
    overall_score: Decimal
    dimension_scores: dict[DimensionType, DimensionScore]
    weights: WeightVector
    scoring_version: str
    methodology: str
    calculated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if not (Decimal("0") <= self.overall_score <= Decimal("100")):
            raise InvalidValueObjectError("Overall FAI score must be between 0 and 100.")


class IFAIScoringEngine(ABC):
    """Abstract Strategy Interface for FAI Scoring Engine implementations (Rules, Stats, ML)."""

    @abstractmethod
    def calculate_score(
        self,
        profile_id: UUID,
        features: FeatureVector,
        weight_vector: WeightVector | None = None,
    ) -> FAIScore:
        """Calculates FAI overall and dimension scores from raw features."""
        pass


class DeterministicRuleScoringEngine(IFAIScoringEngine):
    """MVP Implementation: Transparent, deterministic rule-based FAI scoring strategy."""

    def calculate_score(
        self,
        profile_id: UUID,
        features: FeatureVector,
        weight_vector: WeightVector | None = None,
    ) -> FAIScore:
        weights = weight_vector or WeightVector.default_equal_weights()

        dim_scores: dict[DimensionType, DimensionScore] = {}

        # 1. Access: Wallets and ILP Reachability
        access_val = Decimal("0")
        if features.ilp_reachable:
            access_val += Decimal("50")
        access_val += Decimal(min(features.wallet_count * 25, 50))
        dim_scores[DimensionType.ACCESS] = DimensionScore(DimensionType.ACCESS, access_val)

        # 2. Connectivity: Success rate & latency penalty
        conn_val = Decimal(str(min(max(features.tx_success_rate * 100, 0), 100)))
        if features.avg_connection_latency_ms > 2000:
            conn_val = max(Decimal("0"), conn_val - Decimal("20"))
        dim_scores[DimensionType.CONNECTIVITY] = DimensionScore(DimensionType.CONNECTIVITY, conn_val)

        # 3. Affordability: Inverse fee burden (0% fee -> 100 score, >= 10% fee -> 0 score)
        fee_ratio = Decimal(str(features.fee_to_volume_ratio))
        afford_val = max(Decimal("0"), Decimal("100") - (fee_ratio * Decimal("1000")))
        dim_scores[DimensionType.AFFORDABILITY] = DimensionScore(DimensionType.AFFORDABILITY, min(afford_val, Decimal("100")))

        # 4. Reliability: Fulfillment rate
        rel_val = Decimal(str(min(max(features.settlement_fulfillment_rate * 100, 0), 100)))
        dim_scores[DimensionType.RELIABILITY] = DimensionScore(DimensionType.RELIABILITY, rel_val)

        # 5. Interoperability: Cross-asset settlement success
        interop_val = Decimal(str(min(max(features.cross_asset_success_rate * 100, 0), 100)))
        dim_scores[DimensionType.INTEROPERABILITY] = DimensionScore(DimensionType.INTEROPERABILITY, interop_val)

        # 6. Usage: Frequency & volume scale
        freq_score = min(features.tx_frequency_monthly * 5, 50)
        vol_score = min(int(features.tx_volume_monthly_usd / 10), 50)
        usage_val = Decimal(str(freq_score + vol_score))
        dim_scores[DimensionType.USAGE] = DimensionScore(DimensionType.USAGE, usage_val)

        # 7. Resilience: Reserve liquidity & fallback availability
        res_val = Decimal("0")
        if features.fallback_route_available:
            res_val += Decimal("40")
        res_val += Decimal(str(min(features.reserve_liquidity_usd / 10, 60)))
        dim_scores[DimensionType.RESILIENCE] = DimensionScore(DimensionType.RESILIENCE, min(res_val, Decimal("100")))

        # Weighted Composite Score
        overall = sum(dim_scores[dim].score * weights.weights[dim] for dim in DimensionType)

        return FAIScore(
            score_id=uuid4(),
            profile_id=profile_id,
            overall_score=overall.quantize(Decimal("0.01")),
            dimension_scores=dim_scores,
            weights=weights,
            scoring_version="v0.1-rule-based",
            methodology="DETERMINISTIC_RULES",
        )
