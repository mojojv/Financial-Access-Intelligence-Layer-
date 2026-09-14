"""Script to generate production Jupyter Notebooks for FAI validation and benchmark analysis."""
import os
import nbformat as nbf


def build_notebook_01() -> nbf.NotebookNode:
    nb = nbf.v4.new_notebook()

    nb.cells = [
        nbf.v4.new_markdown_cell("""# 📊 FAI Dimension & Methodology Validation

This notebook performs methodological validation on the **Financial Access Index (FAI)** calculation pipeline across 1,000 synthetic financial profiles.

### Key Objectives:
1. **Dimension Score Calculation**: Run `FAIDimensionPipeline` across 1,000 synthetic profiles.
2. **Distribution & Radar Analysis**: Visualize score distributions and radar charts across 4 socio-economic archetypes.
3. **Correlation Heatmaps**: Evaluate Pearson and Spearman rank correlations among the 7 FAI dimensions.
4. **Sensitivity Analysis**: Demonstrate mathematical continuity without abrupt score jumps in `[0.00, 100.00]`.
"""),
        nbf.v4.new_code_cell("""import sys
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(".."))

from src.domain.access_index.dimension_calculators import FAIDimensionPipeline
from src.domain.access_index.weighting import DeterministicLinearWeightingStrategy
from src.domain.access_index.dimensions import WeightVector
from src.domain.shared.value_objects import DimensionKey

sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams['font.size'] = 11
"""),
        nbf.v4.new_markdown_cell("""## 1. Load Synthetic Profiles Dataset"""),
        nbf.v4.new_code_cell("""dataset_path = os.path.join("..", "data", "synthetic", "profiles_dataset.csv")
if not os.path.exists(dataset_path):
    from data.synthetic.profile_generator import generate_synthetic_profiles
    df_raw = generate_synthetic_profiles(1000)
else:
    df_raw = pd.read_csv(dataset_path)

print(f"Loaded {len(df_raw)} financial profiles.")
df_raw.head()
"""),
        nbf.v4.new_markdown_cell("""## 2. Compute FAI Dimension & Composite Scores"""),
        nbf.v4.new_code_cell("""pipeline = FAIDimensionPipeline()
weighting_strategy = DeterministicLinearWeightingStrategy()
weights = WeightVector.default_equal_weights()

dim_scores_list = []
composite_scores = []

for _, row in df_raw.iterrows():
    feature_dict = row.to_dict()
    dims = pipeline.compute_all_dimensions(feature_dict)
    comp_score = weighting_strategy.compute_composite_score(dims, weights)
    
    score_entry = {k.value: float(v.score.value) for kk, (k, v) in enumerate(dims.items())}
    score_entry["overall_fai_score"] = float(comp_score.value)
    score_entry["archetype"] = row["archetype"]
    dim_scores_list.append(score_entry)

df_scores = pd.DataFrame(dim_scores_list)
print("Calculated score breakdown summary:")
df_scores.groupby("archetype")["overall_fai_score"].describe()
"""),
        nbf.v4.new_markdown_cell("""## 3. Score Distributions Across 7 Dimensions"""),
        nbf.v4.new_code_cell("""fig, axes = plt.subplots(3, 3, figsize=(15, 12))
axes = axes.flatten()

dim_columns = [k.value for k in DimensionKey] + ["overall_fai_score"]

for i, col in enumerate(dim_columns):
    sns.histplot(df_scores[col], kde=True, ax=axes[i], color="indigo", bins=20)
    axes[i].set_title(f"Distribution: {col.replace('_', ' ').title()}", fontsize=12, fontweight="bold")
    axes[i].set_xlim(0, 100)

plt.tight_layout()
plt.show()
"""),
        nbf.v4.new_markdown_cell("""## 4. Radar / Spider Chart by Archetype"""),
        nbf.v4.new_code_cell("""archetype_means = df_scores.groupby("archetype")[[k.value for k in DimensionKey]].mean()

categories = [k.value.capitalize() for k in DimensionKey]
N = len(categories)

angles = [n / float(N) * 2 * np.pi for n in range(N)]
angles += angles[:1]

fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
plt.xticks(angles[:-1], categories, color='grey', size=11)

colors = {"ARCHETYPE_A_HIGH_ACCESS": "#2ecc71", "ARCHETYPE_B_FEE_BURDENED": "#e67e22",
          "ARCHETYPE_C_LOW_RESILIENCE": "#e74c3c", "ARCHETYPE_D_DISCONNECTED": "#95a5a6"}

for arch in archetype_means.index:
    values = archetype_means.loc[arch].values.flatten().tolist()
    values += values[:1]
    ax.plot(angles, values, linewidth=2, linestyle='solid', label=arch, color=colors.get(arch, "blue"))
    ax.fill(angles, values, color=colors.get(arch, "blue"), alpha=0.1)

plt.title("FAI 7 Dimensions Profile by Socio-Economic Archetype", size=14, fontweight="bold", y=1.08)
plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
plt.show()
"""),
        nbf.v4.new_markdown_cell("""## 5. Pearson & Spearman Correlation Matrices"""),
        nbf.v4.new_code_cell("""fig, axes = plt.subplots(1, 2, figsize=(16, 6))

pearson_corr = df_scores[[k.value for k in DimensionKey]].corr(method="pearson")
spearman_corr = df_scores[[k.value for k in DimensionKey]].corr(method="spearman")

sns.heatmap(pearson_corr, annot=True, fmt=".2f", cmap="Blues", ax=axes[0], vmin=-1, vmax=1)
axes[0].set_title("Pearson Linear Correlation Matrix", fontweight="bold")

sns.heatmap(spearman_corr, annot=True, fmt=".2f", cmap="Purples", ax=axes[1], vmin=-1, vmax=1)
axes[1].set_title("Spearman Rank Correlation Matrix", fontweight="bold")

plt.tight_layout()
plt.show()
"""),
        nbf.v4.new_markdown_cell("""## 6. Sensitivity Analysis (Mathematical Continuity Test)"""),
        nbf.v4.new_code_cell("""base_features = {
    "wallet_count": 2, "ilp_reachable": True, "tx_success_rate": 0.85,
    "avg_connection_latency_ms": 250.0, "fee_to_volume_ratio": 0.02,
    "settlement_fulfillment_rate": 0.90, "cross_asset_success_rate": 0.80,
    "tx_frequency_monthly": 10, "tx_volume_monthly_usd": 150.0,
    "reserve_liquidity_usd": 40.0, "fallback_route_available": True
}

latencies = np.linspace(50, 2000, 100)
scores_sensitivity = []

for lat in latencies:
    f = base_features.copy()
    f["avg_connection_latency_ms"] = float(lat)
    dims = pipeline.compute_all_dimensions(f)
    comp = weighting_strategy.compute_composite_score(dims, weights)
    scores_sensitivity.append(float(comp.value))

plt.figure(figsize=(10, 5))
plt.plot(latencies, scores_sensitivity, color="darkred", linewidth=2.5)
plt.title("Sensitivity Curve: Latency (ms) vs Overall FAI Score", fontweight="bold")
plt.xlabel("Average Connection Latency (ms)")
plt.ylabel("Overall FAI Score [0.00, 100.00]")
plt.ylim(0, 100)
plt.axvline(200, color="gray", linestyle="--", label="Penalty Trigger (200ms)")
plt.legend()
plt.show()
""")
    ]
    return nb


