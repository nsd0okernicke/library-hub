"""Configuration module for the Loan Service.

Loads settings from environment variables (or .env file) using pydantic-settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings for the Loan Service.

    All values can be overridden via environment variables or a .env file.

    Attributes:
        database_url: Async PostgreSQL connection string.
        rabbitmq_url: AMQP connection string for RabbitMQ.
        rabbitmq_exchange: Name of the topic exchange used for all domain events.
        rabbitmq_queue_book_reserved: Queue binding for incoming BookReserved events.
        rabbitmq_queue_book_out_of_stock: Queue binding for incoming BookOutOfStock events.
        loan_duration_days: Default loan duration in days (default: 28).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    database_url: str = (
        "postgresql+asyncpg://postgres:password@localhost:5432/loan_db"
    )
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    rabbitmq_exchange: str = "library.events"
    rabbitmq_queue_book_reserved: str = "loan.book-reserved"
    rabbitmq_queue_book_out_of_stock: str = "loan.book-out-of-stock"
    loan_duration_days: int = 28


def get_settings() -> Settings:
    """Return a cached Settings instance.

    Returns:
        A fully initialised Settings object.
    """
    return Settings()

