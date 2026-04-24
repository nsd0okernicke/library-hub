"""Root conftest for catalog-service tests.

Shared fixtures and pytest configuration.
Session-scoped Testcontainer fixtures for PostgreSQL and RabbitMQ
used by adapter integration tests.
"""
import pytest
from testcontainers.postgres import PostgresContainer
from testcontainers.rabbitmq import RabbitMqContainer


@pytest.fixture(scope="session")
def postgres_url() -> str:
    """Start a PostgreSQL Testcontainer and return its async connection URL."""
    with PostgresContainer("postgres:16-alpine") as pg:
        url = pg.get_connection_url().replace("psycopg2", "asyncpg")
        yield url


@pytest.fixture(scope="session")
def rabbitmq_url() -> str:
    """Start a RabbitMQ Testcontainer and return its AMQP URL."""
    with RabbitMqContainer("rabbitmq:3.13-management-alpine") as rmq:
        yield f"amqp://{rmq.username}:{rmq.password}@{rmq.get_container_host_ip()}:{rmq.get_exposed_port(5672)}/"

