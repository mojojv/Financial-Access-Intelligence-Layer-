"""Open Payments Fixtures and Mock Response Generators for Offline Unit & ACL Testing."""
from typing import Any


def mock_wallet_discovery_response(wallet_url: str = "https://ilp.wallet.com/alice") -> dict[str, Any]:
    """Generates mock Open Payments wallet address metadata JSON response."""
    return {
        "id": wallet_url,
        "assetCode": "USD",
        "assetScale": 2,
        "authServer": "https://auth.wallet.example.com",
        "resourceServer": "https://wallet.example.com",
    }


def mock_incoming_payment_response(
    wallet_url: str = "https://ilp.wallet.com/bob",
    incoming_id: str = "inc-pay-123",
    amount_str: str = "5000",
) -> dict[str, Any]:
    """Generates mock Open Payments incoming payment JSON response."""
    return {
        "id": f"{wallet_url}/incoming-payments/{incoming_id}",
        "walletAddress": wallet_url,
        "incomingAmount": {"value": amount_str, "assetCode": "USD", "assetScale": 2},
        "completed": False,
    }


def mock_quote_response(
    sender_wallet: str = "https://ilp.wallet.com/alice",
    receiver_incoming_url: str = "https://ilp.wallet.com/bob/incoming-payments/inc-pay-123",
) -> dict[str, Any]:
    """Generates mock Open Payments quote JSON response."""
    return {
        "id": f"{sender_wallet}/quotes/quote-789",
        "walletAddress": sender_wallet,
        "receiver": receiver_incoming_url,
        "debitAmount": {"value": "10000", "assetCode": "USD", "assetScale": 2},
        "estimatedFee": {"value": "50", "assetCode": "USD", "assetScale": 2},
    }


def mock_outgoing_payment_response(
    sender_wallet: str = "https://ilp.wallet.com/alice",
    quote_url: str = "https://ilp.wallet.com/alice/quotes/quote-789",
) -> dict[str, Any]:
    """Generates mock Open Payments outgoing payment JSON response."""
    return {
        "id": f"{sender_wallet}/outgoing-payments/out-456",
        "walletAddress": sender_wallet,
        "quoteId": quote_url,
        "debitAmount": {"value": "10000", "assetCode": "USD", "assetScale": 2},
        "state": "COMPLETED",
    }
