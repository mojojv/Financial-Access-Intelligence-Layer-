# Financial Access Index (FAI) Methodology

The **Financial Access Index (FAI)** is a composite metric normalized to a range of **[0.00, 100.00]** that quantifies the real-time financial health, capability, and systemic access of a financial profile within Interledger Open Payments networks.

---

## 📐 Mathematical Formulation

The composite FAI score \( S_{\text{FAI}} \) is computed as a weighted combination of 7 dimension scores \( S_d \):

\[
S_{\text{FAI}} = \text{quantize}_{0.01} \left( \min \left( 100.00, \max \left( 0.00, \sum_{d \in D} w_d \cdot S_d \right) \right) \right)
\]

Where:
- \( D = \{ \text{Access}, \text{Connectivity}, \text{Affordability}, \text{Reliability}, \text{Interoperability}, \text{Usage}, \text{Resilience} \} \)
- \( w_d \ge 0 \) represents the weight assigned to dimension \( d \), subject to the normalization constraint \( \sum_{d \in D} w_d = 1.0 \).

---

## 📊 Dimension Calculators

### 1. Access Dimension (\( S_{\text{Access}} \))
Measures account reachability and protocol connectivity.

\[
S_{\text{Access}} = \min \left( 100, (50 \cdot \mathbb{I}_{\text{ILP\_reachable}}) + \min(N_{\text{wallets}} \cdot 25, 50) \right)
\]

### 2. Connectivity Dimension (\( S_{\text{Connectivity}} \))
Measures execution success rates and network latency overhead.

\[
S_{\text{Connectivity}} = \max \left( 0, \min \left( 100, 100 \cdot R_{\text{success}} - \max \left( 0, \min \left( 30, \frac{L_{\text{ms}} - 200}{20} \right) \right) \right) \right)
\]

### 3. Affordability Dimension (\( S_{\text{Affordability}} \))
Applies an inverse linear decay to fee-to-volume ratios.

\[
S_{\text{Affordability}} = \max \left( 0, \min \left( 100, 100 - (\rho_{\text{fee}} \cdot 1000) \right) \right)
\]

Where \( \rho_{\text{fee}} = \frac{\text{Fee}}{\text{Volume}} \). A fee ratio of 0% yields a score of 100; a fee ratio \(\ge 10\%\) yields a score of 0.

### 4. Reliability Dimension (\( S_{\text{Reliability}} \))
Measures settlement fulfillment consistency across ILP payment streams.

\[
S_{\text{Reliability}} = \max(0, \min(100, 100 \cdot R_{\text{fulfillment}}))
\]

### 5. Interoperability Dimension (\( S_{\text{Interoperability}} \))
Measures multi-asset cross-currency conversion success over Interledger.

\[
S_{\text{Interoperability}} = \max(0, \min(100, 100 \cdot R_{\text{cross\_asset}}))
\]

### 6. Usage Dimension (\( S_{\text{Usage}} \))
Combines transaction frequency and logarithmic monetary throughput.

\[
S_{\text{Usage}} = \min \left( 100, \min(50, 3 \cdot F_{\text{monthly}}) + \min(50, 7.5 \cdot \ln(1 + \max(0, V_{\text{monthly}}))) \right)
\]

### 7. Resilience Dimension (\( S_{\text{Resilience}} \))
Evaluates fallback route availability and reserve liquidity buffers.

\[
S_{\text{Resilience}} = \min \left( 100, (40 \cdot \mathbb{I}_{\text{fallback}}) + \min(60, 9 \cdot \ln(1 + \max(0, R_{\text{reserve}}))) \right)
\]

---

## 🎯 Pluggable Weighting Strategies (Pattern Strategy)

FAIL implements the **Strategy Pattern** via the abstract interface `WeightingStrategy`:

- **`DeterministicLinearWeightingStrategy`**: Uses equal baseline weights (\( w_d = \frac{1}{7} \approx 0.1428 \)) or policy-configured vectors.
- **`PCAStatisticalWeightingStrategy`**: Variance-weighted aggregation based on Principal Component Analysis (PCA) over historical cohort datasets.
- **`XGBoostMLScoringEngine`**: Machine learning non-linear scoring strategy.

---

## 🛡 Barrier Evaluation Engine

The `BarrierEvaluator` continuously monitors dimension scores against configured thresholds to diagnose structural financial access barriers:

| Dimension | Barrier Code | Trigger Condition | Severity Classification |
|---|---|---|---|
| **Access** | `BAR_ACC_05` | Score < 50.00 | `CRITICAL` (Score == 0) / `HIGH` |
| **Affordability** | `BAR_AFF_01` | Score < 40.00 | `HIGH` (Score < 20) / `MEDIUM` |
| **Connectivity** | `BAR_CON_04` | Score < 50.00 | `HIGH` (Score < 30) / `MEDIUM` |
| **Interoperability** | `BAR_INT_02` | Score < 45.00 | `HIGH` (Score < 25) / `MEDIUM` |
| **Resilience** | `BAR_RES_03` | Score < 35.00 | `MEDIUM` |
| **Usage** | `BAR_USG_06` | Score < 30.00 | `MEDIUM` / `LOW` |
| **Reliability** | `BAR_REL_07` | Score < 50.00 | `HIGH` (Score < 25) / `MEDIUM` |
