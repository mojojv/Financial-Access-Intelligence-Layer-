"""Abstract Weighting Strategies for Financial Access Index Calculation."""
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict
from src.domain.access_index.dimensions import FinancialDimension, WeightVector
from src.domain.shared.value_objects import DimensionKey, ScoreValue
from src.domain.shared.exceptions import InvalidValueObjectError


class WeightingStrategy(ABC):
    """Abstract Strategy Interface for weighting dimension scores into a composite FAI Score."""

    @abstractmethod
    def compute_composite_score(
        self,
        dimensions: Dict[DimensionKey, FinancialDimension],
        weight_vector: WeightVector,
    ) -> ScoreValue:
        """Computes the overall composite FAI ScoreValue (0.00 to 100.00)."""
        pass


class DeterministicLinearWeightingStrategy(WeightingStrategy):
    """Initial Strategy: Linear weighted combination of dimension scores."""

    def compute_composite_score(
        self,
        dimensions: Dict[DimensionKey, FinancialDimension],
        weight_vector: WeightVector,
    ) -> ScoreValue:
        if not dimensions:
            raise InvalidValueObjectError("Cannot compute composite score with empty dimensions dictionary.")

        composite_val = Decimal("0.00")
        for dim_key, dim_entity in dimensions.items():
            weight = weight_vector.weights.get(dim_key, Decimal("0.00"))
            composite_val += dim_entity.score.value * weight

        # Quantize to 2 decimal places and return validated ScoreValue
        final_val = min(Decimal("100.00"), max(Decimal("0.00"), composite_val))
        return ScoreValue(value=final_val.quantize(Decimal("0.01")))


class PCAStatisticalWeightingStrategy(WeightingStrategy):
    """Phase 2 Strategy: Principal Component Analysis (PCA) variance-weighted aggregation."""

    def compute_composite_score(
        self,
        dimensions: Dict[DimensionKey, FinancialDimension],
        weight_vector: WeightVector,
    ) -> ScoreValue:
        # Variance-weighted PCA formulation simulation
        weights = weight_vector.weights
        total_variance_explained = sum(weights.values())
        if total_variance_explained == 0:
            return ScoreValue(Decimal("0.00"))

        pca_sum = sum(dim.score.value * (weights[k] / total_variance_explained) for k, dim in dimensions.items())
        final_val = min(Decimal("100.00"), max(Decimal("0.00"), pca_sum))
        return ScoreValue(value=final_val.quantize(Decimal("0.01")))
