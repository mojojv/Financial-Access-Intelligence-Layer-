"""Unit tests for Financial Access Index scoring calculation."""
from decimal import Decimal
from uuid import uuid4

from src.domain.access_index.dimensions import DimensionType
from src.domain.access_index.scoring import (
    DeterministicRuleScoringEngine,
    FeatureVector,
)


def test_deterministic_scoring_engine_balanced_profile() -> None:
    engine = DeterministicRuleScoringEngine()
    profile_id = uuid4()
    features = FeatureVector(
        wallet_count=2,
        ilp_reachable=True,
        tx_success_rate=0.98,
        avg_connection_latency_ms=150.0,
        fee_to_volume_ratio=0.01,  # 1% fee -> score ~90
        settlement_fulfillment_rate=0.99,
        cross_asset_success_rate=0.95,
        tx_frequency_monthly=10,
        tx_volume_monthly_usd=200.0,
        reserve_liquidity_usd=100.0,
        fallback_route_available=True,
    )

    fai_score = engine.calculate_score(profile_id=profile_id, features=features)

    assert fai_score.profile_id == profile_id
    assert len(fai_score.dimension_scores) == 7
    assert fai_score.overall_score > Decimal("50.0")

    # Verify Access dimension score (50 for ILP + 50 for 2 wallets = 100)
    assert fai_score.dimension_scores[DimensionType.ACCESS].score == Decimal("100")


def test_deterministic_scoring_engine_high_fee_penalty() -> None:
    engine = DeterministicRuleScoringEngine()
    profile_id = uuid4()

    # Profile with high fee ratio (15% fee)
    features = FeatureVector(
        wallet_count=1,
        ilp_reachable=True,
        tx_success_rate=0.90,
        avg_connection_latency_ms=500.0,
        fee_to_volume_ratio=0.15,  # High fee penalty
        settlement_fulfillment_rate=0.95,
        cross_asset_success_rate=0.80,
        tx_frequency_monthly=5,
        tx_volume_monthly_usd=50.0,
        reserve_liquidity_usd=10.0,
        fallback_route_available=False,
    )

    fai_score = engine.calculate_score(profile_id=profile_id, features=features)

    # Affordability score should be 0 due to penalty
    assert fai_score.dimension_scores[DimensionType.AFFORDABILITY].score == Decimal("0")
