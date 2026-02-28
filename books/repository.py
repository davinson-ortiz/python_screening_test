from sqlalchemy.ext.asyncio import AsyncSession
from .models import Book
from datetime import datetime
from .exceptions import ValidationError, DataBaseError, BookNotFoundError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, or_
from typing import Sequence


class BookManager:
    def __init__(self, session: AsyncSession):
        """Initializes the BookManager with dependency injection of the database session."""
        self._session = session

    async def add_book(self, title: str, author: str, year: int) -> None:
        """Adds a new book to the database."""
        # Only validate domain-specific rules here
        current_year = datetime.now().year
        if year < 0 or year > current_year:
            raise ValidationError(f"Year must be between 0 and {current_year}.")

        try:
            async with self._session.begin_nested():
                new_book = Book(title=title.strip(), author=author.strip(), year=year)
                self._session.add(new_book)
            await self._session.commit()
        except SQLAlchemyError as e:
            await self._session.rollback()
            raise DataBaseError(f"An error occurred while adding the book: {str(e)}")

    async def get_all_books(self) -> Sequence[Book]:
        """Retrieves all books from the database."""
        try:
            result = await self._session.execute(select(Book))
            return result.scalars().all()
        except SQLAlchemyError as e:
            raise DataBaseError(f"An error occurred while retrieving books: {str(e)}")  


    async def find_book(self, query: str) -> Sequence[Book]:
        """Finds books by title or author."""
        if not query or not query.strip():
            return []  # Return empty list for empty or whitespace-only queries
        
        try:
            stmt = select(Book).where(
                or_(
                    Book.title.icontains(query.strip()),
                    Book.author.icontains(query.strip()),
                )
            )

            result = await self._session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            raise DataBaseError(f"An error occurred while searching for books: {str(e)}")


    async def delete_book(self, book_id: int) -> None:
        """Deletes a book from the database."""
        try:
            book = await self._session.get(Book, book_id)
            if not book:
                raise BookNotFoundError(f"Book with id {book_id} does not exist.")

            async with self._session.begin_nested():
                await self._session.delete(book)
            await self._session.commit()
        except BookNotFoundError:
            raise
        except SQLAlchemyError as e:
            await self._session.rollback()
            raise DataBaseError(f"An error occurred while deleting the book: {str(e)}")