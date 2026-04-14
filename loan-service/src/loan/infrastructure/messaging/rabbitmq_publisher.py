"""RabbitMQ publisher adapter for the Loan Service."""
from __future__ import annotations

import json
from typing import Any

import aio_pika

from loan.domain.ports.message_publisher import MessagePublisher


class RabbitmqPublisher(MessagePublisher):
    """Publishes domain events to a RabbitMQ topic exchange.

    Args:
        exchange: An aio-pika AbstractExchange instance.
        exchange_name: Name of the exchange (used for logging only).
    """

    def __init__(self, exchange: aio_pika.abc.AbstractExchange, exchange_name: str) -> None:
        self._exchange = exchange
        self._exchange_name = exchange_name

    async def publish(self, routing_key: str, payload: dict[str, Any]) -> None:
        """Serialise payload as JSON and publish to the exchange.

        Args:
            routing_key: RabbitMQ routing key (e.g. 'book.loan.requested').
            payload: Event payload dict – must be JSON-serialisable.
        """
        body = json.dumps(payload, default=str).encode("utf-8")
        message = aio_pika.Message(
            body=body,
            content_type="application/json",
        )
        await self._exchange.publish(message, routing_key=routing_key)

