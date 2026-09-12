"""Financial Access Index Dimension Definitions and Value Objects."""
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Dict
from src.domain.shared.exceptions import InvalidValueObjectError


class DimensionType(str, Enum):
    """The 7 Core Dimensions of the Financial Access Index."""
    ACCESS = "access"
    CONNECTIVITY = "connectivity"
    AFFORDABILITY = "affordability"
    RELIABILITY = "reliability"
    INTEROPERABILITY = "interoperability"
    USAGE = "usage"
    RESILIENCE = "resilience"


@dataclass(frozen=True)
class DimensionScore:
    """Score for a specific FAI dimension (0.0 to 100.0 scale)."""
    dimension: DimensionType
    score: Decimal
    confidence: Decimal = Decimal("1.0")

    def __post_init__(self) -> None:
        if not (Decimal("0") <= self.score <= Decimal("100")):
            raise InvalidValueObjectError(f"Dimension score for {self.dimension} must be between 0 and 100.")
        if not (Decimal("0") <= self.confidence <= Decimal("1.0")):
            raise InvalidValueObjectError(f"Confidence score for {self.dimension} must be between 0 and 1.")


@dataclass(frozen=True)
class WeightVector:
    """Normalized weight vector for FAI calculation."""
    weights: Dict[DimensionType, Decimal]

    def __post_init__(self) -> None:
        missing = set(DimensionType) - set(self.weights.keys())
        if missing:
            raise InvalidValueObjectError(f"Weight vector missing dimensions: {missing}")

        total_weight = sum(self.weights.values())
        if abs(total_weight - Decimal("1.0")) > Decimal("0.001"):
            raise InvalidValueObjectError(f"Weight vector sum must equal 1.0 (got {total_weight}).")

    @classmethod
    def default_equal_weights(cls) -> "WeightVector":
        """Returns equal weights (1/7 for each dimension)."""
        equal_w = Decimal("1.0") / Decimal(len(DimensionType))
        weights = {dim: equal_w for dim in DimensionType}
        # adjust small rounding residual on first dimension
        residual = Decimal("1.0") - sum(weights.values())
        weights[DimensionType.ACCESS] += residual
        return cls(weights=weights)
