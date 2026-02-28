from typing import Protocol, Sequence
from .models import Book

class IBookRepository(Protocol):
    """Interface for book repository"""
    async def add_book(self, title: str, author: str) -> None:
        ...

    async def get_all_books(self) -> Sequence[Book]:
        ...

    async def find_book(self, query: str) -> Sequence[Book]:
        ...

    async def delete_book(self, book_id: int) -> None:
        ...
