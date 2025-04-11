import time
import requests
import json
from typing import Dict, Optional, Any, Union
from ..exceptions import (
    AuthenticationError,
    InvalidResponseError,
    LoginFailedError,
    PasswordResetedError
)
from colorama import Fore, Style

class BaseMixin:
    BASE_URL = "https://api.pinterest.com/v3"
    DEFAULT_HEADERS = {
        'Accept-Language': 'en-US',
        'User-Agent': 'Pinterest for Android/13.12.4 (sdk_gphone64_arm64; 12)',
        'X-Pinterest-App-Type-Detailed': '3',
        'X-Pinterest-Device': 'sdk_gphone64_arm64',
        'X-Pinterest-Device-Hardwareid': '66097399e0a69560',
        'X-Pinterest-Device-Manufacturer': 'Google',
        'X-Pinterest-Installid': '68e6437e05c84e57b9cf0833d28dd1c',
        'X-Pinterest-Appstate': 'active',
        'X-Node-Id': 'true',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept-Encoding': 'gzip, deflate, br',
        'Host': 'api.pinterest.com'
    }

    def __init__(self):
        """Initialize base functionality."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Pinterest for Android/13.12.4 ({device}; 12)',
            'X-Pinterest-App-Type-Detailed': '3',
            'X-Pinterest-Device': '{device}',
            'X-Pinterest-Device-Hardwareid': '{hardware_id}',
            'X-Pinterest-Device-Manufacturer': '{manufacturer}',
            'X-Pinterest-Installid': '{install_id}'
        })
        # Note: Logger will be initialized by PinterestAPI class

    def _get_timestamp(self) -> str:
        """Get current timestamp in the required format."""
        return str(int(time.time() + 100000))

    def _handle_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        require_auth: bool = True
    ) -> Dict[str, Any]:
        """Handle API request with authentication and error handling.
        
        Args:
            method (str): HTTP method (GET, POST, etc.)
            endpoint (str): API endpoint path
            data (dict, optional): Request body data
            params (dict, optional): URL parameters
            headers (dict, optional): Additional headers
            require_auth (bool): Whether this request requires authentication
            
        Returns:
            dict: Response data
            
        Raises:
            AuthenticationError: If authentication is required but not available
        """
        try:
            # Make the request
            response = self.session.request(
                method=method,
                url=f"{self.BASE_URL}{endpoint}",
                data=data,
                params=params,
                headers=headers
            )
            
            # Log response for debugging
            if hasattr(self, 'logger'):
                self.logger.log_response(response)
            
            # Try to parse response as JSON
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = response.text
            
            # Check for error codes in response
            if isinstance(response_data, dict):
                if response_data.get('status') == 'failure':
                    error_code = response_data.get('code')
                    error_msg = response_data.get('message', 'Unknown error')
                    
                    # Handle specific error codes
                    if error_code == 88:
                        raise PasswordResetedError(error_msg)
                    elif error_code in (401, 403):
                        raise AuthenticationError(error_msg)
                    else:
                        raise LoginFailedError(error_msg)
            
            # Handle HTTP error status codes
            if response.status_code >= 400:
                if response.status_code in (401, 403):
                    raise AuthenticationError(f"Authentication failed: {response.status_code}")
                else:
                    response.raise_for_status()
            
            return response_data
            
        except requests.exceptions.RequestException as e:
            # Handle token expiration or other auth errors
            if hasattr(e, 'response') and e.response and e.response.status_code in (401, 403):
                print(f"{Fore.RED}❌ Authentication error: {str(e)}{Style.RESET_ALL}")
                print(f"{Fore.RED}❌ Response status: {e.response.status_code}{Style.RESET_ALL}")
                print(f"{Fore.RED}❌ Response headers: {json.dumps(dict(e.response.headers), indent=2)}{Style.RESET_ALL}")
                try:
                    error_data = e.response.json()
                    print(f"{Fore.RED}❌ Error data: {json.dumps(error_data, indent=2)}{Style.RESET_ALL}")
                    
                    # Check for password reset error code
                    if isinstance(error_data, dict) and error_data.get('code') == 88:
                        raise PasswordResetedError(error_data.get('message', 'Password reset required'))
                except:
                    print(f"{Fore.RED}❌ Error text: {e.response.text[:1000]}{Style.RESET_ALL}")
                
                self._access_token = None
                raise AuthenticationError("Session expired or invalid. Please login again.")
            raise e

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Dict[str, Any] = None,
        data: Dict[str, Any] = None,
        headers: Optional[Dict[str, str]] = None,
        retry_count: int = 0,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """Make a request to the Pinterest API with automatic session refresh handling.
        
        Args:
            method (str): HTTP method (GET, POST, etc.)
            endpoint (str): API endpoint
            params (Dict[str, Any], optional): Query parameters
            data (Dict[str, Any], optional): Request body data
            headers (Dict[str, str], optional): Additional headers to include
            retry_count (int): Current retry attempt (used internally)
            max_retries (int): Maximum number of retry attempts
            
        Returns:
            Dict[str, Any]: Response data
            
        Raises:
            LoginFailedError: If authentication fails after max retries
            requests.exceptions.RequestException: For other request errors
        """
        if not hasattr(self, 'get_access_token'):
            self.logger.error("Login mixin not properly initialized")
            raise LoginFailedError("Login mixin not properly initialized")

        try:
            access_token = self.get_access_token()
            request_headers = self.DEFAULT_HEADERS.copy()
            request_headers['Authorization'] = f'Bearer {access_token}'
            
            # Update headers if additional ones provided
            if headers:
                request_headers.update(headers)

            # Log request details with data
            self.logger.debug(
                "Making API request",
                extra={
                    'context': {
                        'method': method,
                        'endpoint': endpoint,
                        'params': self._truncate_data(params) if params else None,
                        'data': self._truncate_data(data) if data else None,
                        'headers': {k: v for k, v in request_headers.items() if k != 'Authorization'},  # Don't log auth token
                        'retry_count': retry_count
                    }
                }
            )

            response = requests.request(
                method=method,
                url=f"{self.BASE_URL}{endpoint}",
                headers=request_headers,
                params=params,
                data=data
            )

            # Try to parse response data
            try:
                response_data = response.json() if response.content else None
            except ValueError:
                response_data = response.text if response.content else None

            # Log response status and data
            self.logger.debug(
                "Received API response",
                extra={
                    'context': {
                        'status_code': response.status_code,
                        'endpoint': endpoint,
                        'content_length': len(response.content) if response.content else 0,
                        'response_headers': dict(response.headers),
                        'response_data': self._truncate_data(response_data) if response_data else None
                    }
                }
            )

            # Check for session expiration
            if response.status_code == 401:
                if retry_count < max_retries:
                    self.logger.warning(
                        "Session expired, attempting refresh",
                        extra={
                            'context': {
                                'attempt': retry_count + 1,
                                'max_retries': max_retries
                            }
                        }
                    )
                    # Try to refresh the session
                    if hasattr(self, 'refresh_session'):
                        self.refresh_session()
                        time.sleep(1)  # Small delay after refresh
                        return self._make_request(
                            method=method,
                            endpoint=endpoint,
                            params=params,
                            data=data,
                            headers=headers,  # Pass headers through on retry
                            retry_count=retry_count + 1,
                            max_retries=max_retries
                        )
                self.logger.error(
                    "Authentication failed after max retries",
                    extra={
                        'context': {
                            'max_retries': max_retries
                        }
                    }
                )
                raise LoginFailedError("Authentication failed and max retries reached")

            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('retry-after', 60))
                self.logger.warning(
                    "Rate limited by API",
                    extra={
                        'context': {
                            'retry_after': retry_after,
                            'attempt': retry_count + 1
                        }
                    }
                )
                time.sleep(retry_after)
                return self._make_request(
                    method=method,
                    endpoint=endpoint,
                    params=params,
                    data=data,
                    headers=headers,  # Pass headers through on retry
                    retry_count=retry_count,
                    max_retries=max_retries
                )

            # Special handling for 403 on comment endpoints
            if response.status_code == 403 and '/comments/' in endpoint:
                self.logger.info(
                    "Comments are disabled for this pin",
                    extra={
                        'context': {
                            'endpoint': endpoint,
                            'pin_id': endpoint.split('/')[2] if len(endpoint.split('/')) > 2 else None,
                            'response_data': self._truncate_data(response_data) if response_data else None
                        }
                    }
                )
                return {'success': False, 'reason': 'comments_disabled', 'response': response_data}

            # Raise for other error status codes
            response.raise_for_status()

            # Log successful response
            self.logger.info(
                "API request successful",
                extra={
                    'context': {
                        'endpoint': endpoint,
                        'method': method,
                        'response_data': self._truncate_data(response_data) if response_data else None
                    }
                }
            )

            return response.json()

        except requests.exceptions.RequestException as e:
            if retry_count < max_retries and (
                getattr(e.response, 'status_code', None) in [401, 429]
            ):
                # Already handled above
                raise
                
            # Special handling for 403 on comment endpoints
            if (
                hasattr(e.response, 'status_code') and 
                e.response.status_code == 403 and 
                '/comments/' in endpoint
            ):
                self.logger.info(
                    "Comments are disabled for this pin",
                    extra={
                        'context': {
                            'endpoint': endpoint,
                            'pin_id': endpoint.split('/')[2] if len(endpoint.split('/')) > 2 else None,
                            'response_data': self._truncate_data(response_data) if response_data else None
                        }
                    }
                )
                return {'success': False, 'reason': 'comments_disabled', 'response': response_data}
                
            self.logger.error(
                "API request failed",
                extra={
                    'context': {
                        'error': str(e),
                        'endpoint': endpoint,
                        'method': method,
                        'response_status': getattr(e.response, 'status_code', None),
                        'response_text': getattr(e.response, 'text', '')[:1000] if hasattr(e.response, 'text') else None
                    }
                }
            )
            raise

    def _truncate_data(self, data: Any, max_length: int = 1000) -> Any:
        """Truncate data for logging to prevent excessive log sizes.
        
        Args:
            data: Data to truncate
            max_length: Maximum length for string values
            
        Returns:
            Truncated data
        """
        if isinstance(data, dict):
            return {k: self._truncate_data(v, max_length) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._truncate_data(item, max_length) for item in data[:10]]  # Only show first 10 items
        elif isinstance(data, str) and len(data) > max_length:
            return data[:max_length] + '...'
        return data

    def login(self):
        """Placeholder for login method that should be implemented by LoginMixin."""
        raise NotImplementedError("Login method must be implemented by LoginMixin")

    def set_device_info(self, device_info: Dict[str, str]) -> None:
        """
        Set device information for the session headers.
        
        Args:
            device_info (Dict[str, str]): Dictionary containing device information
        """
        device = device_info.get('device', 'sdk_gphone64_arm64')
        hardware_id = device_info.get('hardware_id', '66097399e0a69560')
        manufacturer = device_info.get('manufacturer', 'Google')
        install_id = device_info.get('install_id', '68e6437e05c84e57b9cf0833d28dd1c')
        
        self.session.headers.update({
            'User-Agent': f'Pinterest for Android/13.12.4 ({device}; 12)',
            'X-Pinterest-Device': device,
            'X-Pinterest-Device-Hardwareid': hardware_id,
            'X-Pinterest-Device-Manufacturer': manufacturer,
            'X-Pinterest-Installid': install_id
        }) 