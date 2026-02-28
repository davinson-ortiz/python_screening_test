class BookManagerError(Exception):
    """Base class for exceptions in the Book Manager."""
    pass

class ValidationError(BookManagerError):
    """Exception raised for validation errors."""
    pass

class DataBaseError(BookManagerError):
    """Exception raised for database errors."""
    pass

class BookNotFoundError(BookManagerError):
    """Exception raised when a book is not found."""
    pass