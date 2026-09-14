# ADR 0001: Strategy Pattern for Financial Access Index (FAI) Scoring and Threshold Barrier Diagnosis

- **Status**: Approved
- **Date**: 2026-09-13
- **Authors**: Staff Software Engineer & DDD Architect
- **Context**: Financial Access Intelligence Layer (FAIL)

---

## 📋 Context & Problem Statement

Measuring financial inclusion requires flexible evaluation algorithms that can evolve from initial deterministic rules to statistical models (PCA) and machine learning models (XGBoost/MCDA) without breaking API contracts, web routers, or domain invariants.

Additionally, raw scores must be translated into actionable financial barrier diagnoses with distinct severity classifications (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`).

---

## 🎯 Decision Drivers

1. **Extensibility**: Support interchanging weighting algorithms dynamically per request or cohort.
2. **Domain Isolation**: Keep scoring logic and barrier diagnosis decoupled from web frameworks (FastAPI) and external protocols (Open Payments).
3. **Determinism & Precision**: Enforce strict score bounds `[0.00, 100.00]` using Python `Decimal` quantization.

---

## 💡 Proposed Solution: Strategy Pattern & Threshold Evaluator

### 1. Strategy Pattern (`WeightingStrategy`)
Define an abstract interface `WeightingStrategy` in `src/domain/access_index/weighting.py`:

```python
class WeightingStrategy(ABC):
    @abstractmethod
    def compute_composite_score(
        self,
        dimensions: Dict[DimensionKey, FinancialDimension],
        weight_vector: WeightVector,
    ) -> ScoreValue:
        pass
```

Implementations:
- `DeterministicLinearWeightingStrategy`: Linear weighted combination of 7 dimension scores.
- `PCAStatisticalWeightingStrategy`: Variance-weighted aggregation based on Principal Component Analysis.

### 2. Threshold-Based Barrier Evaluator
Define `BarrierEvaluator` in `src/domain/barriers/evaluator.py` mapping dimension scores against threshold rules:

- Score == 0.00 on Access -> `CRITICAL` Severity (`BAR_ACC_05`).
- Score < Threshold -> `HIGH` / `MEDIUM` Severity.
- Score > Threshold -> Normal / Resolved State.

---

## ⚖️ Consequences

### Positive
- Web routes (`apps/api/routes.py`) rely solely on FastAPI Dependency Injection (`fastapi.Depends()`) and Application Use Cases.
- Clean separation between score computation and barrier diagnosis.
- Easy to add new machine learning strategies in `src/infrastructure/ml/scoring/`.

### Negative / Mitigation
- Requires maintaining explicit mapping between DTOs and domain value objects. Addressed via Pydantic v2 schemas and Application Use Cases.
