"""SQLAlchemy ORM models for Book and BookStock."""
from sqlalchemy import Column, String, Integer
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class BookModel(Base, AsyncAttrs):
    """ORM model for the 'books' table."""

    __tablename__ = "books"
    isbn = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    genre = Column(String, nullable=False)
    description = Column(String, nullable=True)


class BookStockModel(Base, AsyncAttrs):
    """ORM model for the 'book_stock' table."""

    __tablename__ = "book_stock"
    isbn = Column(String, primary_key=True)
    available_count = Column(Integer, nullable=False)
