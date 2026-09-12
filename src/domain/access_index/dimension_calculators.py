"""Independent Dimension Calculators for the 7 Financial Access Index Dimensions."""
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any, Dict
import math

from src.domain.access_index.dimensions import FinancialDimension
from src.domain.shared.value_objects import DimensionKey, ScoreValue


class IDimensionCalculator(ABC):
    """Abstract Interface for individual FAI dimension score calculators."""

    @property
    @abstractmethod
    def dimension_key(self) -> DimensionKey:
        """Returns the target dimension key."""
        pass

    @abstractmethod
    def calculate(self, features: Dict[str, Any]) -> FinancialDimension:
        """Calculates normalized dimension score (0.00 to 100.00) from telemetry features."""
        pass


class AccessDimensionCalculator(IDimensionCalculator):
    """1. Access: Measures wallet availability and Interledger protocol reachability."""

    @property
    def dimension_key(self) -> DimensionKey:
        return DimensionKey.ACCESS

    def calculate(self, features: Dict[str, Any]) -> FinancialDimension:
        wallet_count = int(features.get("wallet_count", 0))
        ilp_reachable = bool(features.get("ilp_reachable", False))

        score_raw = 0.0
        if ilp_reachable:
            score_raw += 50.0
        score_raw += min(wallet_count * 25.0, 50.0)

        return FinancialDimension(
            key=self.dimension_key,
            score=ScoreValue.from_float(score_raw),
        )


class ConnectivityDimensionCalculator(IDimensionCalculator):
    """2. Connectivity: Measures transaction success rate and network latency."""

    @property
    def dimension_key(self) -> DimensionKey:
        return DimensionKey.CONNECTIVITY

    def calculate(self, features: Dict[str, Any]) -> FinancialDimension:
        success_rate = float(features.get("tx_success_rate", 0.0))
        latency_ms = float(features.get("avg_connection_latency_ms", 1000.0))

        # Base success score (0-100)
        base = success_rate * 100.0
        # Latency penalty: reduce up to 30 points if latency > 500ms
        latency_penalty = max(0.0, min(30.0, (latency_ms - 200.0) / 20.0))
        score_raw = max(0.0, min(100.0, base - latency_penalty))

        return FinancialDimension(
            key=self.dimension_key,
            score=ScoreValue.from_float(score_raw),
        )


class AffordabilityDimensionCalculator(IDimensionCalculator):
    """3. Affordability: Measures fee ratio relative to transaction volume."""

    @property
    def dimension_key(self) -> DimensionKey:
        return DimensionKey.AFFORDABILITY

    def calculate(self, features: Dict[str, Any]) -> FinancialDimension:
        fee_ratio = float(features.get("fee_to_volume_ratio", 0.05))  # Default 5%

        # Fee ratio decay: 0% fee -> 100 score, >= 10% fee -> 0 score
        score_raw = max(0.0, min(100.0, 100.0 - (fee_ratio * 1000.0)))

        return FinancialDimension(
            key=self.dimension_key,
            score=ScoreValue.from_float(score_raw),
        )


class ReliabilityDimensionCalculator(IDimensionCalculator):
    """4. Reliability: Measures settlement fulfillment consistency over ILP streams."""

    @property
    def dimension_key(self) -> DimensionKey:
        return DimensionKey.RELIABILITY

    def calculate(self, features: Dict[str, Any]) -> FinancialDimension:
        fulfillment_rate = float(features.get("settlement_fulfillment_rate", 0.0))
        score_raw = max(0.0, min(100.0, fulfillment_rate * 100.0))

        return FinancialDimension(
            key=self.dimension_key,
            score=ScoreValue.from_float(score_raw),
        )


class InteroperabilityDimensionCalculator(IDimensionCalculator):
    """5. Interoperability: Measures cross-asset currency conversion success."""

    @property
    def dimension_key(self) -> DimensionKey:
        return DimensionKey.INTEROPERABILITY

    def calculate(self, features: Dict[str, Any]) -> FinancialDimension:
        cross_asset_rate = float(features.get("cross_asset_success_rate", 0.0))
        score_raw = max(0.0, min(100.0, cross_asset_rate * 100.0))

        return FinancialDimension(
            key=self.dimension_key,
            score=ScoreValue.from_float(score_raw),
        )


class UsageDimensionCalculator(IDimensionCalculator):
    """6. Usage: Measures transaction frequency and monthly monetary throughput."""

    @property
    def dimension_key(self) -> DimensionKey:
        return DimensionKey.USAGE

    def calculate(self, features: Dict[str, Any]) -> FinancialDimension:
        tx_freq = int(features.get("tx_frequency_monthly", 0))
        tx_vol = float(features.get("tx_volume_monthly_usd", 0.0))

        freq_score = min(50.0, tx_freq * 3.0)
        vol_score = min(50.0, math.log1p(tx_vol) * 7.5)
        score_raw = min(100.0, freq_score + vol_score)

        return FinancialDimension(
            key=self.dimension_key,
            score=ScoreValue.from_float(score_raw),
        )


class ResilienceDimensionCalculator(IDimensionCalculator):
    """7. Resilience: Measures reserve liquidity buffer and fallback routing options."""

    @property
    def dimension_key(self) -> DimensionKey:
        return DimensionKey.RESILIENCE

    def calculate(self, features: Dict[str, Any]) -> FinancialDimension:
        fallback_avail = bool(features.get("fallback_route_available", False))
        reserve_usd = float(features.get("reserve_liquidity_usd", 0.0))

        score_raw = (40.0 if fallback_avail else 0.0) + min(60.0, math.log1p(reserve_usd) * 9.0)
        score_raw = min(100.0, score_raw)

        return FinancialDimension(
            key=self.dimension_key,
            score=ScoreValue.from_float(score_raw),
        )


class FAIDimensionPipeline:
    """Pipeline orchestrator running all 7 dimension calculators."""

    def __init__(self) -> None:
        self.calculators: Dict[DimensionKey, IDimensionCalculator] = {
            DimensionKey.ACCESS: AccessDimensionCalculator(),
            DimensionKey.CONNECTIVITY: ConnectivityDimensionCalculator(),
            DimensionKey.AFFORDABILITY: AffordabilityDimensionCalculator(),
            DimensionKey.RELIABILITY: ReliabilityDimensionCalculator(),
            DimensionKey.INTEROPERABILITY: InteroperabilityDimensionCalculator(),
            DimensionKey.USAGE: UsageDimensionCalculator(),
            DimensionKey.RESILIENCE: ResilienceDimensionCalculator(),
        }

    def compute_all_dimensions(self, features: Dict[str, Any]) -> Dict[DimensionKey, FinancialDimension]:
        """Runs all 7 calculators and returns a dictionary of FinancialDimension entities."""
        return {dim_key: calc.calculate(features) for dim_key, calc in self.calculators.items()}
