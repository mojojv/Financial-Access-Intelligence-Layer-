"""Pure Domain Value Objects (Immutable, Side-Effect Free)."""
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from urllib.parse import urlparse
from uuid import UUID, uuid4

from src.domain.shared.exceptions import (
    InvalidDimensionScoreError,
    InvalidValueObjectError,
    InvalidWalletAddressError,
)


@dataclass(frozen=True)
class ProfileID:
    """Strongly-typed Value Object wrapping a pseudonymous user Profile UUID."""
    value: UUID

    @classmethod
    def generate(cls) -> "ProfileID":
        """Factory method to generate a new pseudonymous ProfileID."""
        return cls(value=uuid4())

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class ScoreValue:
    """Immutable Value Object enforcing score constraints within [0.00, 100.00]."""
    value: Decimal

    def __post_init__(self) -> None:
        if not (Decimal("0.00") <= self.value <= Decimal("100.00")):
            raise InvalidDimensionScoreError(
                f"ScoreValue must be between 0.00 and 100.00, got {self.value}"
            )

    @classmethod
    def from_float(cls, float_val: float) -> "ScoreValue":
        """Factory constructor converting float to quantized Decimal score."""
        dec_val = Decimal(str(round(float_val, 2)))
        return cls(value=dec_val)

    def __str__(self) -> str:
        return f"{self.value:.2f}"


@dataclass(frozen=True)
class WalletAddress:
    """Value Object encapsulating a validated Interledger Open Payments Wallet Address URL."""
    url: str

    def __post_init__(self) -> None:
        if not self.url.startswith("https://") and not self.url.startswith("http://localhost"):
            raise InvalidWalletAddressError(f"Wallet address must be a valid HTTPS URL: {self.url}")
        parsed = urlparse(self.url)
        if not parsed.netloc or not parsed.path:
            raise InvalidWalletAddressError(f"Invalid Wallet Address structure: {self.url}")

    def __str__(self) -> str:
        return self.url


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


class DimensionKey(str, Enum):
    """The 7 Core Dimensions of the Financial Access Index."""
    ACCESS = "access"
    CONNECTIVITY = "connectivity"
    AFFORDABILITY = "affordability"
    RELIABILITY = "reliability"
    INTEROPERABILITY = "interoperability"
    USAGE = "usage"
    RESILIENCE = "resilience"


# Alias for backward compatibility
DimensionType = DimensionKey


class BarrierCode(str, Enum):
    """Catalog of detectable structural financial barriers."""
    HIGH_FEE_BURDEN = "BAR_AFF_01"              # Affordability constraint
    LOW_INTEROPERABILITY = "BAR_INT_02"         # Cross-asset conversion constraint
    LOW_RESILIENCE = "BAR_RES_03"               # Liquidity reserve constraint
    UNRELIABLE_CONNECTIVITY = "BAR_CON_04"      # High latency or packet drop constraint
    LIMITED_ACCESS = "BAR_ACC_05"               # Wallet unreachability constraint
    LOW_USAGE = "BAR_USG_06"                    # Inactive telemetry constraint
    UNRELIABLE_SETTLEMENT = "BAR_REL_07"        # Settlement fulfillment constraint
