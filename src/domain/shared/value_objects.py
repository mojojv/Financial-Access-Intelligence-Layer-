"""Shared Value Objects."""
from dataclasses import dataclass
from decimal import Decimal
from urllib.parse import urlparse
from src.domain.shared.exceptions import InvalidValueObjectError


@dataclass(frozen=True)
class Money:
    """Immutable Money Value Object."""
    amount: Decimal
    asset_code: str
    asset_scale: int = 2

    def __post_init__(self) -> None:
        if self.amount < Decimal("0"):
            raise InvalidValueObjectError("Money amount cannot be negative.")
        if not self.asset_code or len(self.asset_code.strip()) == 0:
            raise InvalidValueObjectError("Asset code cannot be empty.")
        if self.asset_scale < 0:
            raise InvalidValueObjectError("Asset scale must be non-negative.")

    def __add__(self, other: "Money") -> "Money":
        if self.asset_code != other.asset_code or self.asset_scale != other.asset_scale:
            raise InvalidValueObjectError("Cannot add Money with different asset codes or scales.")
        return Money(
            amount=self.amount + other.amount,
            asset_code=self.asset_code,
            asset_scale=self.asset_scale,
        )


@dataclass(frozen=True)
class WalletAddress:
    """Open Payments Wallet Address Value Object (e.g., https://ilp.wallet.com/alice)."""
    url: str

    def __post_init__(self) -> None:
        if not self.url.startswith("https://") and not self.url.startswith("http://localhost"):
            raise InvalidValueObjectError("Wallet Address must be a valid HTTPS URL.")
        parsed = urlparse(self.url)
        if not parsed.netloc or not parsed.path:
            raise InvalidValueObjectError("Invalid Wallet Address URL structure.")

    def __str__(self) -> str:
        return self.url
