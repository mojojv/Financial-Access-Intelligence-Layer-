# Financial Access Intelligence Layer (FAIL)

[![CI Pipeline](https://github.com/fail-open/financial-access-intelligence/actions/workflows/ci.yml/badge.svg)](https://github.com/fail-open/financial-access-intelligence/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![Tests Passing](https://img.shields.io/badge/tests-49%2F49%20passed-brightgreen.svg)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-%3E80%25-success.svg)](tests/)
[![Latency SLO](https://img.shields.io/badge/latency-0.041ms%2Fprofile-blueviolet.svg)](tests/performance/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

The **Financial Access Intelligence Layer (FAIL)** is an open-source research and engineering platform designed to measure, diagnose, and optimize global financial inclusion using real-time telemetry from **Interledger Open Payments**.

---

## 🏛 Key System Capabilities

- **Multi-Dimensional FAI Engine**: Measures 7 core dimensions (*Access*, *Connectivity*, *Affordability*, *Reliability*, *Interoperability*, *Usage*, *Resilience*) on a normalized `[0.00, 100.00]` score scale using exact `Decimal` precision.
- **Strategy Pattern (`WeightingStrategy`)**: Pluggable weighting architecture supporting rule-based (`DeterministicLinearWeightingStrategy`), statistical (`PCAStatisticalWeightingStrategy`), and machine learning scoring models.
- **Structural Barrier Diagnosis (`BarrierEvaluator`)**: Threshold-based engine evaluating multidimensional profile scores to diagnose systemic obstacles across 4 severity tiers (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`).
- **Clean FastAPI Router Layer**: Zero business/protocol logic in routes. 100% Dependency Injection with `fastapi.Depends()` and strict Pydantic v2 DTOs.
- **Open Payments ACL Adapter**: Anti-Corruption Layer (ACL) for Interledger Open Payments with GNAP HTTP Signatures (Ed25519) and zero floating-point money handling.
- **DevOps & Production Infrastructure**: Multi-stage Dockerfile built on Python 3.12-slim and `uv`, non-root security container execution, Docker Compose (FastAPI, Worker, Postgres 16, Redis 7), and GitHub Actions CI.
- **Data Science & Benchmark Suite**: 1,000 profile synthetic telemetry generator, 2 econometric Jupyter notebooks, and a `pytest-benchmark` performance suite running at **0.041ms per profile calculation** (~24,359 ops/sec).

---

## 🛠 Repository Structure

```text
financial-access-intelligence/
├── .github/
│   └── workflows/ci.yml         # GitHub Actions CI Workflow (Ruff, Mypy, Pytest >80% Cov)
├── apps/
│   └── api/                     # FastAPI Web Application & Routes (Clean DI Router)
├── data/
│   └── synthetic/               # Synthetic Telemetry Generator & CSV Dataset (1,000 Profiles)
├── docs/                        # MkDocs Documentation (Methodology, Open Payments, ADRs)
├── notebooks/                   # Jupyter Notebooks (01 Validation & 02 Strategy Benchmark)
├── src/
│   ├── domain/                  # Pure DDD Domain (Entities, Value Objects, Strategy Interfaces)
│   ├── application/             # Application Use Cases & Orchestration
│   ├── infrastructure/          # Database, Redis Cache, ML Models, Observability
│   └── integrations/            # Open Payments ACL Client & GNAP Ed25519 Signatures
├── tests/                       # Unit, Integration, API, Open Payments & Performance Benchmarks
├── Dockerfile                   # Multi-Stage Production Dockerfile (Python 3.12 + uv + appuser)
├── docker-compose.yml           # Production Docker Stack (API, Worker, Postgres 16, Redis 7)
├── mkdocs.yml                   # MkDocs Material Site Configuration
└── pyproject.toml               # Project Metadata & Dependency Specifications
```

---

## 🚀 Quickstart Guide

### 1. Environment Setup
```bash
# Clone the repository
git clone https://github.com/mojojv/Financial-Access-Intelligence-Layer-.git
cd Financial-Access-Intelligence-Layer-

# Create virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev,ml]"
```

### 2. Execute Quality & Test Suite
```bash
# Run Ruff Linter
ruff check .

# Run Mypy Static Type Checking
mypy src

# Run Unit, Integration & API Tests with Coverage Report
python -m pytest --cov=src --cov-report=term-missing

# Run Performance Benchmark Suite
python -m pytest tests/performance/test_scoring_benchmark.py -s
```

### 3. Generate Synthetic Data & Run Econometric Notebooks
```bash
# Generate 1,000 synthetic profile telemetries
python data/synthetic/profile_generator.py

# Launch Jupyter Lab / Notebook
jupyter lab notebooks/
```

### 4. Containerized Local Deployment (Docker Compose)
```bash
# Build and launch all services (API, Worker, Postgres 16, Redis 7)
docker-compose up --build -d

# Check API health status
curl http://localhost:8000/health
```

### 5. Documentation Server (MkDocs)
```bash
# Serve documentation locally
mkdocs serve
```

---

## 📖 Architectural Documentation & ADRs

- [**Research Methodology**](docs/methodology/fai-index.md): Mathematical formulations, dimension scaling, and weighting strategies.
- [**Open Payments Integration**](docs/guides/open-payments-integration.md): Interledger protocol setup, GNAP HTTP signatures, and wallet resolution.
- [**Architecture Decision Records (ADRs)**](docs/adrs/0001-fai-scoring-engine-architecture.md): Technical decision records governing system design.

---

## 📄 License

This project is licensed under the Apache 2.0 License — see the [LICENSE](LICENSE) file for details.
