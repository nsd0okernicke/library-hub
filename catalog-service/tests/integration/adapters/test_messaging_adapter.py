"""Integration test for the messaging adapter of the Catalog Service.

Tests the RabbitMQ publisher against a real RabbitMQ instance via Testcontainers.
"""

import pytest

import aio_pika

from catalog.infrastructure.messaging.rabbitmq_publisher import RabbitmqPublisher


@pytest.mark.asyncio
async def test_catalog_messaging_adapter_integration(rabbitmq_url: str) -> None:
    """RabbitMQ publisher connects and publishes an event without errors."""
    connection = await aio_pika.connect_robust(rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            "test.events", aio_pika.ExchangeType.TOPIC, durable=False
        )
        publisher = RabbitmqPublisher(exchange=exchange, exchange_name="test.events")
    publisher.publish("book.added", {"isbn": "978-0-596-51774-8", "title": "Test"})
    # If no exception is raised, the adapter works correctly

