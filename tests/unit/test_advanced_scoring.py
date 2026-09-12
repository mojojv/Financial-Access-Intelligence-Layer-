"""Unit tests for advanced scoring engines (MCDA & ML XGBoost)."""
from decimal import Decimal
from uuid import uuid4
from src.domain.access_index.dimensions import DimensionType
from src.domain.access_index.scoring import FeatureVector
from src.infrastructure.ml.scoring.mcda import MCDAScoringEngine
from src.infrastructure.ml.scoring.xgboost_engine import XGBoostMLScoringEngine


def test_mcda_scoring_engine() -> None:
    engine = MCDAScoringEngine()
    profile_id = uuid4()
    features = FeatureVector(
        wallet_count=2,
        ilp_reachable=True,
        tx_success_rate=0.98,
        avg_connection_latency_ms=120.0,
        fee_to_volume_ratio=0.01,
        settlement_fulfillment_rate=0.99,
        cross_asset_success_rate=0.95,
        tx_frequency_monthly=15,
        tx_volume_monthly_usd=300.0,
        reserve_liquidity_usd=100.0,
        fallback_route_available=True,
    )
    score = engine.calculate_score(profile_id, features)
    assert score.methodology == "NON_LINEAR_MCDA_CHOQUET"
    assert len(score.dimension_scores) == 7
    assert score.overall_score > Decimal("50.0")


def test_xgboost_ml_scoring_engine() -> None:
    engine = XGBoostMLScoringEngine()
    profile_id = uuid4()
    features = FeatureVector(
        wallet_count=3,
        ilp_reachable=True,
        tx_success_rate=0.99,
        avg_connection_latency_ms=100.0,
        fee_to_volume_ratio=0.005,
        settlement_fulfillment_rate=0.99,
        cross_asset_success_rate=0.98,
        tx_frequency_monthly=25,
        tx_volume_monthly_usd=500.0,
        reserve_liquidity_usd=250.0,
        fallback_route_available=True,
    )
    score = engine.calculate_score(profile_id, features)
    assert score.methodology == "GRADIENT_BOOSTING_ENSEMBLE"
    assert score.overall_score > Decimal("70.0")
