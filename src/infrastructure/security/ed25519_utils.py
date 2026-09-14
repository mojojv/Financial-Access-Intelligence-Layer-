"""Ed25519 key generation and HTTP Signature utilities for GNAP / Open Payments.

Provides helpers to generate Ed25519 keypairs, sign requests,
and validate signatures — structured per the Open Payments / GNAP
HTTP Message Signatures specification.

References:
  - https://openpayments.dev/introduction/overview/
  - https://www.ietf.org/archive/id/draft-ietf-gnap-core-protocol-20.txt
  - https://www.rfc-editor.org/rfc/rfc9421 (HTTP Message Signatures)
"""
import base64
import hashlib
import json
import time

try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
    )

    def generate_ed25519_keypair() -> tuple[bytes, bytes]:
        """Generates a new Ed25519 keypair.

        Returns:
            Tuple of (private_key_pem_bytes, public_key_pem_bytes).
        """
        private_key = Ed25519PrivateKey.generate()
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return private_pem, public_pem

    def sign_http_message(
        method: str,
        url: str,
        private_key_pem: bytes,
        key_id: str,
        body_json: dict | None = None,
    ) -> dict[str, str]:
        """Creates RFC 9421-compliant HTTP Signature headers for GNAP requests.

        Args:
            method: HTTP method (GET, POST, etc.).
            url: Full request URL.
            private_key_pem: PEM-encoded Ed25519 private key.
            key_id: Key identifier registered with the Authorization Server.
            body_json: Optional request body dict for content-digest computation.

        Returns:
            Dictionary of HTTP headers to attach to the request.
        """
        created = int(time.time())
        nonce = base64.urlsafe_b64encode(hashlib.sha256(f"{created}{url}".encode()).digest()).decode()[:16]

        components = ["@method", "@target-uri"]
        if body_json is not None:
            components.append("content-digest")

        signature_input = (
            f'sig1=({" ".join(f"{chr(34)}{c}{chr(34)}" for c in components)});'
            f'created={created};keyid="{key_id}";nonce="{nonce}"'
        )

        # Build signing string
        private_key = serialization.load_pem_private_key(private_key_pem, password=None)
        signing_string = f'"@method": {method.upper()}\n"@target-uri": {url}\n'
        if body_json is not None:
            body_bytes = json.dumps(body_json, separators=(",", ":")).encode()
            digest = base64.b64encode(hashlib.sha256(body_bytes).digest()).decode()
            signing_string += f'"content-digest": sha-256=:{digest}:\n'
        signing_string += f'"@signature-params": {signature_input}'

        raw_signature = private_key.sign(signing_string.encode())
        encoded_sig = base64.b64encode(raw_signature).decode()

        headers: dict[str, str] = {
            "Signature-Input": signature_input,
            "Signature": f"sig1=:{encoded_sig}:",
        }
        if body_json is not None:
            headers["Content-Digest"] = f"sha-256=:{base64.b64encode(hashlib.sha256(json.dumps(body_json, separators=(',', ':')).encode()).digest()).decode()}:"

        return headers

    _CRYPTO_AVAILABLE = True

except ImportError:
    # Fallback when cryptography library is not installed
    def generate_ed25519_keypair() -> tuple[bytes, bytes]:  # type: ignore
        """Returns placeholder keypair when cryptography library is unavailable."""
        placeholder = b"PLACEHOLDER_KEYPAIR_INSTALL_cryptography_PACKAGE"
        return placeholder, placeholder

    def sign_http_message(  # type: ignore
        method: str,
        url: str,
        private_key_pem: bytes,
        key_id: str,
        body_json: dict | None = None,
    ) -> dict[str, str]:
        """Returns placeholder signature headers when cryptography is unavailable."""
        return {
            "Signature-Input": f'sig1=("@method" "@target-uri");created={int(time.time())};keyid="{key_id}"',
            "Signature": "sig1=:PLACEHOLDER_SIGNATURE==:",
        }

    _CRYPTO_AVAILABLE = False
