from pinterest_api import PinterestAPI
from pinterest_api.exceptions import (
    EmailNotFoundError,
    LoginFailedError,
    InvalidResponseError,
    PinterestAuthError,
    IncorrectPasswordError,
    AuthenticationError,
    PasswordResetedError
)
import requests
import json
from datetime import datetime
import os
import concurrent.futures
from typing import List, Dict, Any, Optional
from colorama import init, Fore, Style
import random
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Import our mixins
from .mixins.tracking_mixin import TrackingMixin
from .mixins.account_processor_mixin import AccountProcessorMixin
from .mixins.proxy_mixin import ProxyMixin
from .mixins.utility_mixin import UtilityMixin
from .mixins.pin_interaction_mixin import PinInteractionMixin
from .mixins.browser_mixin import BrowserMixin

# Initialize colorama for cross-platform colored output
init()

# File to track last rotation time
LAST_ROTATION_FILE = 'last_rotation.txt'
# File to track current IP
CURRENT_IP_FILE = 'current_ip.txt'

class PinterestAutomation:
    """
    Main class for Pinterest automation that uses mixins for different actions.
    """
    
    def __init__(self, accounts: List[Dict[str, str]], comments: List[str], 
                 num_pins_to_process: int = 10, max_workers: int = 10):
        """
        Initialize the Pinterest automation.
        
        Args:
            accounts (List[Dict[str, str]]): List of account dictionaries with 'email' and 'password'
            comments (List[str]): List of comments to use for pin interactions
            num_pins_to_process (int): Number of pins to process per account
            max_workers (int): Maximum number of concurrent workers
        """
        self.accounts = accounts
        self.comments = comments
        self.num_pins_to_process = num_pins_to_process
        self.max_workers = max_workers
        self.proxies = self._load_proxies()
        
        # Assign proxies to accounts
        self._assign_proxies_to_accounts()
    
    def _load_proxies(self) -> List[Dict[str, str]]:
        """Load proxy configurations."""
        # Hardcoded proxy configuration - in a real app, this would be loaded from a config file
        return [
            {
                'ip': '45.79.156.193',
                'port': '8527',
                'username': '81QRQ8B9TNXA',
                'password': 'jQKBfOZC0v',
                'rotate_url': 'https://api.mountproxies.com/api/proxy/67f3afc999e9e63742ed5658/rotate_ip?api_key=a4f667e14ef53ce1f5bb0a39a42a2d3a&_gl=1*hsie7f*_gcl_au*MjE0NzQwMTg3Ni4xNzQyNzI5OTgz'
            }
            # Add more proxies here if needed
        ]
    
    def _assign_proxies_to_accounts(self):
        """Assign proxies to accounts."""
        for i, account in enumerate(self.accounts):
            # Use modulo to cycle through available proxies
            proxy_index = i % len(self.proxies)
            proxy = self.proxies[proxy_index]
            account['proxy'] = f"{proxy['username']}:{proxy['password']}@{proxy['ip']}:{proxy['port']}"
    
    def run(self) -> List[Dict[str, Any]]:
        """
        Run the Pinterest automation for all accounts.
        
        Returns:
            List[Dict[str, Any]]: Results for each account
        """
        print(f"{Fore.CYAN}🚀 Starting to process {Fore.YELLOW}{len(self.accounts)}{Fore.CYAN} accounts with {Fore.YELLOW}{len(self.proxies)}{Fore.CYAN} proxies...{Style.RESET_ALL}")
        
        # Get unique proxies from accounts
        unique_proxies = set(account.get('proxy') for account in self.accounts if account.get('proxy'))
        
        # If we have only one proxy, process accounts sequentially
        if len(unique_proxies) <= 1:
            print(f"{Fore.YELLOW}⚠️ Only one proxy available. Processing accounts sequentially.{Style.RESET_ALL}")
            results = []
            for account in self.accounts:
                try:
                    result = self._process_account(account)
                    results.append(result)
                except Exception as e:
                    print(f"{Fore.RED}❌ Error processing {Fore.YELLOW}{account['email']}{Fore.RED}: {str(e)}{Style.RESET_ALL}")
                    results.append({
                        'email': account['email'],
                        'status': 'failed',
                        'error': str(e)
                    })
        else:
            # If we have multiple proxies, process accounts in parallel
            print(f"{Fore.GREEN}✨ Multiple proxies available. Processing accounts in parallel.{Style.RESET_ALL}")
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(self.max_workers, len(unique_proxies))) as executor:
                # Submit all accounts for processing
                future_to_account = {
                    executor.submit(self._process_account, account): account 
                    for account in self.accounts
                }
                
                # Collect results as they complete
                results = []
                for future in concurrent.futures.as_completed(future_to_account):
                    account = future_to_account[future]
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        print(f"{Fore.RED}❌ Error processing {Fore.YELLOW}{account['email']}{Fore.RED}: {str(e)}{Style.RESET_ALL}")
                        results.append({
                            'email': account['email'],
                            'status': 'failed',
                            'error': str(e)
                        })
        
        # Print summary
        successful = 0
        password_reset = 0
        other_failed = 0
        
        # Count different result types
        for r in results:
            # First check for password reset errors
            if r.get('error_type') == 'password_reset' or any('password has been reset' in str(error).lower() for error in r.get('errors', [])):
                password_reset += 1
            # Then check for active status
            elif r.get('status') == 'active':
                successful += 1
            # Otherwise count as general failure
            else:
                other_failed += 1
        
        print(f"\n{Fore.CYAN}📊 Summary:{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Total accounts: {Fore.YELLOW}{len(self.accounts)}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}Successful: {Fore.YELLOW}{successful}{Style.RESET_ALL}")
        if password_reset > 0:
            print(f"{Fore.RED}Password Reset: {Fore.YELLOW}{password_reset}{Style.RESET_ALL}")
        if other_failed > 0:
            print(f"{Fore.RED}Other Errors: {Fore.YELLOW}{other_failed}{Style.RESET_ALL}")
        
        # Print details of failed accounts
        failed_total = password_reset + other_failed
        if failed_total > 0:
            print(f"\n{Fore.RED}Failed accounts details:{Style.RESET_ALL}")
            for result in results:
                if result['status'] != 'active':
                    email = result.get('email', 'Unknown')
                    error = result.get('error', 'Unknown error')
                    
                    # Check if it's a password reset error
                    if result.get('error_type') == 'password_reset' or 'password has been reset' in str(error).lower():
                        print(f"  {Fore.RED}❌ {email}: {Fore.YELLOW}Password has been reset{Style.RESET_ALL}")
                    else:
                        print(f"  {Fore.RED}❌ {email}: {error}{Style.RESET_ALL}")
        
        print(f"\n{Fore.CYAN}📊 Final Summary:{Style.RESET_ALL}")
        print(f"Total accounts: {len(results)}")
        print(f"Successful: {Fore.GREEN}{successful}{Style.RESET_ALL}")
        print(f"Failed: {Fore.RED}{failed_total}{Style.RESET_ALL}")
        if password_reset > 0:
            print(f"  - Password Reset: {Fore.RED}{password_reset}{Style.RESET_ALL}")
        if other_failed > 0:
            print(f"  - Other Errors: {Fore.RED}{other_failed}{Style.RESET_ALL}")
        print(f"Total time: {sum(r.get('processing_time', 0) for r in results):.2f} seconds")
        
        return results
    
    def _process_account(self, account: Dict[str, str], retry_count: int = 0, max_retries: int = 3) -> Dict[str, Any]:
        """
        Process a single Pinterest account.
        
        Args:
            account (Dict[str, str]): Account dictionary with 'email' and 'password'
            retry_count (int): Current retry attempt number
            max_retries (int): Maximum number of retries allowed
            
        Returns:
            Dict[str, Any]: Result of processing the account
        """
        # This method will be implemented by the AccountProcessorMixin
        raise NotImplementedError("This method should be implemented by a mixin")


