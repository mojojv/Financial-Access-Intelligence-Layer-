"""Barrier Entity and Severity Classifications."""
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from src.domain.access_index.dimensions import DimensionType
from src.domain.shared.value_objects import BarrierCode as BarrierCode, DimensionKey


class BarrierSeverity(str, Enum):
    """Classification of barrier impact severity."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class BarrierState(str, Enum):
    """Lifecycle state of a barrier."""
    DIAGNOSED = "diagnosed"
    MITIGATING = "mitigating"
    RESOLVED = "resolved"
    IGNORED = "ignored"


@dataclass
class Barrier:
    """Barrier Entity representing a diagnosed financial obstacle."""
    barrier_id: UUID
    snapshot_id: UUID
    profile_id: UUID
    barrier_code: BarrierCode
    dimension: DimensionKey
    severity: BarrierSeverity
    evidence: dict[str, Any]
    state: BarrierState = BarrierState.DIAGNOSED
    detected_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def resolve(self) -> None:
        """Transitions barrier state to RESOLVED."""
        self.state = BarrierState.RESOLVED

    def start_mitigation(self) -> None:
        """Transitions barrier state to MITIGATING."""
        self.state = BarrierState.MITIGATING


class BarrierDetectionService:
    """Domain Service that evaluates an FAI Score snapshot against rule specifications to detect barriers."""

    def detect_barriers(self, fai_score: Any) -> list[Barrier]:
        barriers: list[Barrier] = []

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
