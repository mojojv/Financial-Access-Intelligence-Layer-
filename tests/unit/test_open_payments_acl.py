"""Unit tests for Open Payments ACL Adapter."""
import asyncio
from decimal import Decimal
from src.integrations.open_payments.client import MockOpenPaymentsACLAdapter


def test_mock_open_payments_acl_flow() -> None:
    async def _run() -> None:
        acl = MockOpenPaymentsACLAdapter()
        receiver_wallet = "https://wallet.example.com/bob"
        sender_wallet = "https://wallet.example.com/alice"

        # 1. Discover
        wallet_meta = await acl.discover_wallet(receiver_wallet)
        assert wallet_meta.asset_code == "USD"

        # 2. Grant
        grant = await acl.request_grant(wallet_meta.auth_server, client_key_id="key-1")
        assert grant.access_token.startswith("gnap_access_token_")

        # 3. Incoming Payment
        inc_payment = await acl.create_incoming_payment(
            wallet_url=receiver_wallet,
            amount=Decimal("50.00"),
            asset_code="USD",
            token=grant.access_token,
        )
        assert inc_payment.amount == Decimal("50.00")

        # 4. Quote
        quote = await acl.request_quote(
            sender_wallet_url=sender_wallet,
            receiver_incoming_payment_url=inc_payment.id,
            token=grant.access_token,
        )
        assert quote.debit_amount == Decimal("100.00")

        # 5. Outgoing Payment
        outgoing = await acl.create_outgoing_payment(
            sender_wallet_url=sender_wallet,
            quote_id=quote.id,
            token=grant.access_token,
        )
        assert outgoing.status == "COMPLETED"

    asyncio.run(_run())

