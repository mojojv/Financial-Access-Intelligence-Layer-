"""Open Payments Data Transfer Objects (DTOs) for Anti-Corruption Layer."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class WalletMetadataDTO:
    """Wallet Address discovery metadata DTO."""
    id: str
    asset_code: str
    asset_scale: int
    auth_server: str
    resource_server: str


@dataclass(frozen=True)
class GNAPGrantDTO:
    """GNAP Authorization Grant token DTO."""
    access_token: str
    manage_token: str
    expires_in_seconds: int


@dataclass(frozen=True)
class IncomingPaymentDTO:
    """Open Payments Incoming Payment resource DTO."""
    id: str
    wallet_address: str
    amount: Decimal
    asset_code: str
    asset_scale: int
    completed: bool


@dataclass(frozen=True)
class QuoteDTO:
    """Open Payments Quote resource DTO."""
    id: str
    wallet_address: str
    receiver_incoming_payment_url: str
    debit_amount: Decimal
    credit_amount: Decimal
    asset_code: str
    asset_scale: int
    estimated_fee: Decimal


@dataclass(frozen=True)
class OutgoingPaymentDTO:
    """Open Payments Outgoing Payment resource DTO."""
    id: str
    wallet_address: str
    quote_id: str
    debit_amount: Decimal
    asset_code: str
    status: str
