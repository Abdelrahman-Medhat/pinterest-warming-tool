import re
from typing import Optional

class ValidationMixin:
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        if not isinstance(email, str):
            raise TypeError("Email must be a string")
            
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValueError("Invalid email format")
        return True

    @staticmethod
    def validate_password(password: str) -> bool:
        """Validate password requirements."""
        if not isinstance(password, str):
            raise TypeError("Password must be a string")
            
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
            
        return True 