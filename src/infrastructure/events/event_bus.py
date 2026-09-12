"""In-process async event bus for domain event dispatching.

Provides a lightweight publish/subscribe mechanism for domain events
following the Observer pattern. In production this should be replaced
or augmented with a message broker (e.g., Kafka, RabbitMQ, Redis Streams).
"""
from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any, Awaitable, Callable, Dict, List, Type

from src.domain.shared.events import DomainEvent


# Handler type: an async callable that receives a DomainEvent
EventHandler = Callable[[DomainEvent], Awaitable[None]]


class InMemoryEventBus:
    """In-process async event bus implementing the publish/subscribe pattern.

    Usage::

        bus = InMemoryEventBus()

        @bus.subscribe(FinancialScoreCalculated)
        async def on_score_calculated(event: FinancialScoreCalculated) -> None:
            print(f"Score calculated for {event.profile_id}: {event.overall_score}")

        await bus.publish(FinancialScoreCalculated(...))
    """

    def __init__(self) -> None:
        self._handlers: Dict[str, List[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: Type[DomainEvent]) -> Callable:
        """Decorator to register an async handler for a given DomainEvent type.

        Args:
            event_type: The DomainEvent subclass to subscribe to.

        Returns:
            Decorator wrapping the original handler function.
        """
        def decorator(handler: EventHandler) -> EventHandler:
            self._handlers[event_type.__name__].append(handler)
            return handler
        return decorator

    def register(self, event_type: Type[DomainEvent], handler: EventHandler) -> None:
        """Programmatic handler registration (alternative to @subscribe decorator).

        Args:
            event_type: The DomainEvent subclass.
            handler: Async callable handler.
        """
        self._handlers[event_type.__name__].append(handler)

    async def publish(self, event: DomainEvent) -> None:
        """Dispatches a domain event to all registered handlers.

        Handlers are invoked concurrently using asyncio.gather.

        Args:
            event: The domain event instance to dispatch.
        """
        handlers = self._handlers.get(type(event).__name__, [])
        if handlers:
            await asyncio.gather(*[handler(event) for handler in handlers], return_exceptions=True)

    async def publish_all(self, events: List[DomainEvent]) -> None:
        """Dispatches multiple domain events sequentially.

        Args:
            events: List of domain events to dispatch in order.
        """
        for event in events:
            await self.publish(event)

    def handler_count(self, event_type: Type[DomainEvent]) -> int:
        """Returns the number of registered handlers for a given event type.

        Args:
            event_type: The event type to check.

        Returns:
            Number of registered handlers.
        """
        return len(self._handlers.get(event_type.__name__, []))

    def clear(self) -> None:
        """Removes all registered handlers (useful for testing)."""
        self._handlers.clear()


# Global singleton event bus — used across the application layer
_default_bus: InMemoryEventBus | None = None


def get_event_bus() -> InMemoryEventBus:
    """Returns the global singleton InMemoryEventBus instance.

    Returns:
        The application-wide event bus.
    """
    global _default_bus
    if _default_bus is None:
        _default_bus = InMemoryEventBus()
    return _default_bus
