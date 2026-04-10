"""Contract-Tests für den MessagePublisher-Port (Loan Service).

🔴 RED-Phase: Diese Tests müssen FEHLSCHLAGEN, bevor die Implementierung beginnt.
Getestete Klasse: loan.ports.message_publisher.MessagePublisher
"""

from __future__ import annotations

from typing import Any

import pytest

from loan.domain.ports.message_publisher import MessagePublisher


class FakeMessagePublisher(MessagePublisher):
    """In-Memory-Implementierung des MessagePublisher-Ports für Tests."""

    def __init__(self) -> None:
        self.published: list[dict[str, Any]] = []

    async def publish(self, routing_key: str, payload: dict[str, Any]) -> None:
        self.published.append({"routing_key": routing_key, "payload": payload})


class TestMessagePublisherIsAbstract:
    def test_cannot_instantiate_abstract_class(self) -> None:
        """MessagePublisher kann nicht direkt instanziiert werden."""
        with pytest.raises(TypeError):
            MessagePublisher()  # type: ignore[abstract]

    def test_fake_can_be_instantiated(self) -> None:
        publisher = FakeMessagePublisher()
        assert publisher is not None


class TestMessagePublisherContract:
    @pytest.fixture
    def publisher(self) -> FakeMessagePublisher:
        return FakeMessagePublisher()

    @pytest.mark.asyncio
    async def test_publish_book_loan_requested(
        self, publisher: FakeMessagePublisher
    ) -> None:
        """publish() für BookLoanRequested-Event (requirements.md §8)."""
        payload = {
            "event_type": "BookLoanRequested",
            "version": "1.0",
            "occurred_at": "2026-04-09T10:00:00Z",
            "loan_id": "some-uuid",
            "isbn": "978-3-16-148410-0",
            "user_id": "user-uuid",
        }
        await publisher.publish("book.loan.requested", payload)
        assert len(publisher.published) == 1
        assert publisher.published[0]["routing_key"] == "book.loan.requested"
        assert publisher.published[0]["payload"]["event_type"] == "BookLoanRequested"
        assert publisher.published[0]["payload"]["version"] == "1.0"

    @pytest.mark.asyncio
    async def test_publish_book_returned(self, publisher: FakeMessagePublisher) -> None:
        """publish() für BookReturned-Event (requirements.md §8)."""
        payload = {
            "event_type": "BookReturned",
            "version": "1.0",
            "occurred_at": "2026-04-09T11:00:00Z",
            "loan_id": "some-uuid",
            "isbn": "978-3-16-148410-0",
        }
        await publisher.publish("book.returned", payload)
        assert publisher.published[0]["payload"]["event_type"] == "BookReturned"

