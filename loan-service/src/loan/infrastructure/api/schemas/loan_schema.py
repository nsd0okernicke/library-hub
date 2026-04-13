"""Pydantic-Schemas für Loan-Objekte (API-Layer).

Trennt Request- und Response-Schemas gemäß Clean Architecture.
"""
from pydantic import BaseModel


class LoanRequest(BaseModel):
    """Schema für eingehende Ausleih-Requests (POST /loans).

    Attributes:
        isbn: ISBN des gewünschten Buches.
        user_id: ID des ausleihenden Nutzers.
    """

    isbn: str
    user_id: str


class LoanResponse(BaseModel):
    """Schema für ausgehende Ausleih-Antworten.

    Attributes:
        loan_id: Eindeutige ID der Ausleihe.
        status: Aktueller Status der Ausleihe.
    """

    loan_id: str
    status: str


class LoansListResponse(BaseModel):
    """Schema für eine Liste von Ausleihen.

    Attributes:
        items: Liste der Ausleih-Response-Objekte.
    """

    items: list

