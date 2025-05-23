import requests
import time
from typing import Dict, Any, Optional
from colorama import Fore, Style

class ProxyMixin:
    """
    Mixin for proxy-related operations.
    """
    
    def check_current_ip(self, proxy_config: Dict[str, str]) -> Optional[str]:
        """
        Check and return the current IP using the proxy.
        
        Args:
            proxy_config (Dict[str, str]): Proxy configuration
            
        Returns:
            Optional[str]: Current IP address or None if check failed
        """
        try:
            response = requests.get('https://api.ipify.org?format=json', proxies=proxy_config, timeout=10)
            return response.json()['ip']
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Error checking current IP: {e}{Style.RESET_ALL}")
            return None
    
    def rotate_ip(self, proxy: Dict[str, str]) -> bool:
        """
        Rotate the proxy IP with time check and retry logic.
        
        Args:
            proxy (Dict[str, str]): Proxy configuration
            
        Returns:
            bool: True if rotation was successful, False otherwise
        """
        # Check if we need to wait before rotating
        last_rotation = self.get_last_rotation_time()
        current_time = self.get_current_time()
        time_since_last_rotation = current_time - last_rotation
        
        wait_time_for_rotation = 130
         
        if time_since_last_rotation < wait_time_for_rotation:
            wait_time = wait_time_for_rotation - time_since_last_rotation
            print(f"{Fore.YELLOW}⏳ Waiting {wait_time} seconds before rotating IP...{Style.RESET_ALL}")
            time.sleep(wait_time)
        
        # Get the IP before rotation
        last_ip = self.get_last_ip()
        
        # Rotate the IP
        rotate_url = proxy.get('rotate_url')
        max_attempts = 3
        maintenance_retries = 2  # Number of times to retry for maintenance
        maintenance_attempts = 0
        
        for attempt in range(1, max_attempts + 1):
            try:
                print(f"{Fore.CYAN}🔄 Rotating IP, attempt {attempt}/{max_attempts}...{Style.RESET_ALL}")
                rotation_response = requests.get(rotate_url, timeout=45)
                
                if rotation_response.status_code != 200:
                    print(f"{Fore.YELLOW}⚠️ Rotation failed: {rotation_response.text}{Style.RESET_ALL}")
                    
                    # Check for specific error messages
                    try:
                        error_data = rotation_response.json()
                        if "message" in error_data:
                            error_message = error_data["message"].lower()
                            
                            # Check for "wait for atleast 120 seconds" message
                            if "wait for atleast 120 seconds" in error_message:
                                print(f"{Fore.YELLOW}⏳ Waiting 130 seconds before retrying rotation...{Style.RESET_ALL}")
                                time.sleep(130)
                                continue
                            
                            # Check for "being processed" message
                            elif "rotation is currently being processed" in error_message or "automatically rotating the ip" in error_message:
                                print(f"{Fore.YELLOW}⏳ IP rotation is in progress. Waiting 120 seconds before retrying...{Style.RESET_ALL}")
                                time.sleep(120)
                                continue
                            
                            # Check for "proxy server under maintenance" message
                            elif "proxy server under maintenance" in error_message or "try again in 5 minutes" in error_message:
                                maintenance_attempts += 1
                                
                                # If we've tried too many times, give up
                                if maintenance_attempts > maintenance_retries:
                                    print(f"{Fore.RED}❌ Proxy server is still under maintenance after {maintenance_attempts} attempts. Giving up.{Style.RESET_ALL}")
                                    return False
                                
                                wait_minutes = 5
                                wait_seconds = wait_minutes * 60
                                print(f"{Fore.YELLOW}⏳ Proxy server under maintenance. Waiting {wait_minutes} minutes before retrying... (Attempt {maintenance_attempts}/{maintenance_retries}){Style.RESET_ALL}")
                                time.sleep(wait_seconds)
                                
                                # Reset the current attempt so we don't count this against our regular retries
                                attempt -= 1
                                continue
                    except (ValueError, KeyError):
                        pass
                    
                    if attempt < max_attempts:
                        time.sleep(5)
                        continue
                    return False
                
                # Wait a bit for the rotation to take effect
                print(f"{Fore.YELLOW}⏳ Waiting 35 seconds for rotation to take effect...{Style.RESET_ALL}")
                time.sleep(35)
                
                # Check the new IP
                proxy_config = {
                    'http': f'http://{proxy["username"]}:{proxy["password"]}@{proxy["ip"]}:{proxy["port"]}',
                    'https': f'http://{proxy["username"]}:{proxy["password"]}@{proxy["ip"]}:{proxy["port"]}'
                }
                new_ip = self.check_current_ip(proxy_config)
                
                if not new_ip:
                    print(f"{Fore.YELLOW}⚠️ Could not verify new IP{Style.RESET_ALL}")
                    if attempt < max_attempts:
                        time.sleep(15)
                        continue
                    return False
                
                # Check if IP actually changed
                if last_ip and new_ip == last_ip:
                    print(f"{Fore.YELLOW}⚠️ IP didn't change: {new_ip}{Style.RESET_ALL}")
                    if attempt < max_attempts:
                        time.sleep(10)
                        continue
                    return False
                
                # Success! Update files and return
                print(f"{Fore.GREEN}✅ Successfully rotated IP to: {new_ip}{Style.RESET_ALL}")
                self.save_current_ip(new_ip)
                self.update_last_rotation_time()
                return True
                
            except Exception as e:
                print(f"{Fore.YELLOW}⚠️ Error during rotation attempt {attempt}: {str(e)}{Style.RESET_ALL}")
                
                # Check if this is a timeout exception, which might indicate maintenance
                if "timeout" in str(e).lower():
                    print(f"{Fore.YELLOW}⏳ Request timed out, possibly due to proxy maintenance. Waiting 2 minutes before retrying...{Style.RESET_ALL}")
                    time.sleep(120)
                    # Don't count this as a regular attempt
                    attempt -= 1
                    continue
                
                if attempt < max_attempts:
                    time.sleep(5)
                else:
                    return False
    
    def rotate_proxy_for_account(self, account: Dict[str, Any]) -> bool:
        """
        Rotate the proxy for a specific account.
        
        Args:
            account (Dict[str, Any]): Account dictionary with proxy information
            
        Returns:
            bool: True if rotation was successful, False otherwise
        """
        if 'proxy' not in account:
            print(f"{Fore.YELLOW}⚠️ No proxy found for account {account['email']}{Style.RESET_ALL}")
            return False
            
        # Extract proxy information
        proxy_str = account['proxy']
        try:
            # Parse proxy string (format: username:password@ip:port)
            auth, address = proxy_str.split('@')
            username, password = auth.split(':')
            ip, port = address.split(':')
            
            # Get the rotate URL from account if available, otherwise use the default
            rotate_url = account.get('rotate_url', 'https://api.mountproxies.com/api/proxy/67f3afc999e9e63742ed5658/rotate_ip?api_key=a4f667e14ef53ce1f5bb0a39a42a2d3a&_gl=1*hsie7f*_gcl_au*MjE0NzQwMTg3Ni4xNzQyNzI5OTgz')
            
            proxy = {
                'username': username,
                'password': password,
                'ip': ip,
                'port': port,
                'rotate_url': rotate_url
            }
            
            # Rotate the IP
            rotation_result = self.rotate_ip(proxy)
            
            if not rotation_result:
                # If rotation failed, notify the user and suggest what to do
                print(f"{Fore.RED}⚠️ Proxy rotation failed for account {account['email']}. The script will continue but may fail if IP is blocked.{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}💡 Suggestion: You can manually restart the script in a few minutes when proxy is available again.{Style.RESET_ALL}")
            
            return rotation_result
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error rotating proxy for account {account['email']}: {str(e)}{Style.RESET_ALL}")
            return False
    
    def get_current_time(self) -> float:
        """
        Get the current time in seconds since epoch.
        
        Returns:
            float: Current time
        """
        return time.time()
    
    def get_last_rotation_time(self) -> float:
        """
        Get the timestamp of the last IP rotation.
        
        Returns:
            float: Last rotation time or 0 if not available
        """
        try:
            with open('last_rotation.txt', 'r') as f:
                return float(f.read().strip())
        except (FileNotFoundError, ValueError):
            return 0
    
    def update_last_rotation_time(self) -> None:
        """
        Update the timestamp of the last IP rotation.
        """
        with open('last_rotation.txt', 'w') as f:
            f.write(str(self.get_current_time()))
    
    def get_last_ip(self) -> Optional[str]:
        """
        Get the last known IP address.
        
        Returns:
            Optional[str]: Last IP address or None if not available
        """
        try:
            with open('current_ip.txt', 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            return None
    
    def save_current_ip(self, ip: str) -> None:
        """
        Save the current IP address.
        
        Args:
            ip (str): IP address to save
        """
        with open('current_ip.txt', 'w') as f:
            f.write(ip) 