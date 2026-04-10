"""Port: MessagePublisher (Catalog Service).

Defines the abstract interface for publishing domain events to the message broker.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class MessagePublisher(ABC):
    """Abstract port for publishing domain events via a message broker (RabbitMQ).

    The concrete adapter wraps aio-pika. A fake in-memory implementation
    is used in unit and application layer tests.
    """

    @abstractmethod
    async def publish(self, routing_key: str, payload: dict[str, Any]) -> None:
        """Publish a domain event to the broker.

        Args:
            routing_key: RabbitMQ routing key (e.g. ``"book.reserved"``).
            payload: JSON-serialisable event payload including
                ``event_type``, ``version``, and ``occurred_at``
                (see requirements.md §8).
        """

