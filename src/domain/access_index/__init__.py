"""Financial Access Index Domain Package."""
from src.domain.access_index.dimensions import (
    DimensionType,
    DimensionScore,
    WeightVector,
)
from src.domain.access_index.scoring import (
    FeatureVector,
    FAIScore,
    IFAIScoringEngine,
    DeterministicRuleScoringEngine,
)

__all__ = [
    "DimensionType",
    "DimensionScore",
    "WeightVector",
    "FeatureVector",
    "FAIScore",
    "IFAIScoringEngine",
    "DeterministicRuleScoringEngine",
]