def build_notebook_02() -> nbf.NotebookNode:
    nb = nbf.v4.new_notebook()

    nb.cells = [
        nbf.v4.new_markdown_cell("""# 🔬 Benchmark: Weighting Strategies & PCA Variance Analysis

This notebook provides an econometric benchmark comparing the **Deterministic Linear Weighting Strategy** against the multivariate **PCA Statistical Weighting Strategy**.

### Key Analysis Components:
1. **Principal Component Analysis (PCA)**: Explained variance ratio and cumulative variance across 7 dimensions.
2. **Factor Loadings Heatmap**: Dimension weights derived from principal component eigenvectors.
3. **Comparative Distribution Analysis**: Deterministic vs PCA score comparisons.
"""),
        nbf.v4.new_code_cell("""import sys
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(".."))

from src.domain.access_index.dimension_calculators import FAIDimensionPipeline
from src.domain.access_index.weighting import DeterministicLinearWeightingStrategy, PCAStatisticalWeightingStrategy
from src.domain.access_index.dimensions import WeightVector
from src.domain.shared.value_objects import DimensionKey

sns.set_theme(style="whitegrid")
"""),
        nbf.v4.new_markdown_cell("""## 1. Load Telemetry & Compute Dimension Matrix"""),
        nbf.v4.new_code_cell("""dataset_path = os.path.join("..", "data", "synthetic", "profiles_dataset.csv")
df_raw = pd.read_csv(dataset_path)

pipeline = FAIDimensionPipeline()
dim_matrix = []

for _, row in df_raw.iterrows():
    dims = pipeline.compute_all_dimensions(row.to_dict())
    dim_matrix.append({k.value: float(v.score.value) for k, v in dims.items()})

df_dims = pd.DataFrame(dim_matrix)
print("Dimension Matrix Shape:", df_dims.shape)
df_dims.describe()
"""),
        nbf.v4.new_markdown_cell("""## 2. Principal Component Analysis (PCA) Variance Analysis"""),
        nbf.v4.new_code_cell("""scaler = StandardScaler()
X_scaled = scaler.fit_transform(df_dims)

pca = PCA(n_components=7)
X_pca = pca.fit_transform(X_scaled)

explained_variance = pca.explained_variance_ratio_
cum_variance = np.cumsum(explained_variance)

df_pca_var = pd.DataFrame({
    "Component": [f"PC{i+1}" for i in range(7)],
    "Explained Variance Ratio": explained_variance,
    "Cumulative Variance": cum_variance,
})

print(df_pca_var.to_string(index=False))

fig, ax1 = plt.subplots(figsize=(9, 5))

color = 'tab:indigo'
ax1.set_xlabel('Principal Components', fontweight='bold')
ax1.set_ylabel('Explained Variance Ratio', color=color, fontweight='bold')
ax1.bar(df_pca_var['Component'], df_pca_var['Explained Variance Ratio'], color=color, alpha=0.6)
ax1.tick_params(axis='y', labelcolor=color)

ax2 = ax1.twinx()
color = 'tab:red'
ax2.set_ylabel('Cumulative Variance', color=color, fontweight='bold')
ax2.plot(df_pca_var['Component'], df_pca_var['Cumulative Variance'], color=color, marker='o', linewidth=2.5)
ax2.tick_params(axis='y', labelcolor=color)

plt.title("PCA Explained Variance & Cumulative Curve across 7 FAI Dimensions", fontweight='bold')
plt.show()
"""),
        nbf.v4.new_markdown_cell("""## 3. PCA Factor Loadings (Dimension Weight Coefficients)"""),
        nbf.v4.new_code_cell("""loadings = pd.DataFrame(
    pca.components_.T,
    columns=[f"PC{i+1}" for i in range(7)],
    index=[k.value.capitalize() for k in DimensionKey]
)

plt.figure(figsize=(10, 6))
sns.heatmap(loadings, annot=True, fmt=".3f", cmap="coolwarm", center=0)
plt.title("PCA Eigenvector Factor Loadings Heatmap", fontweight="bold", fontsize=14)
plt.ylabel("FAI Dimension")
plt.show()
"""),
        nbf.v4.new_markdown_cell("""## 4. Scoring Strategy Comparison: Deterministic Linear vs PCA Weighted"""),
        nbf.v4.new_code_cell("""linear_strategy = DeterministicLinearWeightingStrategy()
pca_strategy = PCAStatisticalWeightingStrategy()
weights_equal = WeightVector.default_equal_weights()

# Derive PCA weight vector proportional to PC1 variance contribution
pc1_weights_raw = np.abs(pca.components_[0])
pc1_weights_norm = pc1_weights_raw / np.sum(pc1_weights_raw)
pca_weights_dict = {dim: Decimal(str(round(pc1_weights_norm[i], 4))) for i, dim in enumerate(DimensionKey)}
# Adjust residual to sum exactly to 1.0
residual = Decimal("1.0") - sum(pca_weights_dict.values())
pca_weights_dict[DimensionKey.ACCESS] += residual
pca_weight_vector = WeightVector(weights=pca_weights_dict)

linear_scores = []
pca_scores = []

for _, row in df_raw.iterrows():
    dims = pipeline.compute_all_dimensions(row.to_dict())
    score_lin = linear_strategy.compute_composite_score(dims, weights_equal)
    score_pca = pca_strategy.compute_composite_score(dims, pca_weight_vector)
    
    linear_scores.append(float(score_lin.value))
    pca_scores.append(float(score_pca.value))

df_comp = pd.DataFrame({
    "Deterministic Linear": linear_scores,
    "PCA Variance Weighted": pca_scores,
    "Archetype": df_raw["archetype"]
})

plt.figure(figsize=(10, 6))
sns.kdeplot(data=df_comp, x="Deterministic Linear", fill=True, color="blue", label="Deterministic Linear", alpha=0.4)
sns.kdeplot(data=df_comp, x="PCA Variance Weighted", fill=True, color="green", label="PCA Variance Weighted", alpha=0.4)
plt.title("Distribution Comparison: Deterministic Linear vs PCA Statistical Strategy", fontweight="bold", fontsize=13)
plt.xlabel("Composite FAI Score [0.00, 100.00]")
plt.ylabel("Density")
plt.legend()
plt.show()

print("Descriptive statistics comparison:")
df_comp[["Deterministic Linear", "PCA Variance Weighted"]].describe()
""")
    ]
    return nb


def main() -> None:
    notebook_dir = os.path.join(os.path.dirname(__file__), "..", "notebooks")
    os.makedirs(notebook_dir, exist_ok=True)

    nb01_path = os.path.normpath(os.path.join(notebook_dir, "01_fai_dimension_validation.ipynb"))
    nb02_path = os.path.normpath(os.path.join(notebook_dir, "02_weighting_strategies_benchmark.ipynb"))

    with open(nb01_path, "w", encoding="utf-8") as f:
        nbf.write(build_notebook_01(), f)
    print(f"[NOTEBOOK BUILDER] Created {nb01_path}")

    with open(nb02_path, "w", encoding="utf-8") as f:
        nbf.write(build_notebook_02(), f)
    print(f"[NOTEBOOK BUILDER] Created {nb02_path}")


if __name__ == "__main__":
    main()
