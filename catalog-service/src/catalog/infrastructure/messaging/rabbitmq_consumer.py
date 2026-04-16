"""RabbitMQ consumer adapter for the Catalog Service.

Consumes:
  - book.loan.requested  →  ReserveBookUseCase
  - book.returned        →  ReturnBookUseCase
"""

from __future__ import annotations

import json
import logging

import aio_pika

from catalog.application.reserve_book_use_case import ReserveBookUseCase
from catalog.application.return_book_use_case import ReturnBookUseCase
from catalog.domain.isbn import Isbn

logger = logging.getLogger(__name__)


class RabbitmqConsumer:
    """Dispatches incoming RabbitMQ messages to the appropriate use case.

    Args:
        reserve_use_case: Use case for handling BookLoanRequested events.
        return_use_case: Use case for handling BookReturned events.
    """

    def __init__(
        self,
        reserve_use_case: ReserveBookUseCase,
        return_use_case: ReturnBookUseCase,
    ) -> None:
        self._reserve = reserve_use_case
        self._return = return_use_case

    async def handle_message(
        self, message: aio_pika.abc.AbstractIncomingMessage
    ) -> None:
        """Decode and dispatch an incoming RabbitMQ message.

        Acks the message on success, nacks (no requeue) on any error.

        Args:
            message: Incoming aio-pika message.
        """
        try:
            payload = json.loads(message.body.decode("utf-8"))
            routing_key = message.routing_key

            if routing_key == "book.loan.requested":
                await self._reserve.execute(
                    isbn=Isbn(payload["isbn"]),
                    loan_id=payload["loan_id"],
                )
            elif routing_key == "book.returned":
                await self._return.execute(isbn=Isbn(payload["isbn"]))
            else:
                logger.warning(
                    "Catalog consumer: unknown routing key '%s' – ignored", routing_key
                )

            await message.ack()

        except Exception as exc:
            logger.exception(
                "Catalog consumer: failed to process message (routing_key=%s): %s",
                getattr(message, "routing_key", "unknown"),
                exc,
            )
            await message.nack(requeue=False)
