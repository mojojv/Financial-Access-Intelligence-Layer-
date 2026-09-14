"""API handler logic tests running against pure Python ASGI app handlers."""
import asyncio
from uuid import UUID

from apps.api.routes import (
    ExecuteInterventionRequestSchema,
    FeatureIngestionSchema,
    calculate_fai_score,
    execute_intervention_payment,
    health_check,
)


def test_health_check_handler() -> None:
    result = asyncio.run(health_check())
    assert result["status"] == "healthy"
    assert result["service"] == "financial-access-intelligence"


def test_calculate_fai_score_handler() -> None:
    schema = FeatureIngestionSchema(
        profile_id=UUID("3fa85f64-5717-4562-b3fc-2c963f66afa6"),
        wallet_count=2,
        ilp_reachable=True,
        tx_success_rate=0.95,
        avg_connection_latency_ms=250.0,
        fee_to_volume_ratio=0.01,
        settlement_fulfillment_rate=0.98,
        cross_asset_success_rate=0.90,
        tx_frequency_monthly=12,
        tx_volume_monthly_usd=250.0,
        reserve_liquidity_usd=50.0,
        fallback_route_available=True,
    )
    data = asyncio.run(calculate_fai_score(schema))
    assert "overall_score" in data
    assert "dimension_scores" in data
    assert len(data["dimension_scores"]) == 7


def test_execute_payment_handler() -> None:
    schema = ExecuteInterventionRequestSchema(
        intervention_id=UUID("3fa85f64-5717-4562-b3fc-2c963f66afa6"),
        sender_wallet="https://ilp.wallet.com/alice",
        receiver_wallet="https://ilp.wallet.com/bob",
        amount=25.0,
        asset_code="USD",
    )
    data = asyncio.run(execute_intervention_payment(schema))
    assert data["status"] == "SUCCESS"
    assert "open_payments_outgoing_id" in data
