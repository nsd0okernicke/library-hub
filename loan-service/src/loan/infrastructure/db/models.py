"""SQLAlchemy ORM models for Loan and User."""
from sqlalchemy import Column, Date, String
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase


class Base(AsyncAttrs, DeclarativeBase):
    """Shared declarative base for all Loan Service ORM models."""


class UserModel(Base):
    """ORM model for the 'users' table."""

    __tablename__ = "users"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)


class LoanModel(Base):
    """ORM model for the 'loans' table."""

    __tablename__ = "loans"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    isbn = Column(String, nullable=False)
    status = Column(String, nullable=False)
    due_date = Column(Date, nullable=False)
    returned_at = Column(Date, nullable=True)

