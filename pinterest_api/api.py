import time
import json
import requests
import os
from typing import Dict, Optional, Any
from .logger import PinterestLogger
from .exceptions import AuthenticationError
from .mixins import (
    ValidationMixin,
    AuthMixin,
    LoginMixin,
    EmailVerificationMixin,
    BaseMixin,
    FeedsMixin,
    PinsMixin,
    CommentMixin,
    TrackingMixin,
    CreatorsMixin
)

class PinterestAPI(
    AuthMixin,  # Auth-related mixins first
    LoginMixin,
    ValidationMixin,
    EmailVerificationMixin,
    FeedsMixin,  # Feature mixins
    PinsMixin,
    CommentMixin,
    TrackingMixin,  # Tracking functionality
    CreatorsMixin,  # Creator functionality
    BaseMixin  # Base mixin last since others depend on it
):
    """
    Pinterest API client with authentication and validation.
    
    Args:
        email (str): User's email address
        password (str): User's password
        proxy (str | dict, optional): Proxy configuration. Can be either:
            - String format: "username:password@host:port"
            - Dictionary format: {'http': 'http://user:pass@host:port', 'https': 'https://user:pass@host:port'}
    """
    
    BASE_URL = "https://api.pinterest.com/v3"
    DEFAULT_HEADERS = {
        'Accept-Language': 'en-US',
        'User-Agent': 'Pinterest for Android/13.11.3 (sdk_gphone64_arm64; 12)',
        'X-Pinterest-App-Type-Detailed': '3',
        'X-Pinterest-Device': 'sdk_gphone64_arm64',
        'X-Pinterest-Device-Manufacturer': 'Google',
        'X-Pinterest-Appstate': 'active',
        'X-Node-Id': 'true',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept-Encoding': 'gzip, deflate',
        'Host': 'api.pinterest.com'
    }

    def __init__(self, email: str, password: str, proxy: Optional[str | Dict[str, str]] = None):
        """Initialize the Pinterest API client.
        
        Args:
            email (str): User's email address
            password (str): User's password
            proxy (str | dict, optional): Proxy configuration. Can be either:
                - String format: "username:password@host:port"
                - Dictionary format: {'http': 'http://user:pass@host:port', 'https': 'https://user:pass@host:port'}
        """
        # Initialize base functionality
        super().__init__()
        
        # Set up logger
        self.logger = PinterestLogger(email)
        self.logger.info("Initializing Pinterest API client", email=email)
        
        # Validate inputs
        self.validate_email(email)
        self.validate_password(password)
        
        self.email = email
        self.password = password
        self.proxy = self._parse_proxy(proxy) if proxy else None
        
        # Initialize session with proxy if provided
        self.session = self._create_session()
        if self.proxy:
            self.logger.info("Using proxy configuration", proxy=str(self.proxy))

    def _parse_proxy(self, proxy: str | Dict[str, str]) -> Dict[str, str]:
        """Parse proxy configuration from string or dict format.
        
        Args:
            proxy: Can be either:
                - String format: "username:password@host:port"
                - Dictionary format: {'http': 'http://user:pass@host:port', 'https': 'https://user:pass@host:port'}
        
        Returns:
            dict: Proxy configuration in requests format {'http': '...', 'https': '...'}
        """
        self.logger.debug("Parsing proxy configuration", proxy=str(proxy))
        
        if isinstance(proxy, dict):
            return proxy
            
        # Parse string format
        if isinstance(proxy, str):
            # If already in URL format with http:// or https://, return as is in dict
            if proxy.startswith(('http://', 'https://')):
                proxy_dict = {
                    'http': proxy if proxy.startswith('http://') else f'http://{proxy.replace("https://", "")}',
                    'https': proxy if proxy.startswith('https://') else f'https://{proxy.replace("http://", "")}'
                }
            else:
                # Convert basic auth format (user:pass@host:port) to URL format
                proxy_url = f'http://{proxy}'
                proxy_dict = {
                    'http': proxy_url,
                    'https': f'https://{proxy.replace("http://", "")}'
                }
            
            self.logger.debug("Proxy configuration parsed successfully", proxy_dict=str(proxy_dict))
            return proxy_dict
            
        raise ValueError("Proxy must be either a string in format 'user:pass@host:port' or a dict with 'http'/'https' keys")

    def _create_session(self) -> requests.Session:
        """Create a new session with default headers and proxy configuration.
        
        Returns:
            requests.Session: Configured session object
        """
        self.logger.debug("Creating new requests session")
        session = requests.Session()
        session.headers.update(self.DEFAULT_HEADERS)
        
        if self.proxy:
            self.logger.debug("Adding proxy configuration to session")
            session.proxies.update(self.proxy)
        
        return session

    def get_session(self) -> requests.Session:
        """Get the current session object.
        
        Returns:
            requests.Session: Current session object
        """
        return self.session

    def load_session(self, session: requests.Session):
        """Load an existing session.
        
        Args:
            session (requests.Session): Session object to load
        """
        self.session = session
        # Ensure default headers are present
        self.session.headers.update(self.DEFAULT_HEADERS)

    def save_session(self, file_path: str) -> None:
        """Save the current Pinterest session data to a file.
        
        Args:
            file_path (str): Path where to save the session data
        """
        if not self._access_token or not self._user_data:
            raise Exception("No active session to save. Please login first.")
            
        session_data = {
            'access_token': self._access_token,
            'user_data': self._user_data,
            'timestamp': time.time()
        }
        
        with open(file_path, 'w') as f:
            json.dump(session_data, f)

    def get_account_session(self) -> Dict[str, Any]:
        """Get the current Pinterest account session data.
        
        Returns:
            dict: Dictionary containing the current session data
        """
        if not self._access_token or not self._user_data:
            raise Exception("No active session. Please login first.")
            
        return {
            'access_token': self._access_token,
            'user_data': self._user_data
        }

    def _get_username(self) -> str:
        """Get username from user_data if available."""
        if hasattr(self, '_user_data') and self._user_data:
            return self._user_data.get('full_name', 'unknown')
        return 'unknown'

    def get_or_create_session(self, session_file: Optional[str] = None) -> Dict[str, Any]:
        """Get an existing session or create a new one.
        
        This method provides a complete session workflow:
        1. If session_file is provided and exists, tries to load it
        2. Validates the loaded session by fetching feeds
        3. If validation fails, removes invalid session file and raises AuthenticationError
        4. If no session_file, loading fails, or session is invalid, performs login
        5. Saves the new session if session_file is provided
        
        Args:
            session_file (str, optional): Path to save/load the session file.
                                        If None, session won't be saved to disk.
        
        Returns:
            dict: Dictionary containing the session data with keys:
                - access_token: The Pinterest access token
                - user_data: User profile data
                
        Raises:
            AuthenticationError: If session is invalid and needs to be recreated
        """
        # Try to load existing session if file is provided
        if session_file and os.path.exists(session_file):
            try:
                self.logger.info("Attempting to load existing session", session_file=session_file)
                with open(session_file, 'r') as f:
                    saved_session = json.load(f)
                
                self._access_token = saved_session['access_token']
                self._user_data = saved_session['user_data']
                username = self._get_username()
                
                # Validate session by trying to fetch feeds
                try:
                    self.logger.info("Validating session", username=username)
                    self.get_home_feed()
                    self.logger.info("Session validated successfully", username=username)
                    return self.get_account_session()
                except (AuthenticationError, requests.exceptions.RequestException) as e:
                    self.logger.warning("Session validation failed, removing invalid session", username=username, error=str(e))
                    try:
                        os.remove(session_file)
                        self.logger.info("Removed invalid session file", file=session_file, username=username)
                    except OSError as e:
                        self.logger.error("Failed to remove invalid session file", error=e, username=username)
                    
                    self._access_token = None
                    self._user_data = None
                    raise AuthenticationError("Session invalid, needs recreation")
                    
            except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
                self.logger.warning("Failed to load session, will create new one", error=str(e))
        
        # Perform login flow
        self.logger.info("Starting new login flow", email=self.email)
        self.check_email_exists()
        self.login()
        session_data = self.get_account_session()
        username = self._get_username()
        
        # Save new session if file path is provided
        if session_file:
            self.logger.info("Saving new session", session_file=session_file, username=username)
            # Ensure directory exists
            os.makedirs(os.path.dirname(session_file), exist_ok=True)
            self.save_session(session_file)
        
        return session_data

