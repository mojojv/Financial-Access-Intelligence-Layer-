"""Financial Barrier Domain Entities and Detection Logic."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List
from uuid import UUID, uuid4

from src.domain.access_index.dimensions import DimensionType
from src.domain.access_index.scoring import FAIScore


class BarrierSeverity(str, Enum):
    """Barrier severity classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class BarrierCode(str, Enum):
    """Catalog of detectable financial access barriers."""
    HIGH_FEE_BURDEN = "BAR_AFF_01"              # Fee ratio > 2.5%
    LOW_INTEROPERABILITY = "BAR_INT_02"         # Cross-asset failure > 30%
    LOW_RESILIENCE = "BAR_RES_03"               # Liquidity reserve < 20
    UNRELIABLE_CONNECTIVITY = "BAR_CON_04"      # Success rate < 70% or high latency
    LIMITED_ACCESS = "BAR_ACC_05"               # No active wallet address reachability
    LOW_USAGE = "BAR_USG_06"                    # Inactive wallet telemetry


@dataclass
class Barrier:
    """Barrier entity representing a diagnosed financial obstacle."""
    barrier_id: UUID
    snapshot_id: UUID
    profile_id: UUID
    barrier_code: BarrierCode
    dimension: DimensionType
    severity: BarrierSeverity
    evidence: Dict[str, Any]
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class BarrierDetectionService:
    """Domain Service that evaluates an FAI Score snapshot against rule specifications to detect barriers."""

    def detect_barriers(self, fai_score: FAIScore) -> List[Barrier]:
        barriers: List[Barrier] = []

        # 1. Evaluate Affordability
        aff_score = fai_score.dimension_scores[DimensionType.AFFORDABILITY].score
        if aff_score < 40:
            barriers.append(
                Barrier(
                    barrier_id=uuid4(),
                    snapshot_id=fai_score.score_id,
                    profile_id=fai_score.profile_id,
                    barrier_code=BarrierCode.HIGH_FEE_BURDEN,
                    dimension=DimensionType.AFFORDABILITY,
                    severity=BarrierSeverity.HIGH if aff_score < 20 else BarrierSeverity.MEDIUM,
                    evidence={"affordability_score": str(aff_score), "threshold": 40},
                )
            )

        # 2. Evaluate Interoperability
        int_score = fai_score.dimension_scores[DimensionType.INTEROPERABILITY].score
        if int_score < 45:
            barriers.append(
                Barrier(
                    barrier_id=uuid4(),
                    snapshot_id=fai_score.score_id,
                    profile_id=fai_score.profile_id,
                    barrier_code=BarrierCode.LOW_INTEROPERABILITY,
                    dimension=DimensionType.INTEROPERABILITY,
                    severity=BarrierSeverity.HIGH if int_score < 25 else BarrierSeverity.MEDIUM,
                    evidence={"interoperability_score": str(int_score), "threshold": 45},
                )
            )

        # 3. Evaluate Resilience
        res_score = fai_score.dimension_scores[DimensionType.RESILIENCE].score
        if res_score < 35:
            barriers.append(
                Barrier(
                    barrier_id=uuid4(),
                    snapshot_id=fai_score.score_id,
                    profile_id=fai_score.profile_id,
                    barrier_code=BarrierCode.LOW_RESILIENCE,
                    dimension=DimensionType.RESILIENCE,
                    severity=BarrierSeverity.MEDIUM,
                    evidence={"resilience_score": str(res_score), "threshold": 35},
                )
            )

        # 4. Evaluate Connectivity
        conn_score = fai_score.dimension_scores[DimensionType.CONNECTIVITY].score
        if conn_score < 50:
            barriers.append(
                Barrier(
                    barrier_id=uuid4(),
                    snapshot_id=fai_score.score_id,
                    profile_id=fai_score.profile_id,
                    barrier_code=BarrierCode.UNRELIABLE_CONNECTIVITY,
                    dimension=DimensionType.CONNECTIVITY,
                    severity=BarrierSeverity.HIGH if conn_score < 30 else BarrierSeverity.MEDIUM,
                    evidence={"connectivity_score": str(conn_score), "threshold": 50},
                )
            )

        # 5. Evaluate Access
        acc_score = fai_score.dimension_scores[DimensionType.ACCESS].score
        if acc_score < 50:
            barriers.append(
                Barrier(
                    barrier_id=uuid4(),
                    snapshot_id=fai_score.score_id,
                    profile_id=fai_score.profile_id,
                    barrier_code=BarrierCode.LIMITED_ACCESS,
                    dimension=DimensionType.ACCESS,
                    severity=BarrierSeverity.CRITICAL if acc_score == 0 else BarrierSeverity.HIGH,
                    evidence={"access_score": str(acc_score), "threshold": 50},
                )
            )

        return barriers
