"""Pydantic schemas for Loan objects (API layer of the Loan Service).

Separates request and response schemas following Clean Architecture.
"""
import uuid
from datetime import date
from typing import Optional

from pydantic import BaseModel


class LoanRequest(BaseModel):
    """Schema für eingehende Ausleih-Requests (POST /loans).

    Attributes:
        isbn: ISBN des gewünschten Buches.
        user_id: UUID des ausleihenden Nutzers.
    """

    isbn: str
    user_id: uuid.UUID


class LoanResponse(BaseModel):
    """Schema für einfache Ausleih-Antworten (loan_id + status).

    Attributes:
        loan_id: Eindeutige ID der Ausleihe.
        status: Aktueller Status der Ausleihe.
    """

    loan_id: str
    status: str


class LoanDetailResponse(BaseModel):
    """Schema für detaillierte Ausleih-Antworten.

    Attributes:
        loan_id: Eindeutige ID der Ausleihe.
        isbn: ISBN des ausgeliehenen Buches.
        user_id: UUID des Nutzers.
        status: Aktueller Status.
        due_date: Fälligkeitsdatum.
        returned_at: Rückgabedatum (oder None).
    """

    loan_id: uuid.UUID
    isbn: str
    user_id: uuid.UUID
    status: str
    due_date: date
    returned_at: Optional[date] = None


class LoansListResponse(BaseModel):
    """Schema für eine Liste von Ausleihen.

    Attributes:
        items: Liste der Ausleih-Response-Objekte.
    """

    items: list

