"""Configuration module for the Catalog Service.

Loads settings from environment variables (or .env file) using pydantic-settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings for the Catalog Service.

    All values can be overridden via environment variables or a .env file.

    Attributes:
        database_url: Async PostgreSQL connection string.
        rabbitmq_url: AMQP connection string for RabbitMQ.
        rabbitmq_exchange: Name of the topic exchange used for all domain events.
        rabbitmq_queue_loan_requested: Queue binding for incoming BookLoanRequested events.
        rabbitmq_queue_book_returned: Queue binding for incoming BookReturned events.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    database_url: str = (
        "postgresql+asyncpg://postgres:password@localhost:5432/catalog_db"
    )
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    rabbitmq_exchange: str = "library.events"
    rabbitmq_queue_loan_requested: str = "catalog.loan-requested"
    rabbitmq_queue_book_returned: str = "catalog.book-returned"


def get_settings() -> Settings:
    """Return a cached Settings instance.

    Returns:
        A fully initialised Settings object.
    """
    return Settings()

