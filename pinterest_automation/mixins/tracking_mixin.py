import time
from typing import Dict, Any, Optional
from colorama import Fore, Style

class TrackingMixin:
    """
    Mixin for tracking-related operations.
    """
    
    def track_app_launch(self, pinterest_api, user_id: str) -> Dict[str, Any]:
        """
        Track app launch event.
        
        Args:
            pinterest_api: Pinterest API instance
            user_id (str): User ID
            
        Returns:
            Dict[str, Any]: Result of the tracking operation
        """
        result = {
            'success': False,
            'error': None
        }
        
        try:
            print(f"{Fore.CYAN}📱 Tracking app launch event{Style.RESET_ALL}")
            
            # Track app launch event
            print(f"{Fore.YELLOW}📤 Sending AppLaunch tracking event...{Style.RESET_ALL}")
            tracking_response = pinterest_api.track_custom_event(
                event_name="AppLaunch",
                event_data={
                    "LaunchType": "cold_start",
                    "AppState": "foreground",
                    "NetworkType": "wifi"
                },
                user_id=user_id
            )
            print(f"{Fore.GREEN}✅ AppLaunch tracking successful {Style.RESET_ALL}")
            
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
            print(f"{Fore.YELLOW}⚠️ AppLaunch tracking failed: {str(e)}{Style.RESET_ALL}")
        
        return result
    
    def track_app_start(self, pinterest_api, user_id: str) -> Dict[str, Any]:
        """
        Track app start event.
        
        Args:
            pinterest_api: Pinterest API instance
            user_id (str): User ID
            
        Returns:
            Dict[str, Any]: Result of the tracking operation
        """
        result = {
            'success': False,
            'error': None
        }
        
        try:
            print(f"{Fore.YELLOW}📤 Sending app_start tracking event...{Style.RESET_ALL}")
            
            # Track app_start event
            tracking_response = pinterest_api.track_custom_event(
                event_name="app_start",
                event_data={
                    "system_info": {
                        "os_version": "12",
                        "app_version": "13.12",
                        "device_model": "sdk_gphone64_arm64"
                    }
                },
                user_id=user_id
            )
            print(f"{Fore.GREEN}✅ app_start tracking successful {Style.RESET_ALL}")
            
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
            print(f"{Fore.YELLOW}⚠️ app_start tracking failed: {str(e)}{Style.RESET_ALL}")
        
        return result
    
    def track_pin_click(self, pinterest_api, pin_id: str, board_id: str, user_id: str) -> Dict[str, Any]:
        """
        Track pin click event.
        
        Args:
            pinterest_api: Pinterest API instance
            pin_id (str): Pin ID
            board_id (str): Board ID
            user_id (str): User ID
            
        Returns:
            Dict[str, Any]: Result of the tracking operation
        """
        result = {
            'success': False,
            'error': None
        }
        
        try:
            print(f"{Fore.YELLOW}📤 Sending pin_click tracking event for pin {pin_id}...{Style.RESET_ALL}")
            
            # Track pin click event
            tracking_response = pinterest_api.track_custom_event(
                event_name="pin_click",
                event_data={
                    "pin_id": pin_id,
                    "board_id": board_id,
                    "source": "home_feed"
                },
                user_id=user_id
            )
            print(f"{Fore.GREEN}✅ pin_click tracking successful {Style.RESET_ALL}")
            
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
            print(f"{Fore.YELLOW}⚠️ pin_click tracking failed: {str(e)}{Style.RESET_ALL}")
        
        return result
    
    def track_in_app_browser_start(self, pinterest_api, user_id: str) -> Dict[str, Any]:
        """
        Track in-app browser start event.
        
        Args:
            pinterest_api: Pinterest API instance
            user_id (str): User ID
            
        Returns:
            Dict[str, Any]: Result of the tracking operation
        """
        result = {
            'success': False,
            'error': None
        }
        
        try:
            # Track InAppBrowser start event
            tracking_response = pinterest_api.track_custom_event(
                event_name="InAppBrowser",
                event_data={
                    "TIMESTAMP": str(int(time.time() * 1000)),
                    "ReportingTool": "INSTABUG",
                    "ChromeTabHelper": "start"
                },
                user_id=user_id
            )
            
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
            print(f"{Fore.YELLOW}⚠️ Error tracking InAppBrowser start: {str(e)}{Style.RESET_ALL}")
        
        return result
    
    def track_in_app_browser_end(self, pinterest_api, user_id: str) -> Dict[str, Any]:
        """
        Track in-app browser end event.
        
        Args:
            pinterest_api: Pinterest API instance
            user_id (str): User ID
            
        Returns:
            Dict[str, Any]: Result of the tracking operation
        """
        result = {
            'success': False,
            'error': None
        }
        
        try:
            # Track InAppBrowser end event
            tracking_response = pinterest_api.track_custom_event(
                event_name="InAppBrowser",
                event_data={
                    "TIMESTAMP": str(int(time.time() * 1000)),
                    "ReportingTool": "INSTABUG",
                    "ChromeTabHelper": "end"
                },
                user_id=user_id
            )
            print(f"{Fore.GREEN}✅ visit_link tracking successful {Style.RESET_ALL}")
            
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
            print(f"{Fore.YELLOW}⚠️ visit_link tracking failed: {str(e)}{Style.RESET_ALL}")
        
        return result
    
    def track_offsite_view(self, pinterest_api, url: str, pin_id: str, check_only: bool = True) -> Dict[str, Any]:
        """
        Track offsite view event.
        
        Args:
            pinterest_api: Pinterest API instance
            url (str): URL to track
            pin_id (str): Pin ID
            check_only (bool): Whether to only check the URL without tracking
            
        Returns:
            Dict[str, Any]: Result of the tracking operation
        """
        result = {
            'success': False,
            'error': None
        }
        
        try:
            print(f"{Fore.CYAN}👁️ Tracking offsite view for pin {pin_id}{Style.RESET_ALL}")
            
            # Track offsite view
            offsite_track = pinterest_api.track_offsite_view(
                url=url,
                pin_id=pin_id,
                check_only=check_only,
                clickthrough_source='closeup'
            )
            
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
            print(f"{Fore.YELLOW}⚠️ Error tracking offsite view: {str(e)}{Style.RESET_ALL}")
        
        return result
    
    def send_warm_requests(self, pinterest_api) -> Dict[str, Any]:
        """
        Send warm requests to various endpoints.
        
        Args:
            pinterest_api: Pinterest API instance
            
        Returns:
            Dict[str, Any]: Result of the warm requests
        """
        result = {
            'success': False,
            'error': None,
            'pinimg': False,
            'api': False
        }
        
        try:
            # Simulate warm request to i.pinimg.com
            print(f"{Fore.CYAN}🌡️ Sending warm request to i.pinimg.com{Style.RESET_ALL}")
            try:
                warm_pinimg = pinterest_api.warm_request(endpoint='pinimg')
                result['pinimg'] = True
            except Exception as e:
                print(f"{Fore.YELLOW}⚠️ Warm request to pinimg failed: {str(e)}{Style.RESET_ALL}")
            
            # Simulate warm request to api.pinterest.com
            print(f"{Fore.CYAN}🌡️ Sending warm request to api.pinterest.com{Style.RESET_ALL}")
            try:
                warm_api = pinterest_api.warm_request(endpoint='api')
                result['api'] = True
            except Exception as e:
                print(f"{Fore.YELLOW}⚠️ Warm request to api failed: {str(e)}{Style.RESET_ALL}")
            
            # Check Facebook installation status
            print(f"{Fore.CYAN}📱 Checking Facebook installation status{Style.RESET_ALL}")
            try:
                fb_check = pinterest_api.track_action(
                    action_type='facebook_installed',
                    additional_tags={
                        "app": "ANDROID_MOBILE",
                        "installed": "false",
                        "app_version": "13128040"
                    }
                )
            except Exception as e:
                print(f"{Fore.YELLOW}⚠️ Facebook installation check failed: {str(e)}{Style.RESET_ALL}")
            
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
            print(f"{Fore.YELLOW}⚠️ Error sending warm requests: {str(e)}{Style.RESET_ALL}")
        
        return result
    
    def track_error(self, account: Dict[str, Any], error: str, error_type: str) -> None:
        """
        Track an error that occurred during account processing.
        
        Args:
            account (Dict[str, Any]): The account that encountered the error
            error (str): The error message
            error_type (str): The type of error (e.g., 'LoginError', 'ProxyError')
        """
        try:
            # Log the error
            print(f"{Fore.RED}❌ Error tracking for account {account['email']}:")
            print(f"  Type: {error_type}")
            print(f"  Message: {error}{Style.RESET_ALL}")
            
            # You can add additional error tracking logic here
            # For example, saving to a log file or sending to a monitoring service
            
        except Exception as e:
            print(f"{Fore.RED}❌ Failed to track error: {str(e)}{Style.RESET_ALL}")
    
    def track_account_processed(self, account: Dict[str, Any], result: Dict[str, Any], processing_time: float) -> None:
        """
        Track the processing of an account.
        
        Args:
            account (Dict[str, Any]): The account that was processed
            result (Dict[str, Any]): The result of processing
            processing_time (float): Time taken to process the account
        """
        try:
            # Log the processing result
            status_color = Fore.GREEN if result['status'] == 'active' else Fore.RED
            print(f"{status_color}📊 Account processing result for {account['email']}:")
            print(f"  Status: {result['status']}")
            print(f"  Processing time: {processing_time:.2f} seconds")
            if result.get('error'):
                print(f"  Error: {result['error']}{Style.RESET_ALL}")
            
            # You can add additional tracking logic here
            # For example, saving to a database or sending to analytics
            
        except Exception as e:
            print(f"{Fore.RED}❌ Failed to track account processing: {str(e)}{Style.RESET_ALL}") 