"""RabbitMQ consumer adapter for the Loan Service.

Consumes:
  - book.reserved       →  ActivateLoanUseCase
  - book.out_of_stock   →  RejectLoanUseCase
"""
from __future__ import annotations

import json
import logging
import uuid

import aio_pika

from loan.application.activate_loan_use_case import ActivateLoanUseCase
from loan.application.reject_loan_use_case import RejectLoanUseCase

logger = logging.getLogger(__name__)


class RabbitmqConsumer:
    """Dispatches incoming RabbitMQ messages to the appropriate use case.

    Args:
        activate_use_case: Use case for handling BookReserved events.
        reject_use_case: Use case for handling BookOutOfStock events.
    """

    def __init__(
        self,
        activate_use_case: ActivateLoanUseCase,
        reject_use_case: RejectLoanUseCase,
    ) -> None:
        self._activate = activate_use_case
        self._reject = reject_use_case

    async def handle_message(self, message: aio_pika.abc.AbstractIncomingMessage) -> None:
        """Decode and dispatch an incoming RabbitMQ message.

        Acks the message on success, nacks (no requeue) on any error.

        Args:
            message: Incoming aio-pika message.
        """
        try:
            payload = json.loads(message.body.decode("utf-8"))
            routing_key = message.routing_key
            loan_id = uuid.UUID(payload["loan_id"]) if "loan_id" in payload else None

            if routing_key == "book.reserved":
                await self._activate.execute(loan_id=loan_id)
            elif routing_key == "book.out_of_stock":
                await self._reject.execute(loan_id=loan_id)
            else:
                logger.warning("Loan consumer: unknown routing key '%s' – ignored", routing_key)

            await message.ack()

        except Exception as exc:
            logger.exception(
                "Loan consumer: failed to process message (routing_key=%s): %s",
                getattr(message, "routing_key", "unknown"),
                exc,
            )
            await message.nack(requeue=False)

