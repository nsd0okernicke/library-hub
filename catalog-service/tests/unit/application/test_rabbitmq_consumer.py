"""Unit tests for RabbitmqConsumer (Catalog Service).

Tests the consumer dispatch logic in isolation – no real RabbitMQ connection.
"""
from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from catalog.infrastructure.messaging.rabbitmq_consumer import RabbitmqConsumer


def _make_message(payload: dict, routing_key: str = "book.loan.requested") -> MagicMock:
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
    async def test_book_loan_requested_triggers_reserve_use_case(self) -> None:
        """BookLoanRequested message calls ReserveBookUseCase.execute()."""
        reserve_uc = AsyncMock()
        return_uc = AsyncMock()
        consumer = RabbitmqConsumer(reserve_use_case=reserve_uc, return_use_case=return_uc)
        loan_id = str(uuid.uuid4())
        msg = _make_message(
            {"event_type": "BookLoanRequested", "loan_id": loan_id, "isbn": "9783161484100"},
            routing_key="book.loan.requested",
        )
        await consumer.handle_message(msg)
        reserve_uc.execute.assert_called_once()
        call_kwargs = reserve_uc.execute.call_args.kwargs
        assert str(call_kwargs["isbn"]) == "9783161484100"
        assert call_kwargs["loan_id"] == loan_id

    @pytest.mark.asyncio
    async def test_book_returned_triggers_return_use_case(self) -> None:
        """BookReturned message calls ReturnBookUseCase.execute()."""
        reserve_uc = AsyncMock()
        return_uc = AsyncMock()
        consumer = RabbitmqConsumer(reserve_use_case=reserve_uc, return_use_case=return_uc)
        msg = _make_message(
            {"event_type": "BookReturned", "isbn": "9783161484100"},
            routing_key="book.returned",
        )
        await consumer.handle_message(msg)
        return_uc.execute.assert_called_once()
        call_kwargs = return_uc.execute.call_args.kwargs
        assert str(call_kwargs["isbn"]) == "9783161484100"

    @pytest.mark.asyncio
    async def test_message_is_acked_on_success(self) -> None:
        """Message is acked after successful processing."""
        reserve_uc = AsyncMock()
        return_uc = AsyncMock()
        consumer = RabbitmqConsumer(reserve_use_case=reserve_uc, return_use_case=return_uc)
        loan_id = str(uuid.uuid4())
        msg = _make_message(
            {"event_type": "BookLoanRequested", "loan_id": loan_id, "isbn": "9783161484100"},
            routing_key="book.loan.requested",
        )
        await consumer.handle_message(msg)
        msg.ack.assert_called_once()

    @pytest.mark.asyncio
    async def test_message_is_nacked_on_error(self) -> None:
        """Message is nacked (requeue=False) if use case raises."""
        reserve_uc = AsyncMock()
        reserve_uc.execute.side_effect = ValueError("No stock found")
        return_uc = AsyncMock()
        consumer = RabbitmqConsumer(reserve_use_case=reserve_uc, return_use_case=return_uc)
        loan_id = str(uuid.uuid4())
        msg = _make_message(
            {"event_type": "BookLoanRequested", "loan_id": loan_id, "isbn": "9783161484100"},
            routing_key="book.loan.requested",
        )
        await consumer.handle_message(msg)
        msg.nack.assert_called_once_with(requeue=False)
        msg.ack.assert_not_called()

    @pytest.mark.asyncio
    async def test_unknown_routing_key_is_acked_and_ignored(self) -> None:
        """Unknown routing key is acked and silently ignored."""
        reserve_uc = AsyncMock()
        return_uc = AsyncMock()
        consumer = RabbitmqConsumer(reserve_use_case=reserve_uc, return_use_case=return_uc)
        msg = _make_message({"event_type": "Unknown"}, routing_key="something.unknown")
        await consumer.handle_message(msg)
        msg.ack.assert_called_once()
        reserve_uc.execute.assert_not_called()
        return_uc.execute.assert_not_called()

