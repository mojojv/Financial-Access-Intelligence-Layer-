"""Synthetic Financial Telemetry Generator for FAIL Engine Benchmarks and Econometric Analysis.

Generates 1,000 heterogeneous financial profile telemetries across 4 socio-economic archetypes
using statistical distributions (Beta, Log-Normal, Gaussian).
"""
import os
from typing import Dict, List, Any
import numpy as np
import pandas as pd


def generate_synthetic_profiles(n_samples: int = 1000, random_seed: int = 42) -> pd.DataFrame:
    """Generates a DataFrame of synthetic financial profiles with realistic telemetry distributions.

    Args:
        n_samples: Total number of profiles to generate (default: 1000).
        random_seed: Random seed for reproducible statistical sampling.

    Returns:
        Pandas DataFrame containing profile telemetries and archetype metadata.
    """
    np.random.seed(random_seed)

    # 4 Archetypes distribution:
    # Archetype A (Fully Included): 35%
    # Archetype B (Fee Burdened): 25%
    # Archetype C (Low Resilience/Volatile): 20%
    # Archetype D (Disconnected): 20%
    counts = {
        "ARCHETYPE_A_HIGH_ACCESS": int(n_samples * 0.35),
        "ARCHETYPE_B_FEE_BURDENED": int(n_samples * 0.25),
        "ARCHETYPE_C_LOW_RESILIENCE": int(n_samples * 0.20),
        "ARCHETYPE_D_DISCONNECTED": n_samples - int(n_samples * 0.35) - int(n_samples * 0.25) - int(n_samples * 0.20),
    }

    records: List[Dict[str, Any]] = []

    for arch, count in counts.items():
        for _ in range(count):
            profile_id = f"prof-{arch[:3]}-{np.random.randint(100000, 999999)}"

            if arch == "ARCHETYPE_A_HIGH_ACCESS":
                wallet_count = np.random.choice([2, 3, 4], p=[0.3, 0.5, 0.2])
                ilp_reachable = True
                tx_success_rate = float(np.random.beta(a=20, b=1))  # ~0.95 - 0.99
                latency_ms = float(np.random.normal(loc=180, scale=30))  # ~120 - 240ms
                fee_ratio = float(np.random.beta(a=1, b=500))  # ~0.001 - 0.005 (0.1% - 0.5%)
                fulfillment_rate = float(np.random.beta(a=30, b=1))  # ~0.96 - 0.99
                cross_asset_rate = float(np.random.beta(a=25, b=2))  # ~0.90 - 0.98
                tx_freq = int(np.random.poisson(lam=25))
                tx_vol = float(np.random.lognormal(mean=5.5, sigma=0.5))  # ~$200 - $600
                reserves = float(np.random.lognormal(mean=6.0, sigma=0.6))  # ~$300 - $1200
                fallback_avail = True

            elif arch == "ARCHETYPE_B_FEE_BURDENED":
                wallet_count = np.random.choice([1, 2], p=[0.6, 0.4])
                ilp_reachable = True
                tx_success_rate = float(np.random.beta(a=10, b=2))  # ~0.80 - 0.90
                latency_ms = float(np.random.normal(loc=350, scale=50))  # ~250 - 450ms
                fee_ratio = float(np.random.beta(a=5, b=45))  # ~0.06 - 0.14 (6% - 14%)
                fulfillment_rate = float(np.random.beta(a=12, b=3))  # ~0.75 - 0.85
                cross_asset_rate = float(np.random.beta(a=8, b=4))  # ~0.60 - 0.75
                tx_freq = int(np.random.poisson(lam=10))
                tx_vol = float(np.random.lognormal(mean=4.2, sigma=0.4))  # ~$50 - $120
                reserves = float(np.random.lognormal(mean=3.5, sigma=0.5))  # ~$20 - $50
                fallback_avail = bool(np.random.choice([True, False], p=[0.3, 0.7]))

            elif arch == "ARCHETYPE_C_LOW_RESILIENCE":
                wallet_count = np.random.choice([1, 2], p=[0.7, 0.3])
                ilp_reachable = True
                tx_success_rate = float(np.random.beta(a=6, b=4))  # ~0.50 - 0.70
                latency_ms = float(np.random.normal(loc=550, scale=100))  # ~400 - 700ms
                fee_ratio = float(np.random.beta(a=2, b=50))  # ~0.02 - 0.06 (2% - 6%)
                fulfillment_rate = float(np.random.beta(a=5, b=5))  # ~0.40 - 0.60
                cross_asset_rate = float(np.random.beta(a=4, b=6))  # ~0.30 - 0.50
                tx_freq = int(np.random.poisson(lam=5))
                tx_vol = float(np.random.lognormal(mean=3.5, sigma=0.5))  # ~$20 - $60
                reserves = float(np.random.exponential(scale=5.0))  # ~$0 - $15
                fallback_avail = False

            else:  # ARCHETYPE_D_DISCONNECTED
                wallet_count = int(np.random.choice([0, 1], p=[0.7, 0.3]))
                ilp_reachable = bool(np.random.choice([True, False], p=[0.1, 0.9]))
                tx_success_rate = float(np.random.beta(a=2, b=8))  # ~0.10 - 0.30
                latency_ms = float(np.random.normal(loc=2500, scale=500))  # ~1500 - 3500ms
                fee_ratio = float(np.random.beta(a=10, b=30))  # ~0.15 - 0.35 (15% - 35%)
                fulfillment_rate = float(np.random.beta(a=2, b=8))  # ~0.10 - 0.30
                cross_asset_rate = float(np.random.beta(a=1, b=9))  # ~0.05 - 0.20
                tx_freq = int(np.random.poisson(lam=1))
                tx_vol = float(np.random.exponential(scale=10.0))  # ~$0 - $20
                reserves = 0.0
                fallback_avail = False

            records.append({
                "profile_id": profile_id,
                "archetype": arch,
                "wallet_count": max(0, wallet_count),
                "ilp_reachable": ilp_reachable,
                "tx_success_rate": max(0.0, min(1.0, tx_success_rate)),
                "avg_connection_latency_ms": max(10.0, latency_ms),
                "fee_to_volume_ratio": max(0.0, fee_ratio),
                "settlement_fulfillment_rate": max(0.0, min(1.0, fulfillment_rate)),
                "cross_asset_success_rate": max(0.0, min(1.0, cross_asset_rate)),
                "tx_frequency_monthly": max(0, tx_freq),
                "tx_volume_monthly_usd": max(0.0, tx_vol),
                "reserve_liquidity_usd": max(0.0, reserves),
                "fallback_route_available": fallback_avail,
            })

    df = pd.DataFrame(records)
    return df


def main() -> None:
    """Generates synthetic dataset and exports to data/synthetic/profiles_dataset.csv."""
    output_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "synthetic")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.normpath(os.path.join(output_dir, "profiles_dataset.csv"))

    print(f"[DATA GENERATOR] Generating 1,000 synthetic financial profiles...")
    df = generate_synthetic_profiles(n_samples=1000, random_seed=42)
    df.to_csv(output_path, index=False)
    print(f"[DATA GENERATOR] Dataset successfully exported to {output_path}")
    print(f"[DATA GENERATOR] Archetype breakdown:")
    print(df["archetype"].value_counts())


if __name__ == "__main__":
    main()
