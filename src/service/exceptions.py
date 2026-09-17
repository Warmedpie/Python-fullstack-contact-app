class ValidationError(Exception):
    """Raised when caller-supplied input fails a business rule."""


class NotFoundError(Exception):
    """Raised when a requested contact or email does not exist."""
