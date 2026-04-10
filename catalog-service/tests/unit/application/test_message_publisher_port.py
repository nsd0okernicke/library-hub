"""Contract-Tests für den MessagePublisher-Port (Catalog Service).

🔴 RED-Phase: Diese Tests müssen FEHLSCHLAGEN, bevor die Implementierung beginnt.
Getestete Klasse: catalog.ports.message_publisher.MessagePublisher
"""

from __future__ import annotations

from typing import Any

import pytest

from catalog.domain.ports.message_publisher import MessagePublisher


class FakeMessagePublisher(MessagePublisher):
    """In-Memory-Implementierung des MessagePublisher-Ports für Tests."""

    def __init__(self) -> None:
        self.published: list[dict[str, Any]] = []

    async def publish(self, routing_key: str, payload: dict[str, Any]) -> None:
        self.published.append({"routing_key": routing_key, "payload": payload})


class TestMessagePublisherIsAbstract:
    """Der Port muss ein abstraktes Interface sein."""

    def test_cannot_instantiate_abstract_class(self) -> None:
        """MessagePublisher kann nicht direkt instanziiert werden."""
        with pytest.raises(TypeError):
            MessagePublisher()  # type: ignore[abstract]

    def test_fake_can_be_instantiated(self) -> None:
        """Eine konkrete Implementierung kann instanziiert werden."""
        publisher = FakeMessagePublisher()
        assert publisher is not None


class TestMessagePublisherContract:
    """Vertrag: publish() muss routing_key und payload enthalten."""

    @pytest.fixture
    def publisher(self) -> FakeMessagePublisher:
        return FakeMessagePublisher()

    @pytest.mark.asyncio
    async def test_publish_stores_message(
        self, publisher: FakeMessagePublisher
    ) -> None:
        """publish() sendet eine Nachricht mit routing_key und payload."""
        payload = {
            "event_type": "BookReserved",
            "version": "1.0",
            "occurred_at": "2026-04-09T10:00:00Z",
            "loan_id": "some-uuid",
            "isbn": "978-3-16-148410-0",
        }
        await publisher.publish("book.reserved", payload)
        assert len(publisher.published) == 1
        assert publisher.published[0]["routing_key"] == "book.reserved"
        assert publisher.published[0]["payload"]["event_type"] == "BookReserved"

    @pytest.mark.asyncio
    async def test_publish_multiple_messages(
        self, publisher: FakeMessagePublisher
    ) -> None:
        """Mehrere publish()-Aufrufe erzeugen mehrere Nachrichten."""
        await publisher.publish(
            "book.reserved", {"event_type": "BookReserved", "version": "1.0"}
        )
        await publisher.publish(
            "book.out_of_stock",
            {"event_type": "BookOutOfStock", "version": "1.0"},
        )
        assert len(publisher.published) == 2

