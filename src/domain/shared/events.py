"""Pure Domain Events for Event-Driven Communication."""
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4


@dataclass(frozen=True, kw_only=True)
class DomainEvent:
    """Base immutable Domain Event class."""
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True, kw_only=True)
class FinancialProfileCreated(DomainEvent):
    """Emitted when a new pseudonymous Financial Profile is registered."""
    profile_id: UUID
    wallet_address: str
    currency_code: str


@dataclass(frozen=True, kw_only=True)
class FinancialScoreCalculated(DomainEvent):
    """Emitted when FAI score is calculated."""
    profile_id: UUID
    score_id: UUID
    overall_score: Decimal
    scoring_version: str
    methodology: str


@dataclass(frozen=True, kw_only=True)
class BarrierDetected(DomainEvent):
    """Emitted when a structural financial barrier is diagnosed."""
    profile_id: UUID
    barrier_id: UUID
    barrier_code: str
    dimension: str
    severity: str


@dataclass(frozen=True, kw_only=True)
class InterventionRecommended(DomainEvent):
    """Emitted when an intervention plan is generated for a barrier."""
    profile_id: UUID
    intervention_id: UUID
    barrier_id: UUID
    intervention_type: str
    routing_policy: str


@dataclass(frozen=True, kw_only=True)
class PaymentInitiated(DomainEvent):
    """Emitted when an Open Payments intervention payment intent is dispatched."""
    profile_id: UUID
    intervention_id: UUID
    payment_intent_id: UUID
    sender_wallet: str
    receiver_wallet: str
    amount: Decimal
    asset_code: str


@dataclass(frozen=True, kw_only=True)
class PaymentCompleted(DomainEvent):
    """Emitted when an Open Payments transaction settles successfully."""
    profile_id: UUID
    payment_intent_id: UUID
    outgoing_payment_id: str
    settled_amount: Decimal
    fee_charged: Decimal
