"""Unit tests for FAI Dimension Calculators, Weighting Strategies, and Barrier Evaluator."""
from decimal import Decimal
import pytest
from uuid import uuid4

from src.domain.access_index.dimension_calculators import (
    FAIDimensionPipeline,
    AccessDimensionCalculator,
    AffordabilityDimensionCalculator,
)
from src.domain.access_index.dimensions import (
    FinancialDimension,
    FinancialScore,
    WeightVector,
)
from src.domain.access_index.weighting import (
    DeterministicLinearWeightingStrategy,
    PCAStatisticalWeightingStrategy,
)
from src.domain.barriers.evaluator import BarrierEvaluator, BarrierThresholdConfig
from src.domain.shared.exceptions import InvalidValueObjectError
from src.domain.shared.value_objects import BarrierCode, DimensionKey, ScoreValue


def test_access_dimension_calculator_boundary_cases() -> None:
    calc = AccessDimensionCalculator()

    # Case 1: Minimum boundary (0 wallets, unreachable)
    dim_min = calc.calculate({"wallet_count": 0, "ilp_reachable": False})
    assert dim_min.score.value == Decimal("0.00")

    # Case 2: Maximum boundary (3 wallets, reachable)
    dim_max = calc.calculate({"wallet_count": 3, "ilp_reachable": True})
    assert dim_max.score.value == Decimal("100.00")


def test_affordability_calculator_high_fee_penalty() -> None:
    calc = AffordabilityDimensionCalculator()

    # Case 1: Zero fee -> 100 score
    dim_zero = calc.calculate({"fee_to_volume_ratio": 0.0})
    assert dim_zero.score.value == Decimal("100.00")

    # Case 2: High fee (15%) -> 0 score
    dim_high = calc.calculate({"fee_to_volume_ratio": 0.15})
    assert dim_high.score.value == Decimal("0.00")


def test_invalid_weight_vector_raises_error() -> None:
    # Invalid weight sum != 1.0
    invalid_weights = {dim: Decimal("0.10") for dim in DimensionKey}
    with pytest.raises(InvalidValueObjectError):
        WeightVector(weights=invalid_weights)


def test_fai_dimension_pipeline_handles_missing_keys() -> None:
    pipeline = FAIDimensionPipeline()
    # Empty feature dictionary should not raise exceptions, defaults to safe boundaries
    dims = pipeline.compute_all_dimensions({})
    assert len(dims) == 7
    for dim_key in DimensionKey:
        assert dim_key in dims
        assert Decimal("0.00") <= dims[dim_key].score.value <= Decimal("100.00")


def test_weighting_strategies_interchangeability() -> None:
    pipeline = FAIDimensionPipeline()
    features = {
        "wallet_count": 2,
        "ilp_reachable": True,
        "tx_success_rate": 0.95,
        "avg_connection_latency_ms": 200.0,
        "fee_to_volume_ratio": 0.01,
        "settlement_fulfillment_rate": 0.98,
        "cross_asset_success_rate": 0.90,
        "tx_frequency_monthly": 15,
        "tx_volume_monthly_usd": 300.0,
        "reserve_liquidity_usd": 100.0,
        "fallback_route_available": True,
    }

    dims = pipeline.compute_all_dimensions(features)
    weights = WeightVector.default_equal_weights()

    # 1. Deterministic Linear Strategy
    linear_strat = DeterministicLinearWeightingStrategy()
    score_linear = linear_strat.compute_composite_score(dims, weights)
    assert score_linear.value > Decimal("50.00")

    # 2. PCA Strategy
    pca_strat = PCAStatisticalWeightingStrategy()
    score_pca = pca_strat.compute_composite_score(dims, weights)
    assert score_pca.value > Decimal("50.00")


def test_barrier_evaluator_threshold_detection() -> None:
    evaluator = BarrierEvaluator(config=BarrierThresholdConfig(affordability_threshold=Decimal("50.00")))
    profile_id = uuid4()

    dims = {
        DimensionKey.ACCESS: FinancialDimension(DimensionKey.ACCESS, ScoreValue.from_float(100.0)),
        DimensionKey.CONNECTIVITY: FinancialDimension(DimensionKey.CONNECTIVITY, ScoreValue.from_float(90.0)),
        DimensionKey.AFFORDABILITY: FinancialDimension(DimensionKey.AFFORDABILITY, ScoreValue.from_float(20.0)), # Triggers barrier
        DimensionKey.RELIABILITY: FinancialDimension(DimensionKey.RELIABILITY, ScoreValue.from_float(95.0)),
        DimensionKey.INTEROPERABILITY: FinancialDimension(DimensionKey.INTEROPERABILITY, ScoreValue.from_float(85.0)),
        DimensionKey.USAGE: FinancialDimension(DimensionKey.USAGE, ScoreValue.from_float(70.0)),
        DimensionKey.RESILIENCE: FinancialDimension(DimensionKey.RESILIENCE, ScoreValue.from_float(60.0)),
    }

    fai_score = FinancialScore.create(
        profile_id=profile_id,
        overall_score=ScoreValue.from_float(74.28),
        dimensions=dims,
        scoring_version="v0.1",
        methodology="RULES",
    )

    barriers = evaluator.evaluate_barriers(fai_score)
    codes = [b.barrier_code for b in barriers]
    assert BarrierCode.HIGH_FEE_BURDEN in codes
