"""Domain Port Interfaces for Open Payments Anti-Corruption Layer (ACL)."""
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional
from src.integrations.open_payments.dto import (
    WalletMetadataDTO,
    GNAPGrantDTO,
    IncomingPaymentDTO,
    QuoteDTO,
    OutgoingPaymentDTO,
)


class IWalletDiscoveryService(ABC):
    @abstractmethod
    async def discover_wallet(self, wallet_url: str) -> WalletMetadataDTO:
        """Resolves Wallet Address URL to wallet metadata."""
        pass


class IGNAPAuthorizationService(ABC):
    @abstractmethod
    async def request_grant(self, auth_server_url: str, client_key_id: str) -> GNAPGrantDTO:
        """Requests GNAP Grant access token from Open Payments Auth Server."""
        pass


class IIncomingPaymentService(ABC):
    @abstractmethod
    async def create_incoming_payment(
        self, wallet_url: str, amount: Decimal, asset_code: str, token: str
    ) -> IncomingPaymentDTO:
        """Creates Incoming Payment on receiver Resource Server."""
        pass


class IQuoteService(ABC):
    @abstractmethod
    async def request_quote(
        self, sender_wallet_url: str, receiver_incoming_payment_url: str, token: str
    ) -> QuoteDTO:
        """Requests payment quote from sender Resource Server."""
        pass


class IOutgoingPaymentService(ABC):
    @abstractmethod
    async def create_outgoing_payment(
        self, sender_wallet_url: str, quote_id: str, token: str
    ) -> OutgoingPaymentDTO:
        """Executes Outgoing Payment using authorized quote."""
        pass
