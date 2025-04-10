from typing import Dict, Any
import requests
from ..exceptions import EmailNotFoundError, InvalidResponseError

class EmailVerificationMixin:
    def check_email_exists(self) -> bool:
        """
        Check if the email exists in Pinterest.
        
        Returns:
            bool: True if email exists, raises exception otherwise.
            
        Raises:
            EmailNotFoundError: If email is not found
            InvalidResponseError: If response format is invalid
            requests.exceptions.RequestException: For network/API errors
        """
        timestamp = self._get_timestamp()
        
        params = {
            'email': self.email,
            'view_type': '14',
            'view_parameter': '163',
            'client_id': self.CLIENT_ID,
            'timestamp': timestamp
        }
        
        # Build URL for signature generation
        url = f"{self.BASE_URL}/register/exists/?{'&'.join(f'{k}={v}' for k, v in params.items())}"
        signature, _ = self.generate_email_check_signature("GET", url)
        params['oauth_signature'] = signature
        
        data = self._handle_request(
            method="GET",
            endpoint="/register/exists/",
            params=params,
            require_auth=False
        )
        
        # Validate response format
        if not isinstance(data, dict) or 'status' not in data or 'data' not in data:
            raise InvalidResponseError(data)
            
        if data['status'] != 'success':
            raise InvalidResponseError(data)
            
        if not data['data']:
            raise EmailNotFoundError(self.email)
            
        return True 