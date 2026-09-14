"""Unit tests for pure DDD Domain Layer (Value Objects, Entities, Aggregate Root, Events)."""
from decimal import Decimal
from uuid import UUID

import pytest

from src.domain.barriers.barriers import (
    BarrierCode,
    BarrierSeverity,
)
from src.domain.shared.events import (
    BarrierDetected,
    FinancialProfileCreated,
    FinancialScoreCalculated,
)
from src.domain.shared.exceptions import (
    InvalidDimensionScoreError,
    InvalidWalletAddressError,
)
from src.domain.shared.value_objects import (
    DimensionKey,
    ScoreValue,
    WalletAddress,
)
from src.domain.users.users import FinancialProfile


def test_score_value_validation() -> None:
    valid_score = ScoreValue.from_float(85.5)
    assert valid_score.value == Decimal("85.50")
    assert str(valid_score) == "85.50"

    with pytest.raises(InvalidDimensionScoreError):
        ScoreValue(Decimal("105.00"))

    with pytest.raises(InvalidDimensionScoreError):
        ScoreValue(Decimal("-5.00"))


def test_wallet_address_validation() -> None:
    valid_wallet = WalletAddress("https://ilp.wallet.com/alice")
    assert str(valid_wallet) == "https://ilp.wallet.com/alice"

    with pytest.raises(InvalidWalletAddressError):
        WalletAddress("http://unsecure-wallet.com/alice")


def test_financial_profile_aggregate_root_flow() -> None:
    wallet = WalletAddress("https://ilp.wallet.com/bob")
    profile = FinancialProfile.create(wallet_address=wallet, currency_code="USD")

    # 1. Check Profile Creation & Event
    assert isinstance(profile.profile_id.value, UUID)
    events = profile.domain_events
    assert len(events) == 1
    assert isinstance(events[0], FinancialProfileCreated)

    profile.clear_domain_events()
    assert len(profile.domain_events) == 0

    # 2. Recalculate FAI Score & Check Event
    dim_map = {
        DimensionKey.ACCESS: 100.0,
        DimensionKey.CONNECTIVITY: 90.0,
        DimensionKey.AFFORDABILITY: 80.0,
        DimensionKey.RELIABILITY: 95.0,
        DimensionKey.INTEROPERABILITY: 85.0,
        DimensionKey.USAGE: 70.0,
        DimensionKey.RESILIENCE: 60.0,
    }
    score = profile.update_score(overall_score_val=82.85, dimension_scores_map=dim_map)

    assert score.overall_score.value == Decimal("82.85")
    events = profile.domain_events
    assert len(events) == 1
    assert isinstance(events[0], FinancialScoreCalculated)
    assert events[0].overall_score == Decimal("82.85")

    # 3. Diagnose Barrier & Check Event
    barrier = profile.record_barrier(
        barrier_code=BarrierCode.HIGH_FEE_BURDEN,
        dimension=DimensionKey.AFFORDABILITY,
        severity=BarrierSeverity.HIGH,
        evidence={"fee_pct": 0.08},
    )

    assert barrier.barrier_code == BarrierCode.HIGH_FEE_BURDEN
    events = profile.domain_events
    assert len(events) == 2
    assert isinstance(events[1], BarrierDetected)
