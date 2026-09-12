"""Integration and Unit Tests for Open Payments ACL Client and Data Mapper."""
import asyncio
from decimal import Decimal
from uuid import UUID

from src.domain.payments.payment_intent import PaymentIntentStatus
from src.domain.shared.value_objects import Money, WalletAddress
from src.integrations.open_payments.client import OpenPaymentsACLClient
from src.integrations.open_payments.mapper import OpenPaymentsMapper
from tests.fixtures.open_payments_mocks import (
    mock_outgoing_payment_response,
    mock_wallet_discovery_response,
)


def test_open_payments_mapper_pure_functions() -> None:
    # 1. Test Wallet Address Mapping
    wallet_vo = OpenPaymentsMapper.to_wallet_address("https://ilp.wallet.com/alice")
    assert isinstance(wallet_vo, WalletAddress)
    assert wallet_vo.url == "https://ilp.wallet.com/alice"

    # 2. Test Money Mapping (Value 10000 with Scale 2 -> 100.00 USD)
    money_vo = OpenPaymentsMapper.to_money(amount_str="10000", asset_code="USD", asset_scale=2)
    assert isinstance(money_vo, Money)
    assert money_vo.amount == Decimal("100.00")
    assert money_vo.asset_code == "USD"

    # 3. Test Outgoing Payment Response to Domain Entity Mapping
    raw_response = mock_outgoing_payment_response()
    sender = WalletAddress("https://ilp.wallet.com/alice")
    receiver = WalletAddress("https://ilp.wallet.com/bob")

    intent = OpenPaymentsMapper.map_outgoing_payment_response(
        response_json=raw_response,
        sender_wallet=sender,
        receiver_wallet=receiver,
    )

    assert isinstance(intent.intent_id, UUID)
    assert intent.status == PaymentIntentStatus.COMPLETED
    assert intent.amount.amount == Decimal("100.00")
    assert intent.outgoing_payment_url == "https://ilp.wallet.com/alice/outgoing-payments/out-456"


def test_open_payments_acl_client_async_flow() -> None:
    async def _run() -> None:
        client = OpenPaymentsACLClient(client_key_id="test-key-id")
        sender = WalletAddress("https://ilp.wallet.com/alice")
        receiver = WalletAddress("https://ilp.wallet.com/bob")
        money = Money(amount=Decimal("50.00"), asset_code="USD")

        # 1. Resolve Wallet
        meta = await client.resolve_wallet(receiver)
        assert meta["assetCode"] == "USD"

        # 2. Create Incoming Payment
        inc = await client.create_incoming_payment(receiver, money, access_token="gnap-token-123")
        assert "incomingAmount" in inc

        # 3. Get Quote
        quote = await client.get_quote(sender, inc["id"], access_token="gnap-token-123")
        assert "debitAmount" in quote

        # 4. Create Outgoing Payment
        outgoing = await client.create_outgoing_payment(sender, quote["id"], access_token="gnap-token-123")
        assert outgoing["state"] == "COMPLETED"

        await client.close()

    asyncio.run(_run())
