class PinterestAuthError(Exception):
    """Base class for Pinterest authentication errors."""
    pass

class AuthenticationError(PinterestAuthError):
    """Raised when authentication is required but not available or token is invalid."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class EmailNotFoundError(PinterestAuthError):
    """Raised when the email is not found during verification."""
    def __init__(self, email: str):
        self.email = email
        self.message = f"Email not found: {email}"
        super().__init__(self.message)

class IncorrectPasswordError(PinterestAuthError):
    """Raised when the password is incorrect."""
    def __init__(self):
        self.message = "The password you entered is incorrect"
        super().__init__(self.message)

class LoginFailedError(PinterestAuthError):
    """Raised when login attempt fails."""
    def __init__(self, message: str = None):
        self.message = message or "Login failed"
        super().__init__(self.message)

class InvalidResponseError(PinterestAuthError):
    """Raised when the API response is not in the expected format."""
    def __init__(self, response: dict):
        self.response = response
        self.message = f"Invalid API response format: {response}"
        super().__init__(self.message)

class PasswordResetedError(PinterestAuthError):
    """Raised when Pinterest has reset the account's password for security reasons."""
    def __init__(self, message: str = None):
        self.message = message or "Your password has been reset by Pinterest for security reasons. Please reset your password to regain access to your account."
        super().__init__(self.message) 