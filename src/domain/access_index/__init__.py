"""Financial Access Index Domain Package."""
from src.domain.access_index.dimensions import (
    DimensionScore,
    DimensionType,
    WeightVector,
)
from src.domain.access_index.scoring import (
    DeterministicRuleScoringEngine,
    FAIScore,
    FeatureVector,
    IFAIScoringEngine,
)

__all__ = [
    "DeterministicRuleScoringEngine",
    "DimensionScore",
    "DimensionType",
    "FAIScore",
    "FeatureVector",
    "IFAIScoringEngine",
    "WeightVector",
]
