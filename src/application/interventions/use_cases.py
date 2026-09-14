"""Intervention Use Cases."""
from typing import Any
from uuid import UUID, uuid4

from src.domain.access_index.dimensions import DimensionType
from src.domain.barriers.barriers import Barrier, BarrierCode, BarrierSeverity
from src.domain.interventions.interventions import Intervention, InterventionEngine


class RecommendInterventionsUseCase:
    """Application Use Case for generating financial intervention recommendations."""

    def __init__(self, engine: InterventionEngine | None = None) -> None:
        self.engine = engine or InterventionEngine()

    def execute(self, barrier_requests: list[dict[str, Any]]) -> dict[str, Any]:
        domain_barriers: list[Barrier] = []

        for b in barrier_requests:
            domain_barriers.append(
                Barrier(
                    barrier_id=UUID(str(b["barrier_id"])) if "barrier_id" in b else uuid4(),
                    snapshot_id=uuid4(),
                    profile_id=UUID(str(b["profile_id"])) if "profile_id" in b else uuid4(),
                    barrier_code=BarrierCode(b["barrier_code"]),
                    dimension=DimensionType(b["dimension"]),
                    severity=BarrierSeverity(b["severity"]),
                    evidence=b.get("evidence", {}),
                )
            )

        interventions: list[Intervention] = self.engine.recommend_interventions(domain_barriers)

        return {
            "interventions_count": len(interventions),
            "interventions": [
                {
                    "intervention_id": i.intervention_id,
                    "barrier_id": i.barrier_id,
                    "profile_id": i.profile_id,
                    "intervention_type": i.intervention_type.value,
                    "status": i.status.value,
                    "metadata": i.metadata,
                }
                for i in interventions
            ],
        }
