"""Unit tests for Barrier Detection logic."""
from uuid import uuid4

from src.domain.access_index.scoring import (
    DeterministicRuleScoringEngine,
    FeatureVector,
)
from src.domain.barriers.barriers import BarrierCode, BarrierDetectionService


def test_barrier_detection_high_fee_burden() -> None:
    engine = DeterministicRuleScoringEngine()
    detector = BarrierDetectionService()
    profile_id = uuid4()

    # Features causing low affordability
    features = FeatureVector(
        wallet_count=2,
        ilp_reachable=True,
        tx_success_rate=0.99,
        avg_connection_latency_ms=100.0,
        fee_to_volume_ratio=0.10,  # 10% fee ratio -> score 0
        settlement_fulfillment_rate=0.99,
        cross_asset_success_rate=0.99,
        tx_frequency_monthly=20,
        tx_volume_monthly_usd=500.0,
        reserve_liquidity_usd=200.0,
        fallback_route_available=True,
    )

    fai_score = engine.calculate_score(profile_id=profile_id, features=features)
    barriers = detector.detect_barriers(fai_score)

    barrier_codes = [b.barrier_code for b in barriers]
    assert BarrierCode.HIGH_FEE_BURDEN in barrier_codes
