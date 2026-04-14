"""Unit tests for RabbitmqConsumer (Loan Service).

Tests the consumer dispatch logic in isolation – no real RabbitMQ connection.
"""
from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from loan.infrastructure.messaging.rabbitmq_consumer import RabbitmqConsumer


def _make_message(payload: dict, routing_key: str = "book.reserved") -> MagicMock:
    """Create a fake aio-pika IncomingMessage."""
    msg = MagicMock()
    msg.body = json.dumps(payload).encode("utf-8")
    msg.routing_key = routing_key
    msg.ack = AsyncMock()
    msg.nack = AsyncMock()
    return msg


class TestRabbitmqConsumerDispatch:
    """Tests for message dispatch in RabbitmqConsumer."""

    @pytest.mark.asyncio
    async def test_book_reserved_triggers_activate_use_case(self) -> None:
        """BookReserved message calls ActivateLoanUseCase.execute()."""
        activate_uc = AsyncMock()
        reject_uc = AsyncMock()
        consumer = RabbitmqConsumer(
            activate_use_case=activate_uc,
            reject_use_case=reject_uc,
        )
        loan_id = str(uuid.uuid4())
        msg = _make_message(
            {"event_type": "BookReserved", "loan_id": loan_id},
            routing_key="book.reserved",
        )
        await consumer.handle_message(msg)
        activate_uc.execute.assert_called_once()
        call_kwargs = activate_uc.execute.call_args.kwargs
        assert call_kwargs["loan_id"] == uuid.UUID(loan_id)

    @pytest.mark.asyncio
    async def test_book_out_of_stock_triggers_reject_use_case(self) -> None:
        """BookOutOfStock message calls RejectLoanUseCase.execute()."""
        activate_uc = AsyncMock()
        reject_uc = AsyncMock()
        consumer = RabbitmqConsumer(
            activate_use_case=activate_uc,
            reject_use_case=reject_uc,
        )
        loan_id = str(uuid.uuid4())
        msg = _make_message(
            {"event_type": "BookOutOfStock", "loan_id": loan_id},
            routing_key="book.out_of_stock",
        )
        await consumer.handle_message(msg)
        reject_uc.execute.assert_called_once()
        call_kwargs = reject_uc.execute.call_args.kwargs
        assert call_kwargs["loan_id"] == uuid.UUID(loan_id)

    @pytest.mark.asyncio
    async def test_message_is_acked_on_success(self) -> None:
        """Message is acked after successful processing."""
        activate_uc = AsyncMock()
        reject_uc = AsyncMock()
        consumer = RabbitmqConsumer(
            activate_use_case=activate_uc,
            reject_use_case=reject_uc,
        )
        loan_id = str(uuid.uuid4())
        msg = _make_message(
            {"event_type": "BookReserved", "loan_id": loan_id},
            routing_key="book.reserved",
        )
        await consumer.handle_message(msg)
        msg.ack.assert_called_once()

    @pytest.mark.asyncio
    async def test_message_is_nacked_on_error(self) -> None:
        """Message is nacked (requeue=False) if use case raises."""
        activate_uc = AsyncMock()
        activate_uc.execute.side_effect = ValueError("Loan not found")
        reject_uc = AsyncMock()
        consumer = RabbitmqConsumer(
            activate_use_case=activate_uc,
            reject_use_case=reject_uc,
        )
        loan_id = str(uuid.uuid4())
        msg = _make_message(
            {"event_type": "BookReserved", "loan_id": loan_id},
            routing_key="book.reserved",
        )
        await consumer.handle_message(msg)
        msg.nack.assert_called_once_with(requeue=False)
        msg.ack.assert_not_called()

    @pytest.mark.asyncio
    async def test_unknown_routing_key_is_acked_and_ignored(self) -> None:
        """Unknown routing key is acked and silently ignored."""
        activate_uc = AsyncMock()
        reject_uc = AsyncMock()
        consumer = RabbitmqConsumer(
            activate_use_case=activate_uc,
            reject_use_case=reject_uc,
        )
        msg = _make_message({"event_type": "Unknown"}, routing_key="something.unknown")
        await consumer.handle_message(msg)
        msg.ack.assert_called_once()
        activate_uc.execute.assert_not_called()
        reject_uc.execute.assert_not_called()

