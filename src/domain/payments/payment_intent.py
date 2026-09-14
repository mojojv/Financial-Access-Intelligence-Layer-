"""PaymentIntent Entity representing payment execution intent."""
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4

from src.domain.shared.value_objects import Money, WalletAddress


class PaymentIntentStatus(str, Enum):
    """Payment intent execution lifecycle status."""
    DRAFT = "draft"
    QUOTED = "quoted"
    AUTHORIZED = "authorized"
    SUBMITTED = "submitted"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PaymentIntent:
    """Domain Entity representing a payment execution intent over Open Payments."""
    intent_id: UUID
    sender_wallet: WalletAddress
    receiver_wallet: WalletAddress
    amount: Money
    status: PaymentIntentStatus = PaymentIntentStatus.DRAFT
    incoming_payment_url: str | None = None
    quote_url: str | None = None
    outgoing_payment_url: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def create(
        cls,
        sender_wallet: WalletAddress,
        receiver_wallet: WalletAddress,
        amount: Money,
    ) -> "PaymentIntent":
        return cls(
            intent_id=uuid4(),
            sender_wallet=sender_wallet,
            receiver_wallet=receiver_wallet,
            amount=amount,
            status=PaymentIntentStatus.DRAFT,
        )
