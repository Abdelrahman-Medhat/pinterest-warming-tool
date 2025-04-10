from typing import Dict, Any, Optional, Literal
import requests
from urllib.parse import quote, urlparse
import json
import time
import struct
import uuid
from requests_toolbelt import MultipartEncoder
from .base import BaseMixin


class TrackingMixin(BaseMixin):
    """Mixin for Pinterest tracking-related functionality."""
    
    WARM_ENDPOINTS = {
        'pinimg': "https://i.pinimg.com/_/_/warm/",
        'api': "https://api.pinterest.com/_/_/warm/"
    }
    
    TRACKING_BASE_URL = "https://trk.pinterest.com/v3"
    CLIENT_ID = "1431602"  # Pinterest Android app client ID
    
    def __init__(self):
        """Initialize tracking functionality."""
        super().__init__()
        
    def warm_request(self, endpoint: Literal['pinimg', 'api'] = 'pinimg') -> Dict[str, Any]:
        """Send a warm request to Pinterest's tracking endpoint.
        
        This request is typically used for tracking and analytics purposes.
        
        Args:
            endpoint (Literal['pinimg', 'api']): Which endpoint to use for the warm request.
                'pinimg' uses i.pinimg.com
                'api' uses api.pinterest.com
        
        Returns:
            Dict[str, Any]: Response data or empty dict if no content
            
        Raises:
            requests.exceptions.RequestException: If the request fails
            ValueError: If an invalid endpoint is specified
        """
        if endpoint not in self.WARM_ENDPOINTS:
            raise ValueError(f"Invalid endpoint '{endpoint}'. Must be one of: {list(self.WARM_ENDPOINTS.keys())}")
            
        url = self.WARM_ENDPOINTS[endpoint]
        host = 'i.pinimg.com' if endpoint == 'pinimg' else 'api.pinterest.com'
        
        headers = {
            'Host': host,
            'Cache-Control': 'no-cache',
            'Accept-Encoding': 'gzip, deflate, br',
            'User-Agent': 'okhttp/4.12.0',
            'Connection': 'keep-alive'
        }
        
        try:
            response = requests.head(
                url=url,
                headers=headers,
                allow_redirects=False
            )
            
            self.logger.debug(
                "Sent warm request",
                extra={
                    'context': {
                        'endpoint': endpoint,
                        'url': url,
                        'status_code': response.status_code,
                        'headers': dict(response.headers)
                    }
                }
            )
            
            return {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'endpoint_used': endpoint
            }
            
        except requests.exceptions.RequestException as e:
            self.logger.error(
                "Warm request failed",
                extra={
                    'context': {
                        'endpoint': endpoint,
                        'url': url,
                        'error': str(e)
                    }
                }
            )
            raise

    def track_offsite_view(
        self,
        url: str,
        pin_id: str,
        check_only: bool = True,
        clickthrough_source: str = 'closeup',
        view_type: int = 3,
        view_parameter: int = 140
    ) -> Dict[str, Any]:
        """Track an offsite view of a Pinterest resource (image, pin, etc.).
        
        Args:
            url (str): The URL of the resource being viewed (will be URL encoded)
            pin_id (str): The Pinterest pin ID associated with the view
            check_only (bool, optional): Whether this is just a check. Defaults to True.
            clickthrough_source (str, optional): Source of the click. Defaults to 'closeup'.
            view_type (int, optional): Type of view. Defaults to 3.
            view_parameter (int, optional): Additional view parameter. Defaults to 140.
            
        Returns:
            Dict[str, Any]: Response data including status and headers
            
        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        # URL encode the resource URL
        encoded_url = quote(url, safe='')
        
        # Construct the tracking URL with parameters
        tracking_url = f"{self.BASE_URL}/offsite/"
        params = {
            'url': encoded_url,
            'pin_id': pin_id,
            'check_only': '1' if check_only else '0',
            'clickthrough_source': clickthrough_source,
            'view_type': str(view_type),
            'view_parameter': str(view_parameter)
        }
        
        # Standard headers for Pinterest API requests
        headers = {
            'Host': 'api.pinterest.com',
            'Accept-Language': 'en-US',
            'User-Agent': 'Pinterest for Android/13.12.4 (sdk_gphone64_arm64; 12)',
            'X-Pinterest-App-Type-Detailed': '3',
            'X-Pinterest-Device': 'sdk_gphone64_arm64',
            'X-Pinterest-Device-Hardwareid': self.session.headers.get('X-Pinterest-Device-Hardwareid', ''),
            'X-Pinterest-Device-Manufacturer': 'Google',
            'X-Pinterest-Installid': self.session.headers.get('X-Pinterest-Installid', ''),
            'X-Pinterest-Appstate': 'active',
            'X-Node-Id': 'true',
            'Accept-Encoding': 'gzip, deflate, br'
        }
        
        try:
            response = self.session.get(
                url=tracking_url,
                params=params,
                headers=headers
            )
            
            self.logger.debug(
                "Sent offsite tracking request",
                extra={
                    'context': {
                        'url': tracking_url,
                        'params': params,
                        'status_code': response.status_code,
                        'headers': dict(response.headers)
                    }
                }
            )
            
            return {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'response_data': response.json() if response.content else None
            }
            
        except requests.exceptions.RequestException as e:
            self.logger.error(
                "Offsite tracking request failed",
                extra={
                    'context': {
                        'url': tracking_url,
                        'params': params,
                        'error': str(e)
                    }
                }
            )
            raise

    def track_action(
        self,
        action_type: str,
        platform: str = 'android',
        app_version: str = '13.12',
        os_version: str = '12',
        device: str = 'sdk_gphone64_arm64',
        manufacturer: str = 'Google',
        client_id: Optional[str] = None,
        additional_tags: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Track an app action event.
        
        This method supports different types of action tracking. Here are the main use cases:

        1. App Start Tracking:
        ```
        # Example request:
        POST /v3/register/track_action/android.app_start.cold/ HTTP/2
        aux_data={
            "tags": {
                "app_version": "13.12",
                "device": "sdk_gphone64_arm64",
                "platform": "android",
                "manufacturer": "Google",
                "os_version": "12"
            }
        }
        
        # Usage:
        track_action(
            action_type='app_start.cold',
            app_version='13.12',
            device='sdk_gphone64_arm64',
            os_version='12'
        )
        ```

        2. Facebook Installation Check:
        ```
        # Example request:
        POST /v3/register/track_action/facebook_installed/ HTTP/2
        aux_data={
            "tags": {
                "app": "ANDROID_MOBILE",
                "installed": "false",
                "app_version": "13128040"
            }
        }
        
        # Usage:
        track_action(
            action_type='facebook_installed',
            additional_tags={
                "app": "ANDROID_MOBILE",
                "installed": "false",
                "app_version": "13128040"
            }
        )
        ```
        
        Args:
            action_type (str): The type of action (e.g. 'app_start.cold', 'facebook_installed')
            platform (str, optional): Platform identifier. Defaults to 'android'.
            app_version (str, optional): App version. Defaults to '13.12'.
            os_version (str, optional): OS version. Defaults to '12'.
            device (str, optional): Device identifier. Defaults to 'sdk_gphone64_arm64'.
            manufacturer (str, optional): Device manufacturer. Defaults to 'Google'.
            client_id (str, optional): Client ID. Defaults to class CLIENT_ID.
            additional_tags (Dict[str, str], optional): Additional tags to include in aux_data.
                Use this to override default tags or add custom ones for specific tracking cases.
            
        Returns:
            Dict[str, Any]: Response data including status and headers
            
        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        # Prepare the aux_data with tags
        tags = {
            "app_version": app_version,
            "device": device,
            "platform": platform,
            "manufacturer": manufacturer,
            "os_version": os_version
        }
        
        # Add any additional tags
        if additional_tags:
            tags.update(additional_tags)
            
        aux_data = {
            "tags": tags
        }
        
        # URL parameters
        params = {
            'aux_data': json.dumps(aux_data),
            'client_id': client_id or self.CLIENT_ID,
            'timestamp': str(int(time.time() + 100000)),  # Match the timestamp format from the example
        }
        
        # Construct the tracking URL
        tracking_url = f"{self.TRACKING_BASE_URL}/register/track_action/{platform}.{action_type}/"
        
        # Headers specific to tracking requests
        headers = {
            'Host': 'trk.pinterest.com',
            'Accept-Language': 'en-US',
            'User-Agent': 'Pinterest for Android/13.12.4 (sdk_gphone64_arm64; 12)',
            'X-Pinterest-App-Type-Detailed': '3',
            'X-Pinterest-Device': device,
            'X-Pinterest-Device-Hardwareid': self.session.headers.get('X-Pinterest-Device-Hardwareid', ''),
            'X-Pinterest-Device-Manufacturer': manufacturer,
            'X-Pinterest-Installid': self.session.headers.get('X-Pinterest-Installid', ''),
            'X-Pinterest-Appstate': 'active',
            'X-Node-Id': 'true',
            'Content-Type': 'application/octet-stream',
            'Content-Encoding': 'gzip',
            'Accept-Encoding': 'gzip, deflate, br',
            'Priority': 'u=1, i'
        }
        
        try:
            # Send POST request with empty gzipped content as in the example
            response = self.session.post(
                url=tracking_url,
                params=params,
                headers=headers,
                data=b'\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\x03\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00'  # Empty gzipped content
            )
            
            self.logger.debug(
                "Sent action tracking request",
                extra={
                    'context': {
                        'action_type': action_type,
                        'url': tracking_url,
                        'params': params,
                        'status_code': response.status_code,
                        'headers': dict(response.headers)
                    }
                }
            )
            
            return {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'response_data': response.json() if response.content else None
            }
            
        except requests.exceptions.RequestException as e:
            self.logger.error(
                "Action tracking request failed",
                extra={
                    'context': {
                        'action_type': action_type,
                        'url': tracking_url,
                        'params': params,
                        'error': str(e)
                    }
                }
            )
            raise

    def track_custom_event(
        self,
        event_name: str,
        event_data: Dict[str, Any],
        user_id: Optional[str] = None,
        app_version: str = '13.12',
        os_version: str = '12',
        device_model: str = 'sdk_gphone64_arm64',
        country: str = 'United States (US)',
        client_id: Optional[str] = None,
        auth_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Track a custom event using the log endpoint.
        
        Args:
            event_name (str): Name of the custom event (e.g. 'InAppBrowser')
            event_data (Dict[str, Any]): Custom event data to include in the payload
            user_id (str, optional): Pinterest user ID
            app_version (str, optional): App version. Defaults to '13.12'
            os_version (str, optional): OS version. Defaults to '12'
            device_model (str, optional): Device model. Defaults to 'sdk_gphone64_arm64'
            country (str, optional): User's country. Defaults to 'United States (US)'
            client_id (str, optional): Client ID. Defaults to class CLIENT_ID
            auth_token (str, optional): Authorization token for the request
            
        Returns:
            Dict[str, Any]: Response data including status and headers
            
        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        # Base URL and parameters
        base_url = "https://trk.pinterest.com/log/"
        current_timestamp = str(int(time.time()))
        
        # Request parameters
        params = {
            "client_id": client_id or self.CLIENT_ID,
            "timestamp": current_timestamp
        }
        
        # Generate signature
        method = "POST"
        url_with_params = f"{base_url}?client_id={params['client_id']}&timestamp={params['timestamp']}"
        signature, _ = self.generate_login_signature(method, url_with_params)
        params["oauth_signature"] = signature
        
        # Final URL
        final_url = f"{base_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
        
        # Prepare headers
        boundary = "29bd6bd5-3ac0-4520-aa58-6124efe576bf"
        headers = {
            "Accept-Language": "en-US",
            "User-Agent": f"Pinterest for Android/{app_version} ({device_model}; {os_version})",
            "X-Pinterest-App-Type-Detailed": "3",
            "X-Pinterest-Device": device_model,
            "X-Pinterest-Device-Hardwareid": self.session.headers.get('X-Pinterest-Device-Hardwareid', '66097399e0a69560'),
            "X-Pinterest-Device-Manufacturer": "Google",
            "X-Pinterest-Installid": self.session.headers.get('X-Pinterest-Installid', '68e6437e05c84e57b9cf0833d28dd1c'),
            "X-Pinterest-Appstate": "active",
            "X-Node-Id": "true",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Accept-Encoding": "gzip, deflate, br",
            "Priority": "u=1, i"
        }
        
        # Add authorization if provided
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        
        # Prepare event data
        event_timestamp = str(int(time.time() * 1000))
        log_data = {
            "logs": [{
                "metadata": {
                    "app_version": app_version,
                    "build_type": "Production",
                    "country": country,
                    "device_model": device_model,
                    "os_version": os_version,
                    "platform": "Android",
                    "user_id": user_id
                },
                "name": "android_custom_event",
                "payload": {
                    "event_data": event_data,
                    "event_name": event_name
                },
                "timestamp": int(event_timestamp)
            }]
        }
        
        # Construct multipart form data
        form_data = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="v0_mobile_json_log_events"; filename="null"\r\n'
            f"Content-Transfer-Encoding: 8bit\r\n"
            f"Content-Type: application/json; charset=utf-8\r\n"
            f"Content-Length: {len(str(log_data))}\r\n\r\n"
            f"{str(log_data)}\r\n"
            f"--{boundary}--\r\n"
        )
        
        try:
            # Send request
            response = requests.post(final_url, headers=headers, data=form_data)
            
            self.logger.debug(
                "Sent custom event tracking request",
                extra={
                    'context': {
                        'event_name': event_name,
                        'url': final_url,
                        'status_code': response.status_code,
                        'headers': dict(response.headers)
                    }
                }
            )
            
            return {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'response_data': response.text
            }
            
        except requests.exceptions.RequestException as e:
            self.logger.error(
                "Custom event tracking request failed",
                extra={
                    'context': {
                        'event_name': event_name,
                        'url': final_url,
                        'error': str(e)
                    }
                }
            )
            raise

    def extract_domain(self, url: str) -> str:
        """Extract domain from URL, handling various URL formats.
        
        Args:
            url (str): The URL to extract domain from
            
        Returns:
            str: The extracted domain
        """
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        # Remove www. if present
        if domain.startswith('www.'):
            domain = domain[4:]
            
        return domain
        
    def create_clickthrough_payload(self, url: str, pin_id: str, is_start: bool = True, 
                                   start_time: Optional[int] = None, 
                                   end_time: Optional[int] = None, 
                                   duration: Optional[int] = None) -> bytes:
        """Create a binary payload for clickthrough tracking.
        
        Args:
            url (str): The URL being clicked through
            pin_id (str): The Pinterest pin ID
            is_start (bool): Whether this is a start event (True) or end event (False)
            start_time (Optional[int]): Start timestamp
            end_time (Optional[int]): End timestamp
            duration (Optional[int]): Duration in seconds
            
        Returns:
            bytes: Binary payload for the tracking request
        """
        if start_time is None:
            start_time = int(time.time())
        if end_time is None and duration is not None:
            end_time = start_time + duration
            
        # Extract domain from URL
        domain = self.extract_domain(url)
        
        # Get session data
        session_id = self.session.headers.get('X-Pinterest-Installid', '')
        user_id = self.session.headers.get('X-Pinterest-User-Id', '')
        advertising_id = self.session.headers.get('X-Pinterest-Advertising-Id', '')
        
        # Create binary payload
        payload = bytearray()
        
        # Add magic bytes (0xED 0x5B)
        payload.extend(b'\xed\x5b')
        
        # Event type (1 for start, 2 for end)
        event_type = 1 if is_start else 2
        payload.extend(struct.pack('>B', event_type))
        
        # Timestamp
        payload.extend(struct.pack('>I', start_time))
        
        # Session ID
        payload.extend(struct.pack('>H', len(session_id)))
        payload.extend(session_id.encode())
        
        # User ID
        payload.extend(struct.pack('>H', len(user_id)))
        payload.extend(user_id.encode())
        
        # Pin ID
        payload.extend(struct.pack('>H', len(pin_id)))
        payload.extend(pin_id.encode())
        
        # Click type
        payload.extend(struct.pack('>H', len("click_type")))
        payload.extend("click_type".encode())
        payload.extend(struct.pack('>H', len("clickthrough")))
        payload.extend("clickthrough".encode())
        
        # Clickthrough domain
        payload.extend(struct.pack('>H', len("clickthrough_domain")))
        payload.extend("clickthrough_domain".encode())
        payload.extend(struct.pack('>H', len(domain)))
        payload.extend(domain.encode())
        
        # Final destination URL
        payload.extend(struct.pack('>H', len("final_destination_url")))
        payload.extend("final_destination_url".encode())
        payload.extend(struct.pack('>H', len(url)))
        payload.extend(url.encode())
        
        # Duration (for end event)
        if not is_start and duration is not None:
            payload.extend(struct.pack('>H', len("duration")))
            payload.extend("duration".encode())
            payload.extend(struct.pack('>I', duration))
        
        # Add commerce data
        commerce_data = {
            "item_set_id": "b735994f-8d31-4166-9c2b-28b845c07577",
            "item_id": "17640b43-6854-4965-bf34-4035cd81a5cd",
            "pin_show_pdp": "true",
            "carousel_image_count": "1",
            "is_pdpplus": "true",
            "free_shipping_price": "$0",
            "is_product_pin_v2": "true",
            "free_shipping_value": "0",
            "is_available": "true"
        }
        
        payload.extend(struct.pack('>H', len("commerce_data")))
        payload.extend("commerce_data".encode())
        payload.extend(struct.pack('>H', len(json.dumps(commerce_data))))
        payload.extend(json.dumps(commerce_data).encode())
        
        # Add is_claimed_domain
        payload.extend(struct.pack('>H', len("is_claimed_domain")))
        payload.extend("is_claimed_domain".encode())
        payload.extend(struct.pack('>H', len("false")))
        payload.extend("false".encode())
        
        # Add is_cct_enabled
        payload.extend(struct.pack('>H', len("is_cct_enabled")))
        payload.extend("is_cct_enabled".encode())
        payload.extend(struct.pack('>H', len("true")))
        payload.extend("true".encode())
        
        # Add is_go_linkless
        payload.extend(struct.pack('>H', len("is_go_linkless")))
        payload.extend("is_go_linkless".encode())
        payload.extend(struct.pack('>H', len("false")))
        payload.extend("false".encode())
        
        return bytes(payload)

    def track_clickthrough(self, url: str, pin_id: str, is_start: bool = True, duration: Optional[int] = None) -> Dict[str, Any]:
        """Track a clickthrough event for a given URL.
        
        Args:
            url (str): The URL to track clickthrough for
            pin_id (str): The Pinterest pin ID
            is_start (bool): Whether this is a start event (True) or end event (False)
            duration (Optional[int]): Duration in seconds (only used for end events)
            
        Returns:
            Dict[str, Any]: Response data
        """
        timestamp = int(time.time())
        
        # Create payload
        payload = self.create_clickthrough_payload(
            url=url,
            pin_id=pin_id,
            is_start=is_start,
            start_time=timestamp if is_start else timestamp - duration,
            end_time=None if is_start else timestamp,
            duration=duration if not is_start else None
        )
        
        # Create multipart form-data
        boundary = str(uuid.uuid4())
        encoder = MultipartEncoder(
            fields={
                'event_batch': ('null', payload, 'application/x-thrift')
            },
            boundary=boundary
        )
        
        # Headers based on the intercepted request
        headers = {
            'Content-Type': f'multipart/form-data; boundary={boundary}',
            'User-Agent': 'Pinterest for Android/13.12.4 (sdk_gphone64_arm64; 12)',
            'X-Pinterest-Advertising-Id': self.session.headers.get('X-Pinterest-Advertising-Id', ''),
            'X-Pinterest-App-Type-Detailed': '3',
            'X-Pinterest-Device': 'sdk_gphone64_arm64',
            'X-Pinterest-Device-Hardwareid': self.session.headers.get('X-Pinterest-Device-Hardwareid', ''),
            'X-Pinterest-Device-Manufacturer': 'Google',
            'X-Pinterest-Installid': self.session.headers.get('X-Pinterest-Installid', ''),
            'X-Pinterest-Appstate': 'active',
            'X-Node-Id': 'true',
            'Authorization': self.session.headers.get('Authorization', ''),
            'Accept-Language': 'en-US',
            'Accept-Encoding': 'gzip, deflate, br'
        }
        
        # Send request
        url = f"https://trk.pinterest.com/v3/callback/event/"
        params = {
            'client_id': self.CLIENT_ID,
            'timestamp': str(timestamp),
            'oauth_signature': 'dc80398b0c61649249702271c0edfe92588aa4b3ff0e6b3c2e201a9ccbc8afcc'
        }
        
        try:
            response = requests.post(
                url,
                params=params,
                data=encoder,
                headers=headers,
                verify=True
            )
            
            return {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'response_data': response.text if response.content else None
            }
            
        except Exception as e:
            self.logger.error(f"Clickthrough tracking request failed: {str(e)}")
            return {
                'status_code': 0,
                'error': str(e)
            }

    def track_experience(
        self,
        pin_id: str,
        placement_ids: list = [12],
        did_long_clickthrough: bool = False,
        did_pin_clickthrough: bool = False,
        did_repin: bool = False,
        is_own_or_group_pin: bool = False,
        login_page_type: str = "unknown",
        pin_image_signature: Optional[str] = None,
        is_creator_card_shown: bool = True,
        creator_username: Optional[str] = None,
        android_app_launch_session_id: Optional[str] = None,
        allows_notifications: str = "true",
        app_state: str = "background"
    ) -> Dict[str, Any]:
        """Track an experience event after visiting a link.
        
        This method makes a request to the Pinterest experiences endpoint to track user interactions
        with pins and other content.
        
        Args:
            pin_id (str): The Pinterest pin ID
            placement_ids (list, optional): List of placement IDs. Defaults to [12].
            did_long_clickthrough (bool, optional): Whether user did a long clickthrough. Defaults to False.
            did_pin_clickthrough (bool, optional): Whether user did a pin clickthrough. Defaults to False.
            did_repin (bool, optional): Whether user did a repin. Defaults to False.
            is_own_or_group_pin (bool, optional): Whether the pin is owned by the user or their group. Defaults to False.
            login_page_type (str, optional): Type of login page. Defaults to "unknown".
            pin_image_signature (Optional[str], optional): Signature of the pin image. Defaults to None.
            is_creator_card_shown (bool, optional): Whether the creator card was shown. Defaults to True.
            creator_username (Optional[str], optional): Username of the creator. Defaults to None.
            android_app_launch_session_id (Optional[str], optional): Android app launch session ID. Defaults to None.
            allows_notifications (str, optional): Whether notifications are allowed. Defaults to "true".
            app_state (str, optional): App state (background/active). Defaults to "background".
            
        Returns:
            Dict[str, Any]: Response data including status and headers
            
        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        # Generate a session ID if not provided
        if not android_app_launch_session_id:
            android_app_launch_session_id = str(uuid.uuid4())
            
        # Generate a pin image signature if not provided
        if not pin_image_signature:
            pin_image_signature = uuid.uuid4().hex
            
        # Prepare the request URL and parameters
        base_url = "https://api.pinterest.com/v3/experiences/platform/ANDROID/"
        
        # Prepare extra context for URL
        extra_context = {
            "android_app_launch_session_id": android_app_launch_session_id,
            "allows_notifications": allows_notifications
        }
        
        # URL encode the extra context
        encoded_extra_context = quote(json.dumps(extra_context))
        
        # Construct the full URL with parameters
        url = f"{base_url}?extra_context={encoded_extra_context}"
        
        # Prepare the request payload
        payload = {
            "options": {
                "placement_ids": placement_ids,
                "extra_context": {
                    "pin_id": pin_id,
                    "did_long_clickthrough": did_long_clickthrough,
                    "did_pin_clickthrough": did_pin_clickthrough,
                    "did_repin": did_repin,
                    "is_own_or_group_pin": is_own_or_group_pin,
                    "login_page_type": login_page_type,
                    "pin_image_signature": pin_image_signature,
                    "is_creator_card_shown": is_creator_card_shown
                },
                "context": {}
            }
        }
        
        # Add creator username if provided
        if creator_username:
            payload["options"]["extra_context"]["creator_username"] = creator_username
        
        # Prepare headers
        headers = {
            "Host": "api.pinterest.com",
            "Accept-Language": "en-US",
            "User-Agent": "Pinterest for Android/13.12.4 (sdk_gphone64_arm64; 12)",
            "X-Pinterest-Advertising-Id": self.session.headers.get('X-Pinterest-Advertising-Id', ''),
            "X-Pinterest-App-Type-Detailed": "3",
            "X-Pinterest-Device": "sdk_gphone64_arm64",
            "X-Pinterest-Device-Hardwareid": self.session.headers.get('X-Pinterest-Device-Hardwareid', ''),
            "X-Pinterest-Device-Manufacturer": "Google",
            "X-Pinterest-Installid": self.session.headers.get('X-Pinterest-Installid', ''),
            "X-Pinterest-Appstate": app_state,
            "X-Node-Id": "true",
            "Authorization": self.session.headers.get('Authorization', ''),
            "Accept-Encoding": "gzip, deflate, br",
            "Priority": "u=1, i",
            "Content-Type": "application/json"
        }
        
        try:
            # Send the request
            response = requests.post(
                url=url,
                headers=headers,
                json=payload
            )
            
            self.logger.debug(
                "Sent experience tracking request",
                extra={
                    'context': {
                        'pin_id': pin_id,
                        'url': url,
                        'status_code': response.status_code,
                        'headers': dict(response.headers)
                    }
                }
            )
            
            return {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'response_data': response.json() if response.content else None
            }
            
        except requests.exceptions.RequestException as e:
            self.logger.error(
                "Experience tracking request failed",
                extra={
                    'context': {
                        'pin_id': pin_id,
                        'url': url,
                        'error': str(e)
                    }
                }
            )
            raise 