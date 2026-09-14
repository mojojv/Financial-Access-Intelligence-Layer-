"""User and FinancialProfile Domain Aggregates."""
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from src.domain.access_index.dimensions import FinancialDimension, FinancialScore
from src.domain.barriers.barriers import Barrier, BarrierCode, BarrierSeverity, BarrierState
from src.domain.shared.events import (
    BarrierDetected,
    DomainEvent,
    FinancialProfileCreated,
    FinancialScoreCalculated,
)
from src.domain.shared.value_objects import DimensionKey, ProfileID, ScoreValue, WalletAddress


@dataclass
class User:
    """User Entity representing a pseudonymous user (Zero-PII compliant)."""
    user_id: UUID
    consent_version: str
    status: str = "active"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def create_pseudonymous(cls, consent_version: str = "1.0") -> "User":
        """Factory method to generate a new pseudonymous User with UUIDv4 identity."""
        return cls(
            user_id=uuid4(),
            consent_version=consent_version,
            status="active",
        )


@dataclass
class FinancialProfile:
    """Aggregate Root managing user financial access state, score history, barriers, and domain events."""
    profile_id: ProfileID
    wallet_address: WalletAddress
    currency_code: str
    raw_features: dict[str, Any]
    latest_score: FinancialScore | None = None
    active_barriers: list[Barrier] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    _domain_events: list[DomainEvent] = field(default_factory=list, repr=False)

    @classmethod
    def create(cls, wallet_address: WalletAddress, currency_code: str = "USD") -> "FinancialProfile":
        """Factory method to register a new pseudonymous Financial Profile."""
        pid = ProfileID.generate()
        profile = cls(
            profile_id=pid,
            wallet_address=wallet_address,
            currency_code=currency_code,
            raw_features={},
        )
        profile._record_event(
            FinancialProfileCreated(
                profile_id=pid.value,
                wallet_address=wallet_address.url,
                currency_code=currency_code,
            )
        )
        return profile

    @property
    def domain_events(self) -> list[DomainEvent]:
        """Returns collected uncommitted domain events."""
        return list(self._domain_events)

    def clear_domain_events(self) -> None:
        """Clears collected domain events after dispatching."""
        self._domain_events.clear()

    def _record_event(self, event: DomainEvent) -> None:
        """Internal helper to record domain events."""
        self._domain_events.append(event)

    def update_score(
        self,
        overall_score_val: float,
        dimension_scores_map: dict[DimensionKey, float],
        methodology: str = "DETERMINISTIC_RULES",
    ) -> FinancialScore:
        """Recalculates the profile's FAI score and records FinancialScoreCalculated event."""
        dim_entities: dict[DimensionKey, FinancialDimension] = {}
        for dim_key, s_val in dimension_scores_map.items():
            dim_entities[dim_key] = FinancialDimension(
                key=dim_key,
                score=ScoreValue.from_float(s_val),
            )

        new_score = FinancialScore.create(
            profile_id=self.profile_id.value,
            overall_score=ScoreValue.from_float(overall_score_val),
            dimensions=dim_entities,
            scoring_version="v0.1-aggregate",
            methodology=methodology,
        )

        self.latest_score = new_score

        self._record_event(
            FinancialScoreCalculated(
                profile_id=self.profile_id.value,
                score_id=new_score.score_id,
                overall_score=new_score.overall_score.value,
                scoring_version=new_score.scoring_version,
                methodology=methodology,
            )
        )

        return new_score

    def record_barrier(
        self,
        barrier_code: BarrierCode,
        dimension: DimensionKey,
        severity: BarrierSeverity,
        evidence: dict[str, Any],
    ) -> Barrier:
        """Diagnoses and registers a structural barrier on the profile."""
        if not self.latest_score:
            snapshot_id = self.profile_id.value
        else:
            snapshot_id = self.latest_score.score_id

        barrier = Barrier(
            barrier_id=ProfileID.generate().value,
            snapshot_id=snapshot_id,
            profile_id=self.profile_id.value,
            barrier_code=barrier_code,
            dimension=dimension,
            severity=severity,
            evidence=evidence,
            state=BarrierState.DIAGNOSED,
        )

        self.active_barriers.append(barrier)

        self._record_event(
            BarrierDetected(
                profile_id=self.profile_id.value,
                barrier_id=barrier.barrier_id,
                barrier_code=barrier_code.value,
                dimension=dimension.value,
                severity=severity.value,
            )
        )

        return barrier
