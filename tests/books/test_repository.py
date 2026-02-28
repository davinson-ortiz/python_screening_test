import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch

from books import BookManager, BookNotFoundError, ValidationError, DataBaseError


CURRENT_YEAR = datetime.now().year

# get_all_books
async def test_add_book_persists_correctly(book_manager: BookManager):
    "The inserted book is recoverable with the exact data provided."
    await book_manager.add_book("1984", "George Orwell", 1949)

    books = await book_manager.get_all_books()

    assert len(books) == 1
    book = books[0]
    assert book.title == "1984"
    assert book.author == "George Orwell"
    assert book.year == 1949


async def test_add_book_strips_whitespace(book_manager: BookManager):
    """Spaces in title and author are removed before persisting."""
    await book_manager.add_book("  Dune  ", "  Frank Herbert  ", 1965)

    books = await book_manager.get_all_books()
    assert books[0].title == "Dune"
    assert books[0].author == "Frank Herbert"


@pytest.mark.parametrize("year", [-1, -500, CURRENT_YEAR + 1, 9999])
async def test_add_book_raises_on_invalid_year(book_manager: BookManager, year: int):
    """Years outside the range [0, current year] throw a ValidationError."""
    with pytest.raises(ValidationError, match=f"Year must be between 0 and {CURRENT_YEAR}."):
        await book_manager.add_book("Título", "Autor", year)


@pytest.mark.parametrize("year", [0, 1, 1949, CURRENT_YEAR])
async def test_add_book_accepts_boundary_years(book_manager: BookManager, year: int):
    "The year range limit values ​​are accepted without exception."
    await book_manager.add_book("Título", "Autor", year)

    books = await book_manager.get_all_books()
    assert books[0].year == year


async def test_get_all_books_returns_empty_on_fresh_state(book_manager: BookManager):
    "The collection is empty before inserting any books."
    books = await book_manager.get_all_books()
    assert books == []


async def test_get_all_books_returns_all_inserted(book_manager: BookManager):
    "Exactly as many books are recovered as were inserted."
    await book_manager.add_book("1984", "George Orwell", 1949)
    await book_manager.add_book("Fahrenheit 451", "Ray Bradbury", 1953)

    books = await book_manager.get_all_books()
    assert len(books) == 2

# find_book
async def test_find_book_matches_by_author(book_manager: BookManager):
    "Searching by author returns only matching books."
    await book_manager.add_book("1984", "George Orwell", 1949)
    await book_manager.add_book("Fahrenheit 451", "Ray Bradbury", 1953)

    result = await book_manager.find_book("Orwell")

    assert len(result) == 1
    assert result[0].title == "1984"
    assert result[0].author == "George Orwell"


async def test_find_book_matches_by_title(book_manager: BookManager):
    "Searching by title returns only matching books."
    await book_manager.add_book("1984", "George Orwell", 1949)
    await book_manager.add_book("Fahrenheit 451", "Ray Bradbury", 1953)

    result = await book_manager.find_book("Fahrenheit")

    assert len(result) == 1
    assert result[0].author == "Ray Bradbury"


async def test_find_book_is_case_insensitive(book_manager: BookManager):
    "The search is case-insensitive (icontains)."
    await book_manager.add_book("1984", "George Orwell", 1949)

    result = await book_manager.find_book("orwell")
    assert len(result) == 1


async def test_find_book_returns_empty_when_no_match(book_manager: BookManager):
    "A search with no matches returns an empty list, not an exception."
    await book_manager.add_book("1984", "George Orwell", 1949)

    result = await book_manager.find_book("Texto Inexistente")
    assert result == []


@pytest.mark.parametrize("query", ["", "   "])
async def test_find_book_returns_empty_on_blank_query(
    book_manager: BookManager, query: str
):
    "An empty query or one that only contains spaces returns an empty list without querying the database."
    await book_manager.add_book("1984", "George Orwell", 1949)

    result = await book_manager.find_book(query)
    assert result == []


# delete_book

async def test_delete_book_removes_record(book_manager: BookManager):
    "The removed book no longer appears in the collection."
    await book_manager.add_book("1984", "George Orwell", 1949)
    books = await book_manager.get_all_books()
    book_id = books[0].id

    await book_manager.delete_book(book_id)

    remaining = await book_manager.get_all_books()
    assert remaining == []


async def test_delete_book_only_removes_target(book_manager: BookManager):
    "Deleting one book does not affect the other records."
    await book_manager.add_book("1984", "George Orwell", 1949)
    await book_manager.add_book("Fahrenheit 451", "Ray Bradbury", 1953)
    books = await book_manager.get_all_books()
    id_to_delete = books[0].id

    await book_manager.delete_book(id_to_delete)

    remaining = await book_manager.get_all_books()
    assert len(remaining) == 1
    assert remaining[0].id != id_to_delete


async def test_delete_book_raises_when_id_not_found(book_manager: BookManager):
    "Attempting to delete a non-existent ID results in a BookNotFoundError."
    with pytest.raises(BookNotFoundError, match="Book with id 999 does not exist."):
        await book_manager.delete_book(999)


# DataBaseError
async def test_get_all_books_raises_database_error_on_sqlalchemy_failure(
    book_manager: BookManager,
):
    """If SQLAlchemy fails to read, get_all_books re-throws DataBaseError."""
    from sqlalchemy.exc import SQLAlchemyError

    with patch.object(
        book_manager._session,
        "execute",
        new_callable=AsyncMock,
        side_effect=SQLAlchemyError("connection lost"),
    ):
        with pytest.raises(DataBaseError, match="An error occurred while retrieving books"):
            await book_manager.get_all_books()