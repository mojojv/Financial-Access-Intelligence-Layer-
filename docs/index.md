# Financial Access Intelligence Layer (FAIL)

Welcome to the official documentation for the **Financial Access Intelligence Layer (FAIL)**, an open-source research and engineering platform designed to measure, diagnose, and optimize global financial inclusion using real-time telemetry from **Interledger Open Payments**.

---

## 🎯 Core Vision

Traditional financial inclusion metrics rely on static annual surveys and macro-economic proxies. FAIL introduces an empirical, multi-dimensional **Financial Access Index (FAI)** that evaluates individual financial profiles across 7 core dimensions in real time:

1. **Access**: Account reachability & Interledger Wallet Address availability.
2. **Connectivity**: Transaction execution success rate & latency overhead.
3. **Affordability**: Fee-to-volume ratio decay and cost efficiency.
4. **Reliability**: ILP stream settlement fulfillment consistency.
5. **Interoperability**: Multi-asset cross-currency conversion success.
6. **Usage**: Monthly transaction frequency and monetary throughput.
7. **Resilience**: Reserve liquidity buffers and fallback routing capability.

---

## 🚀 Key Architectural Pillars

- **Domain-Driven Design (DDD)**: Immutable Value Objects, aggregates, and strict boundary separation between domain, application, and infrastructure layers.
- **Strategy Pattern (`WeightingStrategy`)**: Pluggable weighting algorithms supporting deterministic rules, statistical PCA variance weighting, and ML predictions.
- **Anti-Corruption Layer (ACL)**: Isolated Open Payments client maintaining financial precision with Python `Decimal`.
- **Production-Ready DevOps**: Multi-stage Docker build targeting Python 3.12, non-root security container execution, and GitHub Actions CI.

---

## 📚 Documentation Sitemap

- [**Research Methodology**](methodology/fai-index.md): Mathematical formulations, dimension scaling, and weighting strategies.
- [**Open Payments Integration**](guides/open-payments-integration.md): Interledger protocol setup, GNAP HTTP signatures, and wallet resolution.
- [**Architecture Decisions (ADRs)**](adrs/0001-fai-scoring-engine-architecture.md): Technical decision records governing system design.
