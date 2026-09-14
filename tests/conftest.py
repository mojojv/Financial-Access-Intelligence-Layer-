"""Pytest configuration and shared fixtures for Financial Access Intelligence Layer tests."""
import asyncio
from decimal import Decimal
from uuid import uuid4

import pytest

from src.domain.access_index.dimensions import DimensionType, WeightVector
from src.domain.access_index.scoring import FeatureVector
from src.domain.barriers.barriers import Barrier, BarrierCode, BarrierSeverity, BarrierState
from src.domain.shared.value_objects import Money, ProfileID, WalletAddress
from src.infrastructure.cache.redis_adapter import RedisCacheAdapter
from src.infrastructure.database.repositories import (
    BarrierRepository,
    FAIScoreRepository,
    FinancialProfileRepository,
    InterventionRepository,
)
from src.infrastructure.events.event_bus import InMemoryEventBus

# ---------------------------------------------------------------------------
# Event loop configuration
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def event_loop_policy():
    """Use default asyncio event loop policy."""
    return asyncio.DefaultEventLoopPolicy()


# ---------------------------------------------------------------------------
# Domain Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_profile_id() -> ProfileID:
    """Returns a deterministic sample ProfileID for testing."""
    return ProfileID(value=uuid4())


@pytest.fixture
def sample_wallet_address() -> WalletAddress:
    """Returns a valid WalletAddress pointing to a test wallet URL."""
    return WalletAddress(url="https://ilp.wallet.test/alice")


@pytest.fixture
def sample_money_usd() -> Money:
    """Returns a $25.00 USD Money value object."""
    return Money(amount=Decimal("25.00"), asset_code="USD", asset_scale=2)


@pytest.fixture
def healthy_feature_vector() -> FeatureVector:
    """Returns a FeatureVector representing a high-access financial profile."""
    return FeatureVector(
        wallet_count=3,
        ilp_reachable=True,
        tx_success_rate=0.98,
        avg_connection_latency_ms=80.0,
        fee_to_volume_ratio=0.005,
        settlement_fulfillment_rate=0.99,
        cross_asset_success_rate=0.97,
        tx_frequency_monthly=45,
        tx_volume_monthly_usd=1200.0,
        reserve_liquidity_usd=500.0,
        fallback_route_available=True,
    )


@pytest.fixture
def constrained_feature_vector() -> FeatureVector:
    """Returns a FeatureVector representing a constrained / low-access profile."""
    return FeatureVector(
        wallet_count=1,
        ilp_reachable=False,
        tx_success_rate=0.55,
        avg_connection_latency_ms=2200.0,
        fee_to_volume_ratio=0.12,
        settlement_fulfillment_rate=0.60,
        cross_asset_success_rate=0.30,
        tx_frequency_monthly=2,
        tx_volume_monthly_usd=20.0,
        reserve_liquidity_usd=5.0,
        fallback_route_available=False,
    )


@pytest.fixture
def sample_barrier(sample_profile_id: ProfileID) -> Barrier:
    """Returns a sample HIGH_FEES barrier in DIAGNOSED state."""
    return Barrier(
        barrier_id=uuid4(),
        snapshot_id=uuid4(),
        profile_id=sample_profile_id.value,
        barrier_code=BarrierCode.HIGH_FEES,
        dimension=DimensionType.AFFORDABILITY,
        severity=BarrierSeverity.HIGH,
        evidence={"fee_to_volume_ratio": 0.12, "threshold": 0.05},
        state=BarrierState.DIAGNOSED,
    )


@pytest.fixture
def balanced_weight_vector() -> WeightVector:
    """Returns equal weights across all 7 FAI dimensions."""
    return WeightVector(
        weights={
            DimensionType.ACCESS: Decimal("1"),
            DimensionType.CONNECTIVITY: Decimal("1"),
            DimensionType.AFFORDABILITY: Decimal("1"),
            DimensionType.RELIABILITY: Decimal("1"),
            DimensionType.INTEROPERABILITY: Decimal("1"),
            DimensionType.USAGE: Decimal("1"),
            DimensionType.RESILIENCE: Decimal("1"),
        }
    )


# ---------------------------------------------------------------------------
# Infrastructure Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def in_memory_cache() -> RedisCacheAdapter:
    """Returns a RedisCacheAdapter backed by an in-memory dictionary."""
    return RedisCacheAdapter(redis_client=None)


@pytest.fixture
def event_bus() -> InMemoryEventBus:
    """Returns a fresh InMemoryEventBus with no registered handlers."""
    bus = InMemoryEventBus()
    return bus


@pytest.fixture
def profile_repo() -> FinancialProfileRepository:
    """Returns an empty in-memory FinancialProfileRepository."""
    return FinancialProfileRepository()


@pytest.fixture
def score_repo() -> FAIScoreRepository:
    """Returns an empty in-memory FAIScoreRepository."""
    return FAIScoreRepository()


@pytest.fixture
def barrier_repo() -> BarrierRepository:
    """Returns an empty in-memory BarrierRepository."""
    return BarrierRepository()


@pytest.fixture
def intervention_repo() -> InterventionRepository:
    """Returns an empty in-memory InterventionRepository."""
    return InterventionRepository()
