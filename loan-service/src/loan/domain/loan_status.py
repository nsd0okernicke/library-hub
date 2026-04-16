"""Domain model: LoanStatus enumeration (Loan Service).

Defines all valid states of a Loan and the allowed transitions between them,
as specified in concept.md (LoanStatus – Zustandsübergänge).
"""

from enum import StrEnum


class LoanStatus(StrEnum):
    """Enumeration of all possible loan states.

    Values are stored as plain strings for easy database persistence
    (SQLAlchemy VARCHAR column).

    States:
        PENDING:  Initial state. BookLoanRequested event has been published.
        ACTIVE:   BookReserved event received. Loan is confirmed.
        RETURNED: Book has been physically returned. Terminal state.
        REJECTED: BookOutOfStock event received. Terminal state.
    """

    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    RETURNED = "RETURNED"
    REJECTED = "REJECTED"
