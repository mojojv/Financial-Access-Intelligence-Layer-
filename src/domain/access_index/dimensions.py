"""Financial Access Index Score Entities and Aggregations."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict
from uuid import UUID, uuid4

from src.domain.shared.value_objects import DimensionKey, ScoreValue, DimensionType
from src.domain.shared.exceptions import InvalidValueObjectError


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
        residual = Decimal("1.0") - sum(weights.values())
        weights[DimensionType.ACCESS] += residual
        return cls(weights=weights)


@dataclass(frozen=True)
class FinancialDimension:
    """Immutable entity/value object representing an evaluated FAI dimension score."""
    key: DimensionKey
    score: ScoreValue
    weight: Decimal = Decimal("0.1428")
    confidence: Decimal = Decimal("1.00")


@dataclass
class FinancialScore:
    """FinancialScore Entity encapsulating overall score and dimension breakdown."""
    score_id: UUID
    profile_id: UUID
    overall_score: ScoreValue
    dimensions: Dict[DimensionKey, FinancialDimension]
    scoring_version: str
    methodology: str
    calculated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(
        cls,
        profile_id: UUID,
        overall_score: ScoreValue,
        dimensions: Dict[DimensionKey, FinancialDimension],
        scoring_version: str,
        methodology: str,
    ) -> "FinancialScore":
        return cls(
            score_id=uuid4(),
            profile_id=profile_id,
            overall_score=overall_score,
            dimensions=dimensions,
            scoring_version=scoring_version,
            methodology=methodology,
        )
