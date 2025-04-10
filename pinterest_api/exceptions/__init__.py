from .auth import (
    PinterestAuthError,
    EmailNotFoundError,
    LoginFailedError,
    InvalidResponseError,
    IncorrectPasswordError,
    AuthenticationError
)

class PinterestError(Exception):
    """Base exception for Pinterest API errors."""
    pass

class AuthenticationError(PinterestError):
    """Raised when authentication fails or session is invalid."""
    pass

class InvalidResponseError(PinterestError):
    """Raised when response from Pinterest API is invalid."""
    pass

class PinterestAuthError(PinterestError):
    """Raised when Pinterest authentication fails."""
    pass

class EmailNotFoundError(PinterestError):
    """Raised when email is not found."""
    pass

class LoginFailedError(PinterestError):
    """Raised when login fails."""
    pass

class IncorrectPasswordError(PinterestError):
    """Raised when password is incorrect."""
    pass

__all__ = [
    'PinterestAuthError',
    'EmailNotFoundError',
    'LoginFailedError',
    'InvalidResponseError',
    'IncorrectPasswordError',
    'AuthenticationError'
] 