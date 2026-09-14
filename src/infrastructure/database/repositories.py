"""SQLAlchemy repository implementations for domain aggregates."""
from datetime import UTC
from uuid import UUID


class FinancialProfileRepository:
    """Repository interface + in-memory implementation for FinancialProfile aggregates.

    In production this class would be injected with an AsyncSession.
    The in-memory implementation allows the full domain + application layer
    to function without a running PostgreSQL instance.
    """

    def __init__(self) -> None:
        self._store: dict[UUID, dict] = {}

    async def save(self, profile_data: dict) -> None:
        """Persists or updates a FinancialProfile snapshot."""
        pid = profile_data["profile_id"]
        self._store[pid] = profile_data

    async def get_by_id(self, profile_id: UUID) -> dict | None:
        """Retrieves a FinancialProfile snapshot by its UUID."""
        return self._store.get(profile_id)

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[dict]:
        """Returns paginated list of all stored profiles."""
        items = list(self._store.values())
        return items[offset: offset + limit]


class FAIScoreRepository:
    """Repository for FAI score snapshots.

    Provides time-series access to historical score calculations.
    """

    def __init__(self) -> None:
        self._store: list[dict] = []

    async def save(self, score_data: dict) -> None:
        """Appends a FAI score snapshot to the time-series store."""
        self._store.append(score_data)

    async def get_latest_by_profile(self, profile_id: UUID) -> dict | None:
        """Returns the most recently calculated score for a given profile."""
        matching = [s for s in self._store if s.get("profile_id") == profile_id]
        return matching[-1] if matching else None

    async def get_history_by_profile(self, profile_id: UUID, limit: int = 20) -> list[dict]:
        """Returns up to `limit` historical scores for a given profile, newest first."""
        matching = [s for s in self._store if s.get("profile_id") == profile_id]
        return list(reversed(matching))[:limit]


class BarrierRepository:
    """Repository for diagnosed structural barriers."""

    def __init__(self) -> None:
        self._store: dict[UUID, dict] = {}

    async def save(self, barrier_data: dict) -> None:
        """Persists a barrier record."""
        bid = barrier_data["barrier_id"]
        self._store[bid] = barrier_data

    async def get_active_by_profile(self, profile_id: UUID) -> list[dict]:
        """Returns all non-resolved barriers for a given profile."""
        return [
            b for b in self._store.values()
            if b.get("profile_id") == profile_id and b.get("state") != "RESOLVED"
        ]

    async def resolve(self, barrier_id: UUID) -> None:
        """Marks a barrier as RESOLVED."""
        from datetime import datetime
        if barrier_id in self._store:
            self._store[barrier_id]["state"] = "RESOLVED"
            self._store[barrier_id]["resolved_at"] = datetime.now(UTC).isoformat()


class InterventionRepository:
    """Repository for intervention plans and execution records."""

    def __init__(self) -> None:
        self._store: dict[UUID, dict] = {}

    async def save(self, intervention_data: dict) -> None:
        """Persists an intervention record."""
        iid = intervention_data["intervention_id"]
        self._store[iid] = intervention_data

    async def get_by_profile(self, profile_id: UUID) -> list[dict]:
        """Returns all interventions associated with a given profile."""
        return [i for i in self._store.values() if i.get("profile_id") == profile_id]

    async def update_status(self, intervention_id: UUID, status: str) -> None:
        """Updates the execution status of an intervention."""
        from datetime import datetime
        if intervention_id in self._store:
            self._store[intervention_id]["status"] = status
            if status == "COMPLETED":
                self._store[intervention_id]["executed_at"] = datetime.now(UTC).isoformat()
