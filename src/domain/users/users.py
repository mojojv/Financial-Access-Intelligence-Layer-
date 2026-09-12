"""Pseudonymous User and Financial Profile Domain Aggregates."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from src.domain.shared.value_objects import WalletAddress


@dataclass
class User:
    """User Entity representing a pseudonymous user (Zero-PII compliant)."""
    user_id: UUID
    consent_version: str
    status: str = "active"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

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
    """FinancialProfile aggregate storing pseudonymous indicators and telemetry vectors."""
    profile_id: UUID
    user_id: UUID
    wallet_address: WalletAddress
    currency_code: str
    raw_features: Dict[str, Any]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def update_features(self, new_features: Dict[str, Any]) -> None:
        """Updates feature telemetry vector."""
        self.raw_features.update(new_features)
        self.updated_at = datetime.now(timezone.utc)
