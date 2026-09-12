"""Unit tests for Open Payments ACL Adapter (OpenPaymentsACLClient)."""
from decimal import Decimal
from uuid import uuid4

import pytest

from src.integrations.open_payments.client import MockOpenPaymentsACLAdapter
from src.domain.shared.value_objects import Money, WalletAddress


@pytest.mark.asyncio
async def test_mock_open_payments_acl_full_flow() -> None:
    """Tests the complete Open Payments 4-step flow using the ACL client."""
    acl = MockOpenPaymentsACLAdapter()

    receiver = WalletAddress(url="https://wallet.example.com/bob")
    sender = WalletAddress(url="https://wallet.example.com/alice")
    amount = Money(amount=Decimal("50.00"), asset_code="USD", asset_scale=2)

    # Step 1 — Resolve wallet metadata
    wallet_meta = await acl.resolve_wallet(receiver)
    assert "assetCode" in wallet_meta
    assert wallet_meta["assetCode"] == "USD"
    assert "authServer" in wallet_meta

    # Step 2 — Simulate GNAP access token (in production: call authServer)
    access_token = f"gnap-token-{uuid4()}"
    assert access_token.startswith("gnap-token-")

    # Step 3 — Create Incoming Payment
    inc_payment = await acl.create_incoming_payment(
        wallet_address=receiver,
        amount=amount,
        access_token=access_token,
    )
    assert "id" in inc_payment
    assert inc_payment["walletAddress"] == receiver.url

    # Step 4 — Request Quote
    quote = await acl.get_quote(
        sender_wallet=sender,
        receiver_incoming_payment_url=inc_payment["id"],
        access_token=access_token,
    )
    assert "id" in quote
    assert "debitAmount" in quote

    # Step 5 — Create Outgoing Payment
    outgoing = await acl.create_outgoing_payment(
        sender_wallet=sender,
        quote_url=quote["id"],
        access_token=access_token,
    )
    assert "id" in outgoing
    assert outgoing.get("state") == "COMPLETED"


@pytest.mark.asyncio
async def test_wallet_resolution_fallback_on_unreachable_url() -> None:
    """Tests that wallet resolution gracefully falls back when URL is unreachable."""
    acl = MockOpenPaymentsACLAdapter()
    unreachable = WalletAddress(url="https://unreachable.wallet.nonexistent/user")
    result = await acl.resolve_wallet(unreachable)
    # Should return fallback metadata, not raise
    assert isinstance(result, dict)
    assert "assetCode" in result


@pytest.mark.asyncio
async def test_create_incoming_payment_includes_amount_in_response() -> None:
    """Tests that IncomingPayment fallback encodes the requested amount."""
    acl = MockOpenPaymentsACLAdapter()
    wallet = WalletAddress(url="https://wallet.example.com/carol")
    amount = Money(amount=Decimal("100.00"), asset_code="USD", asset_scale=2)
    result = await acl.create_incoming_payment(
        wallet_address=wallet,
        amount=amount,
        access_token="test-token",
    )
    incoming_amount = result.get("incomingAmount", {})
    assert incoming_amount.get("assetCode") == "USD"
    assert incoming_amount.get("assetScale") == 2
