"""Tests for infrastructure layer: repositories, cache, and event bus."""
from uuid import uuid4

import pytest

from src.domain.shared.events import BarrierDetected, FinancialScoreCalculated
from src.infrastructure.cache.redis_adapter import RedisCacheAdapter
from src.infrastructure.database.repositories import (
    BarrierRepository,
    FAIScoreRepository,
    FinancialProfileRepository,
)
from src.infrastructure.events.event_bus import InMemoryEventBus

# ---------------------------------------------------------------------------
# RedisCacheAdapter Tests
# ---------------------------------------------------------------------------

class TestRedisCacheAdapter:
    """Tests for in-memory fallback cache adapter."""

    @pytest.mark.asyncio
    async def test_set_and_get_returns_value(self):
        cache = RedisCacheAdapter()
        await cache.set("key:1", {"score": 75.0})
        result = await cache.get("key:1")
        assert result == {"score": 75.0}

    @pytest.mark.asyncio
    async def test_get_missing_key_returns_none(self):
        cache = RedisCacheAdapter()
        result = await cache.get("nonexistent:key")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_removes_key(self):
        cache = RedisCacheAdapter()
        await cache.set("temp:key", "value")
        await cache.delete("temp:key")
        result = await cache.get("temp:key")
        assert result is None

    @pytest.mark.asyncio
    async def test_invalidate_profile_removes_all_profile_keys(self):
        cache = RedisCacheAdapter()
        pid = uuid4()
        await cache.set(RedisCacheAdapter.score_key(pid), {"overall": 80})
        await cache.set(f"fai:profile:{pid}:barriers", [])
        await cache.invalidate_profile(pid)
        assert await cache.get(RedisCacheAdapter.score_key(pid)) is None

    def test_score_key_format(self):
        pid = uuid4()
        key = RedisCacheAdapter.score_key(pid)
        assert f"fai:profile:{pid}:latest_score" == key

    def test_wallet_key_format(self):
        url = "https://ilp.wallet.com/alice"
        key = RedisCacheAdapter.wallet_key(url)
        assert key == f"fai:wallet:{url}"


# ---------------------------------------------------------------------------
# FinancialProfileRepository Tests
# ---------------------------------------------------------------------------

