"""Unit tests for RabbitmqPublisher (Loan Service)."""
from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from loan.infrastructure.messaging.rabbitmq_publisher import RabbitmqPublisher


class TestRabbitmqPublisher:
    """Tests for the RabbitmqPublisher adapter."""

    def _make_publisher(self) -> tuple[RabbitmqPublisher, MagicMock]:
        exchange = AsyncMock()
        publisher = RabbitmqPublisher(exchange=exchange, exchange_name="library.events")
        return publisher, exchange

    @pytest.mark.asyncio
    async def test_publish_sends_message_to_exchange(self) -> None:
        """publish() calls exchange.publish() with a Message."""
        publisher, exchange = self._make_publisher()
        await publisher.publish("book.loan.requested", {"event_type": "BookLoanRequested"})
        exchange.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_uses_correct_routing_key(self) -> None:
        """publish() passes the routing_key to exchange.publish()."""
        publisher, exchange = self._make_publisher()
        await publisher.publish("book.loan.requested", {"event_type": "BookLoanRequested"})
        _, kwargs = exchange.publish.call_args
        assert kwargs.get("routing_key") == "book.loan.requested"

    @pytest.mark.asyncio
    async def test_publish_serialises_payload_as_json(self) -> None:
        """publish() encodes the payload as UTF-8 JSON in the message body."""
        publisher, exchange = self._make_publisher()
        payload: dict[str, Any] = {"event_type": "BookLoanRequested", "loan_id": "some-uuid"}
        await publisher.publish("book.loan.requested", payload)
        args, _ = exchange.publish.call_args
        body = json.loads(args[0].body.decode("utf-8"))
        assert body["event_type"] == "BookLoanRequested"
        assert body["loan_id"] == "some-uuid"

    @pytest.mark.asyncio
    async def test_publish_sets_content_type(self) -> None:
        """publish() sets content_type to 'application/json'."""
        publisher, exchange = self._make_publisher()
        await publisher.publish("book.loan.requested", {"event_type": "BookLoanRequested"})
        args, _ = exchange.publish.call_args
        assert args[0].content_type == "application/json"

    def test_exchange_name_stored(self) -> None:
        """Constructor stores the exchange_name attribute."""
        publisher, _ = self._make_publisher()
        assert publisher._exchange_name == "library.events"

