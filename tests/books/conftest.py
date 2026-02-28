import pytest
from typing import AsyncGenerator
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from books.models import Base, Book
from books import BookManager


@pytest.fixture(scope="module")
async def async_engine():
    """Creates an in-memory SQLite database for testing, and ensures the schema is created and dropped properly."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(autouse=True)
async def clean_books_table(async_engine):
    """Ensures the books table is empty before each test to maintain test isolation."""
    yield
    async with async_engine.begin() as conn:
        await conn.execute(delete(Book))


@pytest.fixture
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provides a SQLAlchemy AsyncSession for interacting with the test database."""
    session_factory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session


@pytest.fixture
async def book_manager(db_session: AsyncSession) -> BookManager:
    return BookManager(session=db_session)