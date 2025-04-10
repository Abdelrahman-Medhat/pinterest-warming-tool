#!/usr/bin/env python3
"""
Pinterest Automation Script

This script automates Pinterest interactions using the pinterest_automation module.
It processes multiple accounts, interacts with pins, and tracks various events.
"""

import os
import json
import time
from datetime import datetime
from typing import List, Dict, Any
from colorama import init, Fore, Style

# Import our Pinterest automation module
from pinterest_automation import PinterestAutomationWithMixins
# Import our proxy rotation module
from proxy_rotation import ProxyManager
# Import configuration
from config import NUM_PINS_TO_PROCESS, MAX_WORKERS, ACCOUNTS_FILE, COMMENTS_FILE

# Initialize colorama for cross-platform colored output
init()

def load_accounts(file_path: str = ACCOUNTS_FILE) -> List[Dict[str, str]]:
    """
    Load Pinterest accounts from a JSON file.
    
    Args:
        file_path (str): Path to the JSON file containing account information
        
    Returns:
        List[Dict[str, str]]: List of account dictionaries with 'email' and 'password'
    """
    try:
        with open(file_path, 'r') as f:
            accounts = json.load(f)
        
        # Validate account behaviors and device info
        for account in accounts:
            # Ensure behaviors field exists
            if 'behaviors' not in account:
                print(f"{Fore.YELLOW}⚠️ No behaviors specified for account {account.get('email', 'unknown')}, using defaults{Style.RESET_ALL}")
                account['behaviors'] = {
                    'open_pin': 100,
                    'like_pin': 100,
                    'save_pin': 100,
                    'comment_pin': 100,
                    'visit_link': 100
                }
            else:
                # Ensure all behavior fields exist
                behaviors = account['behaviors']
                default_behaviors = {
                    'open_pin': 100,
                    'like_pin': 100,
                    'save_pin': 100,
                    'comment_pin': 100,
                    'visit_link': 100
                }
                
                # Add missing behaviors with defaults
                for behavior, default in default_behaviors.items():
                    if behavior not in behaviors:
                        print(f"{Fore.YELLOW}⚠️ Missing behavior '{behavior}' for account {account.get('email', 'unknown')}, using default: {default}%{Style.RESET_ALL}")
                        behaviors[behavior] = default
                
                # Ensure visit_link is always 100%
                if behaviors.get('visit_link', 100) != 100:
                    print(f"{Fore.YELLOW}⚠️ Forcing visit_link to 100% for account {account.get('email', 'unknown')}{Style.RESET_ALL}")
                    behaviors['visit_link'] = 100
                
                # Validate probability values (0-100)
                for behavior, probability in behaviors.items():
                    if not isinstance(probability, (int, float)) or probability < 0 or probability > 100:
                        print(f"{Fore.YELLOW}⚠️ Invalid probability value for '{behavior}' in account {account.get('email', 'unknown')}: {probability}, using default: 100%{Style.RESET_ALL}")
                        behaviors[behavior] = 100
            
            # Ensure device_info field exists
            if 'device_info' not in account:
                print(f"{Fore.YELLOW}⚠️ No device info specified for account {account.get('email', 'unknown')}, using defaults{Style.RESET_ALL}")
                account['device_info'] = {
                    'device': 'sdk_gphone64_arm64',
                    'hardware_id': '66097399e0a69560',
                    'manufacturer': 'Google',
                    'install_id': '68e6437e05c84e57b9cf0833d28dd1c'
                }
            else:
                # Ensure all device info fields exist
                device_info = account['device_info']
                default_device_info = {
                    'device': 'sdk_gphone64_arm64',
                    'hardware_id': '66097399e0a69560',
                    'manufacturer': 'Google',
                    'install_id': '68e6437e05c84e57b9cf0833d28dd1c'
                }
                
                # Add missing device info fields with defaults
                for field, default in default_device_info.items():
                    if field not in device_info:
                        print(f"{Fore.YELLOW}⚠️ Missing device info '{field}' for account {account.get('email', 'unknown')}, using default: {default}{Style.RESET_ALL}")
                        device_info[field] = default
        
        print(f"{Fore.GREEN}✅ Loaded {len(accounts)} accounts from {file_path}{Style.RESET_ALL}")
        return accounts
    
    except Exception as e:
        print(f"{Fore.RED}❌ Error loading accounts: {str(e)}{Style.RESET_ALL}")
        return []

