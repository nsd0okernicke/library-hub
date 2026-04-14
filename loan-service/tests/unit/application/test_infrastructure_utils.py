"""Unit tests for infrastructure utilities: InMemoryUserRepository and LoggingMessagePublisher.

Covers branches not hit by API tests:
- InMemoryUserRepository.find_by_email() when the e-mail is unknown
- LoggingMessagePublisher.publish() log output
"""
from __future__ import annotations

import logging
import uuid

import pytest

from loan.infrastructure.db.fake_repositories import (
    InMemoryMessagePublisher,
    InMemoryUserRepository,
)
from loan.infrastructure.messaging.logging_publisher import LoggingMessagePublisher
from loan.domain.user import User


class TestInMemoryUserRepositoryFindByEmail:
    """Cover the None-path in find_by_email (line 72-73 in fake_repositories.py)."""

    @pytest.mark.asyncio
    async def test_find_by_email_unknown_returns_none(self) -> None:
        """find_by_email returns None when the e-mail is not registered."""
        repo = InMemoryUserRepository()
        result = await repo.find_by_email("unknown@example.com")
        assert result is None

    @pytest.mark.asyncio
    async def test_find_by_email_known_returns_user(self) -> None:
        """find_by_email returns the user when the e-mail is registered."""
        repo = InMemoryUserRepository()
        user = User(name="Alice", email="alice@example.com")
        await repo.save(user)
        result = await repo.find_by_email("alice@example.com")
        assert result == user


class TestInMemoryMessagePublisher:
    """Cover InMemoryMessagePublisher.publish (line 68 in fake_repositories.py)."""

    @pytest.mark.asyncio
    async def test_publish_stores_message(self) -> None:
        """publish() stores routing_key and payload."""
        publisher = InMemoryMessagePublisher()
        await publisher.publish("book.returned", {"event_type": "BookReturned"})
        assert len(publisher.published) == 1
        assert publisher.published[0]["routing_key"] == "book.returned"
        assert publisher.published[0]["payload"]["event_type"] == "BookReturned"


class TestLoggingMessagePublisher:
    """Cover LoggingMessagePublisher.publish (line 30 in logging_publisher.py)."""

    @pytest.mark.asyncio
    async def test_publish_logs_message(self, caplog: pytest.LogCaptureFixture) -> None:
        """publish() logs routing_key and payload at INFO level."""
        publisher = LoggingMessagePublisher()
        with caplog.at_level(logging.INFO):
            await publisher.publish(
                "book.loan.requested",
                {"event_type": "BookLoanRequested", "isbn": "9783161484100"},
            )
        assert "book.loan.requested" in caplog.text
        assert "BookLoanRequested" in caplog.text

