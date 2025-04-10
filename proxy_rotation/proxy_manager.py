import os
import time
import json
import requests
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from colorama import Fore, Style

from .proxy_config import ProxyConfig, ProxyConfigManager

class ProxyManager:
    """
    Manager class for handling proxy rotation and management.
    """
    
    def __init__(self, config_file: str = "proxy_config.json"):
        """
        Initialize the ProxyManager.
        
        Args:
            config_file (str): Path to the proxy configuration file
        """
        self.config_manager = ProxyConfigManager(config_file)
        self.last_rotation_file = 'last_rotation.txt'
        self.current_ip_file = 'current_ip.txt'
        self.min_rotation_interval = 130  # Minimum seconds between rotations
    
    def get_current_time(self) -> int:
        """
        Get current time in seconds since epoch.
        
        Returns:
            int: Current time in seconds
        """
        return int(time.time())
    
    def get_last_rotation_time(self) -> int:
        """
        Get the timestamp of the last rotation.
        
        Returns:
            int: Timestamp of the last rotation
        """
        if os.path.exists(self.last_rotation_file):
            with open(self.last_rotation_file, 'r') as f:
                try:
                    return int(f.read().strip())
                except:
                    return 0
        return 0
    
    def update_last_rotation_time(self) -> None:
        """
        Update the last rotation timestamp.
        """
        with open(self.last_rotation_file, 'w') as f:
            f.write(str(self.get_current_time()))
    
    def get_last_ip(self) -> Optional[str]:
        """
        Get the last used IP.
        
        Returns:
            Optional[str]: The last used IP or None if not available
        """
        if os.path.exists(self.current_ip_file):
            with open(self.current_ip_file, 'r') as f:
                return f.read().strip()
        return None
    
    def save_current_ip(self, ip: str) -> None:
        """
        Save the current IP.
        
        Args:
            ip (str): The IP to save
        """
        with open(self.current_ip_file, 'w') as f:
            f.write(ip)
    
    def check_current_ip(self, proxy: ProxyConfig) -> Optional[str]:
        """
        Check and return the current IP using the proxy.
        
        Args:
            proxy (ProxyConfig): The proxy configuration to use
            
        Returns:
            Optional[str]: The current IP or None if check failed
        """
        try:
            response = requests.get('https://api.ipify.org?format=json', proxies=proxy.get_proxy_dict(), timeout=10)
            return response.json()['ip']
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Error checking current IP: {e}{Style.RESET_ALL}")
            return None
    
    def rotate_ip(self, proxy: ProxyConfig) -> bool:
        """
        Rotate the proxy IP with time check and retry logic.
        
        Args:
            proxy (ProxyConfig): The proxy configuration to rotate
            
        Returns:
            bool: True if rotation was successful, False otherwise
        """
        # Check if we need to wait before rotating
        last_rotation = self.get_last_rotation_time()
        current_time = self.get_current_time()
        time_since_last_rotation = current_time - last_rotation
        
        if time_since_last_rotation < self.min_rotation_interval:
            wait_time = self.min_rotation_interval - time_since_last_rotation
            print(f"{Fore.YELLOW}⏳ Waiting {wait_time} seconds before rotating IP...{Style.RESET_ALL}")
            time.sleep(wait_time)
        
        # Get the IP before rotation
        last_ip = self.get_last_ip()
        
        # Rotate the IP
        rotate_url = proxy.rotate_url
        max_attempts = 3
        
        for attempt in range(1, max_attempts + 1):
            try:
                print(f"{Fore.CYAN}🔄 Rotating IP, attempt {attempt}/{max_attempts}...{Style.RESET_ALL}")
                rotation_response = requests.get(rotate_url, timeout=45)
                
                if rotation_response.status_code != 200:
                    print(f"{Fore.YELLOW}⚠️ Rotation failed: {rotation_response.text}{Style.RESET_ALL}")
                    # Check for specific error message about waiting 120 seconds
                    try:
                        error_data = rotation_response.json()
                        if "message" in error_data and "wait for atleast 120 seconds" in error_data["message"].lower():
                            print(f"{Fore.YELLOW}⏳ Waiting 120 seconds before retrying rotation...{Style.RESET_ALL}")
                            time.sleep(120)
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
                new_ip = self.check_current_ip(proxy)
                
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
                
                # Update the proxy object
                proxy.current_ip = new_ip
                proxy.last_rotation_time = self.get_current_time()
                self.config_manager.save_config()
                
                return True
                
            except Exception as e:
                print(f"{Fore.YELLOW}⚠️ Error during rotation attempt {attempt}: {e}{Style.RESET_ALL}")
                if attempt < max_attempts:
                    time.sleep(5)
                else:
                    return False
        
        return False
    
    def assign_proxies_to_accounts(self, accounts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Assign proxies to accounts based on their index.
        
        Args:
            accounts (List[Dict[str, Any]]): List of account dictionaries
            
        Returns:
            List[Dict[str, Any]]: Updated account list with proxy assignments
        """
        proxies = self.config_manager.get_proxies()
        if not proxies:
            print(f"{Fore.YELLOW}⚠️ No proxies available. Accounts will not have proxy assignments.{Style.RESET_ALL}")
            return accounts
        
        for i, account in enumerate(accounts):
            # Use modulo to cycle through available proxies
            proxy_index = i % len(proxies)
            proxy = proxies[proxy_index]
            account['proxy'] = proxy.get_proxy_string()
            account['proxy_config'] = proxy.to_dict()
        
        return accounts
    
    def get_proxy_for_account(self, account: Dict[str, Any]) -> Optional[ProxyConfig]:
        """
        Get the proxy configuration for an account.
        
        Args:
            account (Dict[str, Any]): Account dictionary
            
        Returns:
            Optional[ProxyConfig]: The proxy configuration or None if not found
        """
        if 'proxy_config' in account:
            return ProxyConfig.from_dict(account['proxy_config'])
        return None
    
    def rotate_proxy_for_account(self, account: Dict[str, Any]) -> bool:
        """
        Rotate the proxy for an account.
        
        Args:
            account (Dict[str, Any]): Account dictionary
            
        Returns:
            bool: True if rotation was successful, False otherwise
        """
        proxy = self.get_proxy_for_account(account)
        if not proxy:
            print(f"{Fore.YELLOW}⚠️ No proxy configuration found for account {account.get('email', 'unknown')}{Style.RESET_ALL}")
            return False
        
        print(f"{Fore.CYAN}🔄 Rotating proxy for account {Fore.YELLOW}{account.get('email', 'unknown')}{Style.RESET_ALL}")
        return self.rotate_ip(proxy)
    
    def get_proxy_status(self) -> List[Dict[str, Any]]:
        """
        Get the status of all proxies.
        
        Returns:
            List[Dict[str, Any]]: List of proxy status dictionaries
        """
        proxies = self.config_manager.get_proxies()
        status = []
        
        for proxy in proxies:
            proxy_status = {
                'proxy': str(proxy),
                'current_ip': proxy.current_ip,
                'last_rotation': datetime.fromtimestamp(proxy.last_rotation_time).isoformat() if proxy.last_rotation_time else None,
                'time_since_rotation': self.get_current_time() - proxy.last_rotation_time if proxy.last_rotation_time else None
            }
            status.append(proxy_status)
        
        return status
    
    def print_proxy_status(self) -> None:
        """
        Print the status of all proxies.
        """
        status = self.get_proxy_status()
        
        print(f"\n{Fore.CYAN}📊 Proxy Status:{Style.RESET_ALL}")
        for proxy_status in status:
            proxy = proxy_status['proxy']
            current_ip = proxy_status['current_ip']
            last_rotation = proxy_status['last_rotation']
            time_since_rotation = proxy_status['time_since_rotation']
            
            print(f"{Fore.CYAN}Proxy: {Fore.YELLOW}{proxy}{Style.RESET_ALL}")
            print(f"  Current IP: {Fore.WHITE}{current_ip or 'Unknown'}{Style.RESET_ALL}")
            print(f"  Last Rotation: {Fore.WHITE}{last_rotation or 'Never'}{Style.RESET_ALL}")
            if time_since_rotation is not None:
                print(f"  Time Since Rotation: {Fore.WHITE}{time_since_rotation} seconds{Style.RESET_ALL}")
            print() 