def load_comments(file_path: str = COMMENTS_FILE) -> List[str]:
    """
    Load comments from a JSON file.
    
    Args:
        file_path (str): Path to the JSON file containing comments
        
    Returns:
        List[str]: List of comments to use for pin interactions
    """
    try:
        if not os.path.exists(file_path):
            print(f"{Fore.YELLOW}⚠️ Comments file not found: {file_path}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Creating sample comments file...{Style.RESET_ALL}")
            
            # Create a sample comments file
            sample_comments = [
                "Great pin! 👍",
                "Love this! ❤️",
                "Amazing! 🔥",
                "Beautiful! ✨",
                "Thanks for sharing! 🙏"
            ]
            
            with open(file_path, 'w') as f:
                json.dump(sample_comments, f, indent=2)
            
            print(f"{Fore.GREEN}✅ Created sample comments file: {file_path}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}⚠️ Please edit the file with your actual comments before running.{Style.RESET_ALL}")
            return []
        
        with open(file_path, 'r') as f:
            comments = json.load(f)
        
        print(f"{Fore.GREEN}✅ Loaded {len(comments)} comments from {file_path}{Style.RESET_ALL}")
        return comments
    
    except Exception as e:
        print(f"{Fore.RED}❌ Error loading comments: {str(e)}{Style.RESET_ALL}")
        return []

def main():
    """
    Main function to run the Pinterest automation.
    """
    print(f"{Fore.CYAN}🚀 Starting Pinterest Automation{Style.RESET_ALL}")
    
    # Initialize proxy manager
    proxy_manager = ProxyManager()
    
    # Load accounts and comments
    accounts = load_accounts()
    if not accounts:
        print(f"{Fore.RED}❌ No accounts loaded. Exiting.{Style.RESET_ALL}")
        return
    
    # Mark the first account
    if accounts:
        accounts[0]['is_first_account'] = True
    
    # Assign proxies to accounts
    accounts = proxy_manager.assign_proxies_to_accounts(accounts)
    
    # Print proxy status
    proxy_manager.print_proxy_status()
    
    comments = load_comments()
    if not comments:
        print(f"{Fore.YELLOW}⚠️ No comments loaded. Using default comments.{Style.RESET_ALL}")
        comments = ["Great pin! 👍", "Love this! ❤️", "Amazing! 🔥"]
    
    # Create the automation instance
    automation = PinterestAutomationWithMixins(
        accounts=accounts,
        comments=comments,
        num_pins_to_process=NUM_PINS_TO_PROCESS,
        max_workers=MAX_WORKERS
    )
    
    # Run the automation
    print(f"{Fore.CYAN}🔄 Running automation for {len(accounts)} accounts...{Style.RESET_ALL}")
    start_time = time.time()
    results = automation.run()
    end_time = time.time()
    
    # Print summary
    success_count = sum(1 for r in results if r['status'] == 'active')
    print(f"\n{Fore.CYAN}📊 Final Summary:{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Total accounts: {Fore.YELLOW}{len(accounts)}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}Successful: {Fore.YELLOW}{success_count}{Style.RESET_ALL}")
    print(f"{Fore.RED}Failed: {Fore.YELLOW}{len(accounts) - success_count}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Total time: {Fore.YELLOW}{end_time - start_time:.2f} seconds{Style.RESET_ALL}")
    
    print(f"\n{Fore.GREEN}✅ Pinterest Automation completed!{Style.RESET_ALL}")

if __name__ == "__main__":
    main() 