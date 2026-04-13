"""
Integrationstest für den DB-Adapter des Loan Service.
Testet die Anbindung an PostgreSQL über Testcontainers.

Test-Status: RED (Adapter noch nicht implementiert)
"""

import pytest
from testcontainers.postgres import PostgresContainer

@pytest.mark.asyncio
async def test_loan_db_adapter_integration():
    """Testet, ob der DB-Adapter mit einer echten PostgreSQL-Instanz funktioniert."""
    with PostgresContainer("postgres:15") as postgres:
        # Hier würde der Adapter initialisiert und getestet
        # Beispiel: Verbindung aufbauen, Tabelle anlegen, Datensatz speichern/lesen
        # Aktuell: Test schlägt fehl, da Adapter noch nicht implementiert
        assert False, "DB-Adapter noch nicht implementiert"
