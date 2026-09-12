"""Application Data Transfer Objects (DTOs)."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List
from uuid import UUID


@dataclass(frozen=True)
class CalculateFAIScoreRequestDTO:
    profile_id: UUID
    wallet_count: int
    ilp_reachable: bool
    tx_success_rate: float
    avg_connection_latency_ms: float
    fee_to_volume_ratio: float
    settlement_fulfillment_rate: float
    cross_asset_success_rate: float
    tx_frequency_monthly: int
    tx_volume_monthly_usd: float
    reserve_liquidity_usd: float
    fallback_route_available: bool
    methodology: str = "DETERMINISTIC_RULES"


@dataclass(frozen=True)
class BarrierResponseDTO:
    barrier_id: UUID
    barrier_code: str
    dimension: str
    severity: str
    evidence: Dict[str, Any]


@dataclass(frozen=True)
class FAIScoreResponseDTO:
    score_id: UUID
    profile_id: UUID
    overall_score: float
    dimension_scores: Dict[str, float]
    barriers: List[BarrierResponseDTO]
    scoring_version: str
    methodology: str
    calculated_at: str


@dataclass(frozen=True)
class InterventionResponseDTO:
    intervention_id: UUID
    barrier_id: UUID
    profile_id: UUID
    intervention_type: str
    status: str
    metadata: Dict[str, Any]
