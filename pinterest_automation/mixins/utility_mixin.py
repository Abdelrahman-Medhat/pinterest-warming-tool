import time
import os
import random
from datetime import datetime
from typing import Dict, Any, List, Optional
from colorama import Fore, Style
import json

class UtilityMixin:
    """
    Mixin for utility functions used across the Pinterest automation.
    """
    
    def get_current_time(self) -> int:
        """Get current time in seconds since epoch."""
        return int(time.time())
    
    def get_last_rotation_time(self) -> int:
        """Get the timestamp of the last rotation."""
        if os.path.exists('last_rotation.txt'):
            with open('last_rotation.txt', 'r') as f:
                try:
                    return int(f.read().strip())
                except:
                    return 0
        return 0
    
    def update_last_rotation_time(self):
        """Update the last rotation timestamp."""
        with open('last_rotation.txt', 'w') as f:
            f.write(str(self.get_current_time()))
    
    def get_last_ip(self) -> Optional[str]:
        """Get the last used IP."""
        if os.path.exists('current_ip.txt'):
            with open('current_ip.txt', 'r') as f:
                return f.read().strip()
        return None
    
    def save_current_ip(self, ip: str):
        """Save the current IP."""
        with open('current_ip.txt', 'w') as f:
            f.write(ip)
    
    def human_delay(self, action: str = "default", min_seconds: float = 3, max_seconds: float = 8) -> float:
        """
        Add a random human-like delay and log it.
        
        Args:
            action (str): Description of the action being delayed
            min_seconds (float): Minimum delay in seconds
            max_seconds (float): Maximum delay in seconds
            
        Returns:
            float: The actual delay time used
        """
        delay = random.uniform(min_seconds, max_seconds)
        print(f"{Fore.YELLOW}⏳ Waiting {delay:.1f} seconds before {action}{Style.RESET_ALL}")
        time.sleep(delay)
        return delay
    
    def save_data(self, data: dict, prefix: str = "pinterest_data") -> str:
        """
        Save data to a JSON file.
        
        Args:
            data (dict): Data to save
            prefix (str): Prefix for the filename
            
        Returns:
            str: Path to the saved file
        """
        # Create a results directory if it doesn't exist
        os.makedirs("results", exist_ok=True)
        
        # Generate timestamp for unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON data
        filename = f"results/{prefix}_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return filename
    
    def save_session_to_file(self, user_data: dict, access_token: str, prefix: str = "pinterest_session") -> str:
        """
        Save Pinterest session data to a file.
        
        Args:
            user_data (dict): User data from successful login
            access_token (str): Access token from successful login
            prefix (str): Prefix for the filename
            
        Returns:
            str: Path to the saved session file
        """
        session_data = {
            'user_data': user_data,
            'access_token': access_token,
            'timestamp': datetime.now().isoformat()
        }
        
        # Create a sessions directory if it doesn't exist
        os.makedirs("sessions", exist_ok=True)
        
        # Get email from user_data and clean it for filename
        email = user_data.get('email', '').replace('@', '_at_').replace('.', '_')
        
        # Save session data with email in filename
        filename = f"sessions/{prefix}_{email}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        return filename
    
    def load_session_from_file(self, filename: str) -> tuple:
        """
        Load Pinterest session data from a file.
        
        Args:
            filename (str): Path to the session file
            
        Returns:
            tuple: (user_data, access_token)
        """
        with open(filename, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
        return session_data['user_data'], session_data['access_token'] 