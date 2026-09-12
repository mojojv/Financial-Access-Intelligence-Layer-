"""Abstract Open Payments Adapter Port Interface for Application Layer."""
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any, Dict, Optional

from src.domain.shared.value_objects import Money, WalletAddress


class OpenPaymentsAdapterInterface(ABC):
    """Anti-Corruption Layer Interface defining generic Open Payments operations."""

    @abstractmethod
    async def resolve_wallet(self, wallet_url: WalletAddress) -> Dict[str, Any]:
        """Resolves Wallet Address URL to metadata (authServer, assetCode, assetScale)."""
        pass

    @abstractmethod
    async def create_incoming_payment(
        self,
        wallet_address: WalletAddress,
        amount: Money,
        access_token: str,
    ) -> Dict[str, Any]:
        """Creates an Incoming Payment resource on receiver's Resource Server."""
        pass

    @abstractmethod
    async def get_quote(
        self,
        sender_wallet: WalletAddress,
        receiver_incoming_payment_url: str,
        access_token: str,
    ) -> Dict[str, Any]:
        """Requests a payment Quote on sender's Resource Server."""
        pass

    @abstractmethod
    async def create_outgoing_payment(
        self,
        sender_wallet: WalletAddress,
        quote_url: str,
        access_token: str,
    ) -> Dict[str, Any]:
        """Executes Outgoing Payment using quote on sender's Resource Server."""
        pass