class PinterestAutomationWithMixins(PinterestAutomation, TrackingMixin, AccountProcessorMixin, ProxyMixin, UtilityMixin, PinInteractionMixin, BrowserMixin):
    """
    Main class for Pinterest automation that combines all mixins.
    """
    
    def __init__(self, accounts: List[Dict[str, str]], comments: List[str], num_pins_to_process: int = 10, max_workers: int = 5):
        """
        Initialize the Pinterest automation with mixins.
        
        Args:
            accounts (List[Dict[str, str]]): List of account dictionaries with 'email' and 'password'
            comments (List[str]): List of comments to use for pin interactions
            num_pins_to_process (int): Number of pins to process per account
            max_workers (int): Maximum number of concurrent workers
        """
        super().__init__(accounts, comments, num_pins_to_process, max_workers)
        print(f"Initializing PinterestAutomationWithMixins {num_pins_to_process}")
        self.tracking = TrackingMixin()
        self.account_processor = AccountProcessorMixin(
            num_pins_to_process=num_pins_to_process
        )
        self.proxy_manager = ProxyMixin()
        self.utility = UtilityMixin()
    
    def _process_account(self, account: Dict[str, Any], retry_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a single account with all mixin functionalities.
        
        Args:
            account (Dict[str, Any]): Account dictionary with credentials and proxy info
            retry_params (Dict[str, Any], optional): Parameters for retry logic
            
        Returns:
            Dict[str, Any]: Result of account processing
        """
        start_time = time.time()
        result = {
            'email': account['email'],
            'status': 'failed',
            'error': None,
            'processing_time': 0,
            'pins_processed': 0,
            'proxy_rotations': 0
        }
        
        try:
            # Skip proxy rotation for the first account
            if False:
                print(f"{Fore.CYAN}⏭️ Skipping proxy rotation for first account{Style.RESET_ALL}")
            else:
                # Rotate proxy before processing
                if 'proxy' in account:
                    print(f"{Fore.CYAN}🔄 Rotating proxy for account {account['email']}...{Style.RESET_ALL}")
                    if not self.proxy_manager.rotate_proxy_for_account(account):
                        result['error'] = 'Failed to rotate proxy'
                        return result
                    result['proxy_rotations'] += 1
            
            # Initialize Pinterest API with email and password
            api = PinterestAPI(
                email=account['email'],
                password=account['password']
            )
            
            # Process account using AccountProcessorMixin
            try:
                account_result = self.account_processor.process_account(
                    account=account,
                    api=api,
                    result={},
                    retry_params=retry_params
                )
                
                # Update result with account processing details
                result.update(account_result)
                
                # Set status to active ONLY if no errors occurred AND this is not a password reset case
                if not result.get('error') and not any('password has been reset' in str(error).lower() for error in result.get('errors', [])) and result.get('error_type') != 'password_reset':
                    result['status'] = 'active'
                else:
                    result['status'] = 'failed'
            except PasswordResetedError as e:
                error_msg = str(e)
                print(f"{Fore.RED}❌ Password Reset Error: {error_msg}{Style.RESET_ALL}")
                result['status'] = 'failed'
                result['error'] = error_msg
                # Add specific error type information
                result['error_type'] = 'password_reset'
                result['errors'] = result.get('errors', []) + [error_msg]
            
            # Track events using TrackingMixin
            self.tracking.track_account_processed(
                account=account,
                result=result,
                processing_time=time.time() - start_time
            )
            
            # Record processing time
            result['processing_time'] = time.time() - start_time
            
            # Final status check for password reset - ALWAYS override to failed
            if any('password has been reset' in str(error).lower() for error in result.get('errors', [])) or result.get('error_type') == 'password_reset':
                result['status'] = 'failed'
                
            return result
            
        except PasswordResetedError as e:
            # Handle password reset error at the top level
            error_msg = str(e)
            print(f"{Fore.RED}❌ Password Reset Error: {error_msg}{Style.RESET_ALL}")
            result['status'] = 'failed'
            result['error'] = error_msg
            # Add specific error type information
            result['error_type'] = 'password_reset'
            result['errors'] = [error_msg]
        except Exception as e:
            # Handle other exceptions
            error_msg = f"Error processing account: {str(e)}"
            print(f"{Fore.RED}❌ {error_msg}{Style.RESET_ALL}")
            result['status'] = 'failed'
            result['error'] = error_msg
        
        # Record processing time even for errors
        result['processing_time'] = time.time() - start_time
        
        return result 