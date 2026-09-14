"""Payment Execution and Route Optimization Use Cases."""
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from src.domain.shared.value_objects import Money, WalletAddress
from src.infrastructure.ml.models.fee_optimizer import ILPLiquidityFeePredictor
from src.integrations.open_payments.client import OpenPaymentsACLClient


class ExecuteInterventionPaymentUseCase:
    """Application Use Case for executing financial intervention payments via Open Payments ACL."""

    def __init__(self, acl_client: OpenPaymentsACLClient | None = None) -> None:
        self.acl_client = acl_client or OpenPaymentsACLClient()

    async def execute(
        self,
        intervention_id: UUID,
        sender_wallet_str: str,
        receiver_wallet_str: str,
        amount: Decimal,
        asset_code: str = "USD",
        idempotency_key: str = "",
    ) -> dict[str, Any]:
        sender_wallet = WalletAddress(url=sender_wallet_str)
        receiver_wallet = WalletAddress(url=receiver_wallet_str)
        money = Money(amount=amount, asset_code=asset_code)

        # ACL Interaction: resolve wallet and initiate outgoing payment flow
        wallet_meta = await self.acl_client.resolve_wallet(sender_wallet)
        quote_res = await self.acl_client.get_quote(
            sender_wallet=sender_wallet,
            receiver_incoming_payment_url=f"{receiver_wallet.url}/incoming-payments/{uuid4()}",
            access_token=f"gnap_token_{idempotency_key or uuid4()}",
        )
        payment_res = await self.acl_client.create_outgoing_payment(
            sender_wallet=sender_wallet,
            quote_url=quote_res.get("id", f"{sender_wallet.url}/quotes/{uuid4()}"),
            access_token=f"gnap_token_{idempotency_key or uuid4()}",
        )

        estimated_fee = Decimal("0.50")

        return {
            "status": "COMPLETED" if payment_res.get("state") == "COMPLETED" else "SUBMITTED",
            "intervention_id": intervention_id,
            "open_payments_outgoing_id": payment_res.get(
                "id", f"{sender_wallet.url}/outgoing-payments/{uuid4()}"
            ),
            "debit_amount": money.amount,
            "asset_code": money.asset_code,
            "estimated_fee": estimated_fee,
        }


class OptimizeRouteUseCase:
    """Application Use Case for predicting optimal transaction routes and liquidity fees."""

    def __init__(self, predictor: ILPLiquidityFeePredictor | None = None) -> None:
        self.predictor = predictor or ILPLiquidityFeePredictor()

    def execute(
        self,
        source_asset: str,
        destination_asset: str,
        amount_usd: Decimal,
    ) -> dict[str, Any]:
        result = self.predictor.predict_optimal_route(
            source_asset=source_asset,
            destination_asset=destination_asset,
            amount_usd=float(amount_usd),
        )
        return {
            "recommended_route_id": result.recommended_route_id,
            "source_asset": result.source_asset,
            "destination_asset": result.destination_asset,
            "predicted_fee_pct": Decimal(str(round(result.predicted_fee_pct, 4))),
            "predicted_success_probability": Decimal(str(round(result.predicted_success_probability, 4))),
            "estimated_settlement_ms": Decimal(str(result.estimated_settlement_ms)),
            "liquidity_provider": result.liquidity_provider,
            "recommended_action": result.recommended_action,
        }
