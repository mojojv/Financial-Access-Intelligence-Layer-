"""InterventionPlan Value Object, Strategies and Intervention Domain Entities."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from src.domain.barriers.barriers import Barrier, BarrierCode
from src.domain.shared.exceptions import InvalidStateTransitionError


class InterventionType(str, Enum):
    """Catalog of supported financial interventions."""
    FEE_OPTIMIZED_ROUTE = "fee_optimized_route"
    CROSS_ASSET_BRIDGE = "cross_asset_bridge"
    RESERVE_AUTO_ALLOCATION = "reserve_auto_allocation"
    ASYNC_RETRY_POLICY = "async_retry_policy"
    WALLETS_DISCOVERY_PROMPT = "wallets_discovery_prompt"


class InterventionStatus(str, Enum):
    """Lifecycle status of an intervention."""
    RECOMMENDED = "recommended"
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class InterventionPlan:
    """Immutable Value Object defining an action plan to resolve a barrier."""
    action: InterventionType
    routing_policy: str
    target_metric_gain: float
    description: str


@dataclass
class Intervention:
    """Intervention entity managing intervention execution lifecycle."""
    intervention_id: UUID
    barrier_id: UUID
    profile_id: UUID
    intervention_type: InterventionType
    status: InterventionStatus
    metadata: Dict[str, Any]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def transition_to(self, new_status: InterventionStatus) -> None:
        """Enforces aggregate state transition invariants."""
        allowed = {
            InterventionStatus.RECOMMENDED: [InterventionStatus.PENDING, InterventionStatus.FAILED],
            InterventionStatus.PENDING: [InterventionStatus.EXECUTING, InterventionStatus.FAILED],
            InterventionStatus.EXECUTING: [InterventionStatus.COMPLETED, InterventionStatus.FAILED],
            InterventionStatus.COMPLETED: [],
            InterventionStatus.FAILED: [],
        }
        if new_status not in allowed[self.status]:
            raise InvalidStateTransitionError(
                f"Cannot transition Intervention from {self.status} to {new_status}"
            )
        self.status = new_status


@dataclass
class InterventionOutcome:
    """Quantifies post-intervention financial access score deltas and savings."""
    outcome_id: UUID
    intervention_id: UUID
    pre_fai_score: Decimal
    post_fai_score: Decimal
    score_delta: Decimal
    cost_saved_usd: Decimal
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class IInterventionStrategy(ABC):
    """Strategy Interface for intervention policy implementations."""

    @abstractmethod
    def can_handle(self, barrier: Barrier) -> bool:
        """Determines if strategy applies to the given barrier."""
        pass

    @abstractmethod
    def recommend(self, barrier: Barrier) -> Intervention:
        """Generates an intervention recommendation for the given barrier."""
        pass


class FeeOptimizedRouteStrategy(IInterventionStrategy):
    """Intervention Strategy for HIGH_FEE_BURDEN barriers."""

    def can_handle(self, barrier: Barrier) -> bool:
        return barrier.barrier_code == BarrierCode.HIGH_FEE_BURDEN

    def recommend(self, barrier: Barrier) -> Intervention:
        return Intervention(
            intervention_id=uuid4(),
            barrier_id=barrier.barrier_id,
            profile_id=barrier.profile_id,
            intervention_type=InterventionType.FEE_OPTIMIZED_ROUTE,
            status=InterventionStatus.RECOMMENDED,
            metadata={
                "routing_policy": "FEE_MINIMIZATION",
                "max_allowed_fee_pct": 0.005,
                "description": "Route Open Payments transaction via lowest fee ILP liquidity provider.",
            },
        )


class CrossAssetBridgeStrategy(IInterventionStrategy):
    """Intervention Strategy for LOW_INTEROPERABILITY barriers."""

    def can_handle(self, barrier: Barrier) -> bool:
        return barrier.barrier_code == BarrierCode.LOW_INTEROPERABILITY

    def recommend(self, barrier: Barrier) -> Intervention:
        return Intervention(
            intervention_id=uuid4(),
            barrier_id=barrier.barrier_id,
            profile_id=barrier.profile_id,
            intervention_type=InterventionType.CROSS_ASSET_BRIDGE,
            status=InterventionStatus.RECOMMENDED,
            metadata={
                "bridge_mode": "MULTI_HOP_ILP_STREAM",
                "description": "Utilize automated multi-asset conversion bridge.",
            },
        )


class InterventionEngine:
    """Intervention Engine orchestrator using dynamic strategy registry."""

    def __init__(self, strategies: Optional[List[IInterventionStrategy]] = None) -> None:
        self._strategies: List[IInterventionStrategy] = strategies or [
            FeeOptimizedRouteStrategy(),
            CrossAssetBridgeStrategy(),
        ]

    def register_strategy(self, strategy: IInterventionStrategy) -> None:
        self._strategies.append(strategy)

    def recommend_interventions(self, barriers: List[Barrier]) -> List[Intervention]:
        interventions: List[Intervention] = []

        for barrier in barriers:
            for strategy in self._strategies:
                if strategy.can_handle(barrier):
                    interventions.append(strategy.recommend(barrier))
                    break

        return interventions
