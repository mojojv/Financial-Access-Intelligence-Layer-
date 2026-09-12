"""Open Payments ACL Client Adapter Implementation."""
from decimal import Decimal
from uuid import uuid4
from src.integrations.open_payments.dto import (
    WalletMetadataDTO,
    GNAPGrantDTO,
    IncomingPaymentDTO,
    QuoteDTO,
    OutgoingPaymentDTO,
)
from src.integrations.open_payments.ports import (
    IWalletDiscoveryService,
    IGNAPAuthorizationService,
    IIncomingPaymentService,
    IQuoteService,
    IOutgoingPaymentService,
)


class MockOpenPaymentsACLAdapter(
    IWalletDiscoveryService,
    IGNAPAuthorizationService,
    IIncomingPaymentService,
    IQuoteService,
    IOutgoingPaymentService,
):
    """Mock Open Payments Adapter for isolated unit testing & offline development."""

    async def discover_wallet(self, wallet_url: str) -> WalletMetadataDTO:
        return WalletMetadataDTO(
            id=wallet_url,
            asset_code="USD",
            asset_scale=2,
            auth_server="https://auth.wallet.example.com",
            resource_server="https://wallet.example.com",
        )

    async def request_grant(self, auth_server_url: str, client_key_id: str) -> GNAPGrantDTO:
        return GNAPGrantDTO(
            access_token=f"gnap_access_token_{uuid4()}",
            manage_token=f"gnap_manage_token_{uuid4()}",
            expires_in_seconds=3600,
        )

    async def create_incoming_payment(
        self, wallet_url: str, amount: Decimal, asset_code: str, token: str
    ) -> IncomingPaymentDTO:
        return IncomingPaymentDTO(
            id=f"{wallet_url}/incoming-payments/{uuid4()}",
            wallet_address=wallet_url,
            amount=amount,
            asset_code=asset_code,
            asset_scale=2,
            completed=False,
        )

    async def request_quote(
        self, sender_wallet_url: str, receiver_incoming_payment_url: str, token: str
    ) -> QuoteDTO:
        return QuoteDTO(
            id=f"{sender_wallet_url}/quotes/{uuid4()}",
            wallet_address=sender_wallet_url,
            receiver_incoming_payment_url=receiver_incoming_payment_url,
            debit_amount=Decimal("100.00"),
            credit_amount=Decimal("99.50"),
            asset_code="USD",
            asset_scale=2,
            estimated_fee=Decimal("0.50"),
        )

    async def create_outgoing_payment(
        self, sender_wallet_url: str, quote_id: str, token: str
    ) -> OutgoingPaymentDTO:
        return OutgoingPaymentDTO(
            id=f"{sender_wallet_url}/outgoing-payments/{uuid4()}",
            wallet_address=sender_wallet_url,
            quote_id=quote_id,
            debit_amount=Decimal("100.00"),
            asset_code="USD",
            status="COMPLETED",
        )
