"""
Integration test for the DB adapter of the Catalog Service.
Tests the connection to PostgreSQL via Testcontainers.

Test status: RED (adapter not yet implemented)
"""

import pytest
from testcontainers.postgres import PostgresContainer

@pytest.mark.asyncio
async def test_catalog_db_adapter_integration():
    """Tests whether the DB adapter works with a real PostgreSQL instance."""
    with PostgresContainer("postgres:15") as postgres:
        # Adapter would be initialised and tested here.
        # Example: open connection, create table, save/read a record.
        # Currently: test fails because the adapter is not yet implemented.
        assert False, "DB adapter not yet implemented"
