"""Events infrastructure package."""
from src.infrastructure.events.event_bus import InMemoryEventBus, get_event_bus

__all__ = ["InMemoryEventBus", "get_event_bus"]
