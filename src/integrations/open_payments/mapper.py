"""Open Payments Data Mappers (ACL Pure Mapping Functions)."""
from decimal import Decimal
from typing import Any, Dict

from src.domain.payments.payment_intent import PaymentIntent, PaymentIntentStatus
from src.domain.shared.value_objects import Money, WalletAddress


class OpenPaymentsMapper:
    """Pure Data Mapper isolating Open Payments REST schemas from Domain Model."""

    @staticmethod
    def to_wallet_address(wallet_url: str) -> WalletAddress:
        """Maps Open Payments wallet URL string to domain WalletAddress Value Object."""
        return WalletAddress(url=wallet_url)

    @staticmethod
    def to_money(amount_str: str, asset_code: str, asset_scale: int = 2) -> Money:
        """Maps Open Payments asset amount to domain Money Value Object."""
        scale_factor = Decimal(10 ** asset_scale)
        amount_decimal = Decimal(amount_str) / scale_factor
        return Money(amount=amount_decimal, asset_code=asset_code, asset_scale=asset_scale)

    @staticmethod
    def map_outgoing_payment_response(
        response_json: Dict[str, Any],
        sender_wallet: WalletAddress,
        receiver_wallet: WalletAddress,
    ) -> PaymentIntent:
        """Maps Open Payments Outgoing Payment JSON response to domain PaymentIntent entity."""
        payment_id = response_json.get("id", "")
        debit_amount_obj = response_json.get("debitAmount", {})
        asset_code = debit_amount_obj.get("assetCode", "USD")
        asset_scale = debit_amount_obj.get("assetScale", 2)
        amount_val = debit_amount_obj.get("value", "0")

        money = OpenPaymentsMapper.to_money(amount_val, asset_code, asset_scale)

        raw_state = response_json.get("state", "COMPLETED")
        status = PaymentIntentStatus.COMPLETED if raw_state == "COMPLETED" else PaymentIntentStatus.SUBMITTED

        intent = PaymentIntent.create(sender_wallet=sender_wallet, receiver_wallet=receiver_wallet, amount=money)
        intent.status = status
        intent.outgoing_payment_url = payment_id
        return intent
