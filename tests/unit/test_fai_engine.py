"""Comprehensive Unit Tests for FAI Dimension Calculators, Weighting Strategies, and Barrier Evaluator."""
from decimal import Decimal
from uuid import uuid4

import pytest

from src.domain.access_index.dimension_calculators import (
    AccessDimensionCalculator,
    AffordabilityDimensionCalculator,
    ConnectivityDimensionCalculator,
    FAIDimensionPipeline,
    ResilienceDimensionCalculator,
    UsageDimensionCalculator,
)
from src.domain.access_index.dimensions import (
    FinancialDimension,
    FinancialScore,
    WeightVector,
)
from src.domain.access_index.weighting import (
    DeterministicLinearWeightingStrategy,
    PCAStatisticalWeightingStrategy,
    WeightingStrategy,
)
from src.domain.barriers.evaluator import BarrierEvaluator, BarrierThresholdConfig
from src.domain.shared.exceptions import InvalidValueObjectError
from src.domain.shared.value_objects import (
    BarrierCode,
    DimensionKey,
    ScoreValue,
)


def test_access_dimension_calculator_boundaries() -> None:
    calc = AccessDimensionCalculator()

    # Min score: 0 wallets, unreachable
    dim_min = calc.calculate({"wallet_count": 0, "ilp_reachable": False})
    assert dim_min.score.value == Decimal("0.00")

    # Max score: 3 wallets, reachable
    dim_max = calc.calculate({"wallet_count": 3, "ilp_reachable": True})
    assert dim_max.score.value == Decimal("100.00")


def test_connectivity_dimension_calculator_latency_penalty() -> None:
    calc = ConnectivityDimensionCalculator()

    # Zero latency, 100% success rate
    dim_perfect = calc.calculate({"tx_success_rate": 1.0, "avg_connection_latency_ms": 100.0})
    assert dim_perfect.score.value == Decimal("100.00")

    # High latency penalty (> 500ms)
    dim_slow = calc.calculate({"tx_success_rate": 1.0, "avg_connection_latency_ms": 800.0})
    assert dim_slow.score.value < Decimal("100.00")


def test_affordability_calculator_fee_decay() -> None:
    calc = AffordabilityDimensionCalculator()

    # Zero fee -> 100 score
    dim_zero = calc.calculate({"fee_to_volume_ratio": 0.0})
    assert dim_zero.score.value == Decimal("100.00")

    # Extreme fee (15%) -> 0 score
    dim_high = calc.calculate({"fee_to_volume_ratio": 0.15})
    assert dim_high.score.value == Decimal("0.00")


def test_usage_and_resilience_negative_safety() -> None:
    calc_usage = UsageDimensionCalculator()
    calc_res = ResilienceDimensionCalculator()

    # Negative inputs should not raise ValueError (math.log1p protected)
    dim_usage = calc_usage.calculate({"tx_frequency_monthly": -5, "tx_volume_monthly_usd": -100.0})
    assert dim_usage.score.value >= Decimal("0.00")

    dim_res = calc_res.calculate({"fallback_route_available": False, "reserve_liquidity_usd": -500.0})
    assert dim_res.score.value == Decimal("0.00")


def test_pipeline_handles_missing_keys() -> None:
    pipeline = FAIDimensionPipeline()
    dims = pipeline.compute_all_dimensions({})
    assert len(dims) == 7
    for key in DimensionKey:
        assert key in dims
        assert Decimal("0.00") <= dims[key].score.value <= Decimal("100.00")


def test_invalid_weight_vector_raises_error() -> None:
    # Invalid sum != 1.0
    invalid_weights = {dim: Decimal("0.10") for dim in DimensionKey}
    with pytest.raises(InvalidValueObjectError):
        WeightVector(weights=invalid_weights)


def test_deterministic_linear_weighting_strategy() -> None:
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

    strategy = DeterministicLinearWeightingStrategy()
    composite_score = strategy.compute_composite_score(dims, weights)

    assert isinstance(composite_score, ScoreValue)
    assert Decimal("0.00") <= composite_score.value <= Decimal("100.00")
    assert composite_score.value > Decimal("50.00")


def test_strategy_interchangeability() -> None:
    pipeline = FAIDimensionPipeline()
    features = {
        "wallet_count": 1,
        "ilp_reachable": True,
        "tx_success_rate": 0.80,
        "avg_connection_latency_ms": 350.0,
        "fee_to_volume_ratio": 0.03,
        "settlement_fulfillment_rate": 0.85,
        "cross_asset_success_rate": 0.70,
        "tx_frequency_monthly": 5,
        "tx_volume_monthly_usd": 50.0,
        "reserve_liquidity_usd": 10.0,
        "fallback_route_available": False,
    }
    dims = pipeline.compute_all_dimensions(features)
    weights = WeightVector.default_equal_weights()

    linear_strat: WeightingStrategy = DeterministicLinearWeightingStrategy()
    pca_strat: WeightingStrategy = PCAStatisticalWeightingStrategy()

    score_linear = linear_strat.compute_composite_score(dims, weights)
    score_pca = pca_strat.compute_composite_score(dims, weights)

    assert Decimal("0.00") <= score_linear.value <= Decimal("100.00")
    assert Decimal("0.00") <= score_pca.value <= Decimal("100.00")


def test_barrier_evaluator_severities_and_thresholds() -> None:
    evaluator = BarrierEvaluator(
        config=BarrierThresholdConfig(
            affordability_threshold=Decimal("50.00"),
            access_threshold=Decimal("50.00"),
        )
    )
    profile_id = uuid4()

    dims = {
        DimensionKey.ACCESS: FinancialDimension(DimensionKey.ACCESS, ScoreValue.from_float(0.0)),  # CRITICAL severity
        DimensionKey.CONNECTIVITY: FinancialDimension(DimensionKey.CONNECTIVITY, ScoreValue.from_float(90.0)),
        DimensionKey.AFFORDABILITY: FinancialDimension(DimensionKey.AFFORDABILITY, ScoreValue.from_float(15.0)),  # HIGH severity
        DimensionKey.RELIABILITY: FinancialDimension(DimensionKey.RELIABILITY, ScoreValue.from_float(95.0)),
        DimensionKey.INTEROPERABILITY: FinancialDimension(DimensionKey.INTEROPERABILITY, ScoreValue.from_float(85.0)),
        DimensionKey.USAGE: FinancialDimension(DimensionKey.USAGE, ScoreValue.from_float(70.0)),
        DimensionKey.RESILIENCE: FinancialDimension(DimensionKey.RESILIENCE, ScoreValue.from_float(60.0)),
    }

    fai_score = FinancialScore.create(
        profile_id=profile_id,
        overall_score=ScoreValue.from_float(59.28),
        dimensions=dims,
        scoring_version="v0.1",
        methodology="RULES",
    )

    barriers = evaluator.evaluate_barriers(fai_score)
    codes = [b.barrier_code for b in barriers]

    assert BarrierCode.LIMITED_ACCESS in codes
    assert BarrierCode.HIGH_FEE_BURDEN in codes

    access_barrier = next(b for b in barriers if b.barrier_code == BarrierCode.LIMITED_ACCESS)
    assert access_barrier.severity.value == "critical"

    fee_barrier = next(b for b in barriers if b.barrier_code == BarrierCode.HIGH_FEE_BURDEN)
    assert fee_barrier.severity.value == "high"
