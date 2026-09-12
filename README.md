# Financial Access Intelligence Layer (FAIL)

An open-source platform that measures financial access via a multi-dimensional **Financial Access Index (FAI)**, identifies structural barriers, and executes targeted financial interventions through **Interledger Open Payments**.

## 🚀 Key Architectural Concepts

- **Clean / Hexagonal Architecture**: Domain logic is strictly isolated from infrastructure and protocols.
- **Open Payments Anti-Corruption Layer (ACL)**: Decoupled integration with Open Payments REST & GNAP specifications.
- **7 FAI Dimensions**: Access, Connectivity, Affordability, Reliability, Interoperability, Usage, Resilience (0-100 scores).
- **Strategy-Based Intervention Engine**: Maps diagnosed barriers to automated payment optimization routing.
- **Privacy by Design**: Pseudonymous UUID user model with zero PII storage.

## 🛠 Project Structure

```text
financial-access-intelligence/
├── apps/
│   ├── api/             # FastAPI Web Application Entrypoint
│   └── worker/          # Background Event & Scoring Worker
├── src/
│   ├── domain/          # Core Business Logic (Entities, Aggregates, Value Objects)
│   ├── application/     # Use Cases & Orchestration
│   ├── infrastructure/  # Database (PostgreSQL), Cache (Redis), ML, Security
│   └── integrations/    # Open Payments ACL Adapter
├── tests/               # Unit, Integration, API & Open Payments Mock Tests
└── docs/                # MkDocs Documentation
```

## 📖 Architecture & Documentation

Full architectural specification and ADRs are available in [`docs/architecture/`](docs/architecture/).