class TestFinancialProfileRepository:
    """Tests for in-memory FinancialProfileRepository."""

    @pytest.mark.asyncio
    async def test_save_and_get_profile(self):
        repo = FinancialProfileRepository()
        pid = uuid4()
        profile = {"profile_id": pid, "wallet_url": "https://wallet.test/bob", "currency_code": "USD"}
        await repo.save(profile)
        result = await repo.get_by_id(pid)
        assert result is not None
        assert result["wallet_url"] == "https://wallet.test/bob"

    @pytest.mark.asyncio
    async def test_get_nonexistent_returns_none(self):
        repo = FinancialProfileRepository()
        result = await repo.get_by_id(uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_list_all_with_pagination(self):
        repo = FinancialProfileRepository()
        for i in range(5):
            await repo.save({"profile_id": uuid4(), "idx": i})
        page = await repo.list_all(limit=3, offset=0)
        assert len(page) == 3


# ---------------------------------------------------------------------------
# FAIScoreRepository Tests
# ---------------------------------------------------------------------------

class TestFAIScoreRepository:
    """Tests for in-memory FAIScoreRepository."""

    @pytest.mark.asyncio
    async def test_save_and_get_latest_score(self):
        repo = FAIScoreRepository()
        pid = uuid4()
        await repo.save({"profile_id": pid, "overall_score": 60.0, "methodology": "DETERMINISTIC_RULES"})
        await repo.save({"profile_id": pid, "overall_score": 75.0, "methodology": "ML_XGBOOST"})
        latest = await repo.get_latest_by_profile(pid)
        assert latest is not None
        assert latest["overall_score"] == 75.0

    @pytest.mark.asyncio
    async def test_get_history_returns_newest_first(self):
        repo = FAIScoreRepository()
        pid = uuid4()
        for score in [40.0, 55.0, 70.0]:
            await repo.save({"profile_id": pid, "overall_score": score})
        history = await repo.get_history_by_profile(pid, limit=10)
        assert history[0]["overall_score"] == 70.0

    @pytest.mark.asyncio
    async def test_no_scores_returns_none(self):
        repo = FAIScoreRepository()
        assert await repo.get_latest_by_profile(uuid4()) is None


# ---------------------------------------------------------------------------
# BarrierRepository Tests
# ---------------------------------------------------------------------------

class TestBarrierRepository:
    """Tests for in-memory BarrierRepository."""

    @pytest.mark.asyncio
    async def test_save_and_get_active_barriers(self):
        repo = BarrierRepository()
        pid = uuid4()
        bid = uuid4()
        await repo.save({"barrier_id": bid, "profile_id": pid, "barrier_code": "HIGH_FEES", "state": "DIAGNOSED"})
        active = await repo.get_active_by_profile(pid)
        assert len(active) == 1

    @pytest.mark.asyncio
    async def test_resolve_barrier_excludes_from_active(self):
        repo = BarrierRepository()
        pid = uuid4()
        bid = uuid4()
        await repo.save({"barrier_id": bid, "profile_id": pid, "state": "DIAGNOSED"})
        await repo.resolve(bid)
        active = await repo.get_active_by_profile(pid)
        assert len(active) == 0


# ---------------------------------------------------------------------------
# InMemoryEventBus Tests
# ---------------------------------------------------------------------------

class TestInMemoryEventBus:
    """Tests for the async in-process event bus."""

    @pytest.mark.asyncio
    async def test_publish_dispatches_to_subscriber(self):
        bus = InMemoryEventBus()
        received = []

        @bus.subscribe(FinancialScoreCalculated)
        async def handler(event: FinancialScoreCalculated) -> None:
            received.append(event)

        event = FinancialScoreCalculated(
            profile_id=uuid4(),
            score_id=uuid4(),
            overall_score=72.5,
            scoring_version="v0.1",
            methodology="DETERMINISTIC_RULES",
        )
        await bus.publish(event)
        assert len(received) == 1
        assert received[0].overall_score == 72.5

    @pytest.mark.asyncio
    async def test_publish_no_handler_does_not_raise(self):
        bus = InMemoryEventBus()
        event = BarrierDetected(
            profile_id=uuid4(),
            barrier_id=uuid4(),
            barrier_code="HIGH_FEES",
            dimension="AFFORDABILITY",
            severity="HIGH",
        )
        # Should complete without error
        await bus.publish(event)

    @pytest.mark.asyncio
    async def test_multiple_handlers_all_invoked(self):
        bus = InMemoryEventBus()
        calls = []

        async def h1(e): calls.append("h1")
        async def h2(e): calls.append("h2")

        bus.register(FinancialScoreCalculated, h1)
        bus.register(FinancialScoreCalculated, h2)

        await bus.publish(FinancialScoreCalculated(
            profile_id=uuid4(), score_id=uuid4(),
            overall_score=55.0, scoring_version="v0.1", methodology="STATISTICAL_COHORT",
        ))
        assert "h1" in calls and "h2" in calls

    @pytest.mark.asyncio
    async def test_publish_all_dispatches_in_order(self):
        bus = InMemoryEventBus()
        order = []

        @bus.subscribe(FinancialScoreCalculated)
        async def on_score(e): order.append(e.overall_score)

        events = [
            FinancialScoreCalculated(profile_id=uuid4(), score_id=uuid4(),
                                      overall_score=float(s), scoring_version="v0.1", methodology="X")
            for s in [10.0, 20.0, 30.0]
        ]
        await bus.publish_all(events)
        assert order == [10.0, 20.0, 30.0]

    def test_handler_count_reflects_registrations(self):
        bus = InMemoryEventBus()
        bus.register(FinancialScoreCalculated, lambda e: None)
        bus.register(FinancialScoreCalculated, lambda e: None)
        assert bus.handler_count(FinancialScoreCalculated) == 2

    def test_clear_removes_all_handlers(self):
        bus = InMemoryEventBus()
        bus.register(FinancialScoreCalculated, lambda e: None)
        bus.clear()
        assert bus.handler_count(FinancialScoreCalculated) == 0
