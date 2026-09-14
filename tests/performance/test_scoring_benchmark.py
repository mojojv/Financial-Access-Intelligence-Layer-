"""Performance and Latency Benchmark Tests for FAI Scoring Engine."""
import time
from uuid import uuid4
import pytest

from src.domain.access_index.dimension_calculators import FAIDimensionPipeline
from src.domain.access_index.weighting import DeterministicLinearWeightingStrategy
from src.domain.access_index.dimensions import WeightVector
from src.domain.shared.value_objects import ScoreValue


def test_fai_scoring_engine_latency_under_5ms() -> None:
    """Benchmark test verifying FAI score calculation latency per profile is under 5ms (0.005s)."""
    pipeline = FAIDimensionPipeline()
    weighting_strategy = DeterministicLinearWeightingStrategy()
    weights = WeightVector.default_equal_weights()

    sample_features = {
        "wallet_count": 2,
        "ilp_reachable": True,
        "tx_success_rate": 0.95,
        "avg_connection_latency_ms": 250.0,
        "fee_to_volume_ratio": 0.01,
        "settlement_fulfillment_rate": 0.98,
        "cross_asset_success_rate": 0.90,
        "tx_frequency_monthly": 12,
        "tx_volume_monthly_usd": 250.0,
        "reserve_liquidity_usd": 50.0,
        "fallback_route_available": True,
    }

    iterations = 1000
    start_time = time.perf_counter()

    for _ in range(iterations):
        dims = pipeline.compute_all_dimensions(sample_features)
        score = weighting_strategy.compute_composite_score(dims, weights)
        assert isinstance(score, ScoreValue)

    total_time_sec = time.perf_counter() - start_time
    avg_latency_ms = (total_time_sec / iterations) * 1000.0

    print(f"\n[BENCHMARK] Executed {iterations} FAI scoring runs in {total_time_sec:.4f}s.")
    print(f"[BENCHMARK] Average latency per profile score calculation: {avg_latency_ms:.4f} ms.")

    # Target SLO assertion: Latency per calculation must be < 5.0 ms
    assert avg_latency_ms < 5.0, f"FAI scoring latency too high: {avg_latency_ms:.4f} ms > 5.0 ms"


@pytest.mark.benchmark
def test_fai_scoring_benchmark_fixture(benchmark: pytest.FixtureRequest) -> None:
    """pytest-benchmark fixture test for detailed statistical latency tracking if pytest-benchmark is active."""
    pipeline = FAIDimensionPipeline()
    weighting_strategy = DeterministicLinearWeightingStrategy()
    weights = WeightVector.default_equal_weights()
    sample_features = {
        "wallet_count": 1,
        "ilp_reachable": True,
        "tx_success_rate": 0.90,
        "avg_connection_latency_ms": 200.0,
        "fee_to_volume_ratio": 0.02,
        "settlement_fulfillment_rate": 0.95,
        "cross_asset_success_rate": 0.85,
        "tx_frequency_monthly": 10,
        "tx_volume_monthly_usd": 150.0,
        "reserve_liquidity_usd": 30.0,
        "fallback_route_available": True,
    }

    def run_calculation():
        dims = pipeline.compute_all_dimensions(sample_features)
        return weighting_strategy.compute_composite_score(dims, weights)

    # Optional runner compatibility
    if hasattr(benchmark, "__call__"):
        result = benchmark(run_calculation)
        assert result is not None
    else:
        result = run_calculation()
        assert result is not None
