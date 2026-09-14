# Open Payments Integration Guide

This guide details how the **Financial Access Intelligence Layer (FAIL)** integrates with **Interledger Open Payments** via an Anti-Corruption Layer (ACL) adapter using **GNAP HTTP Signatures (Ed25519)** and exact **Decimal monetary precision**.

---

## 🏛 Anti-Corruption Layer (ACL) Architecture

The Open Payments API specification requires interacting with external auth servers and resource servers. FAIL isolates all external Open Payments protocol logic inside `src/integrations/open_payments/` to protect domain models from network schemas.

```
+------------------------------+
|     HTTP FastAPI Router      |
+------------------------------+
               |
               v
+------------------------------+
|   Application Use Cases      |
+------------------------------+
               |
               v
+------------------------------+
| OpenPaymentsACLClient (ACL)  |
+------------------------------+
               |
       (GNAP / Ed25519)
               v
+------------------------------+
|  Interledger Open Payments   |
+------------------------------+
```

---

## 🔒 GNAP HTTP Signatures

Interledger Open Payments mandates GNAP (Grant Negotiation and Authorization Protocol) signed with Ed25519 keys.

Every HTTP request sent by `OpenPaymentsACLClient` includes structured signature headers:

```http
POST /incoming-payments HTTP/1.1
Host: wallet.example.com
Authorization: GNAP gnap_token_xyz123
Signature-Input: sig1=("@method" "@target-uri");created=1617000000;keyid="key-001"
Signature: sig1=:Ed25519_Signature_Structured_Header_Hash_Placeholder==:
Content-Type: application/json
```

---

## 💰 Precision Financial Handling (`Decimal`)

To prevent binary floating-point rounding errors (e.g. `0.1 + 0.2 = 0.30000000000000004`), FAIL enforces Python `Decimal` across all domain value objects and application layers.

### Money Value Object Example
```python
from decimal import Decimal
from src.domain.shared.value_objects import Money

# Guaranteed exact precision
amount = Money(amount=Decimal("25.50"), asset_code="USD", asset_scale=2)
```

---

## 🔄 Outgoing Payment Execution Workflow

1. **Resolve Wallet Metadata**: Queries receiver and sender Wallet Address URLs.
2. **Create Incoming Payment**: Requests incoming payment grant on receiver's Resource Server.
3. **Get Quote**: Requests payment quote on sender's Resource Server to determine path costs and fees.
4. **Create Outgoing Payment**: Submits authorized quote to complete stream settlement over ILP.
