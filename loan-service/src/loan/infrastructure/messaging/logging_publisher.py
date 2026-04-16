"""No-op MessagePublisher for local development.

Logs published messages instead of sending them to RabbitMQ.
Replace with a real RabbitMQ adapter when the messaging infrastructure is ready.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from loan.domain.ports.message_publisher import MessagePublisher

logger = logging.getLogger(__name__)


class LoggingMessagePublisher(MessagePublisher):
    """Development-only publisher that logs messages instead of sending them.

    Useful for manual testing without a running RabbitMQ instance.
    """

    async def publish(self, routing_key: str, payload: dict[str, Any]) -> None:
        """Log the message payload instead of publishing to RabbitMQ.

        Args:
            routing_key: The routing key that would be used.
            payload: The event payload that would be published.
        """
        logger.info(
            "[LoggingMessagePublisher] routing_key=%s payload=%s",
            routing_key,
            json.dumps(payload, default=str),
        )
