import random
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from colorama import Fore, Style

class PinInteractionMixin:
    """
    Mixin for pin interaction operations like liking, commenting, and saving pins.
    """
    
    def human_delay(self, action_description: str, min_delay: float, max_delay: float) -> float:
        """
        Simulate a human-like delay with a random duration.
        
        Args:
            action_description (str): Description of the action being delayed
            min_delay (float): Minimum delay in seconds
            max_delay (float): Maximum delay in seconds
            
        Returns:
            float: The actual delay time in seconds
        """
        delay = random.uniform(min_delay, max_delay)
        print(f"{Fore.YELLOW}⏳ Waiting {delay:.1f} seconds before {action_description}...{Style.RESET_ALL}")
        time.sleep(delay)
        return delay
    
    def like_pin(self, pinterest_api, pin_id: str, full_name: str) -> Dict[str, Any]:
        """
        Like a pin with human-like behavior.
        
        Args:
            pinterest_api: Pinterest API instance
            pin_id (str): ID of the pin to like
            full_name (str): User's full name for logging
            
        Returns:
            Dict[str, Any]: Result of the like operation
        """
        result = {
            'success': False,
            'error': None,
            'timing': {
                'start_time': datetime.now().isoformat(),
                'end_time': None,
                'total_time': 0
            }
        }
        
        try:
            # Add random delay before liking
            like_delay = self.human_delay("liking the pin", 2, 5)
            
            print(f"{Fore.CYAN}❤️  Reacting to pin {Fore.YELLOW}{pin_id}{Fore.CYAN} as {Fore.YELLOW}{full_name}{Style.RESET_ALL}")
            
            # Like the pin
            reaction_data = pinterest_api.react_to_pin(pin_id)
            
            # Track pin reaction event
            print(f"{Fore.YELLOW}📤 Sending PinReaction tracking event for pin {pin_id}...{Style.RESET_ALL}")
            try:
                tracking_response = pinterest_api.track_custom_event(
                    event_name="PinReaction",
                    event_data={
                        "PinID": pin_id,
                        "ReactionType": "like",
                        "Source": "closeup"
                    },
                    user_id=pinterest_api.get_user_data().get('id')
                )
                print(f"{Fore.GREEN}✅ PinReaction tracking successful {Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.YELLOW}⚠️ PinReaction tracking failed: {str(e)}{Style.RESET_ALL}")
            
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
            print(f"{Fore.YELLOW}⚠️ Error liking pin: {str(e)}{Style.RESET_ALL}")
        
        finally:
            result['timing']['end_time'] = datetime.now().isoformat()
            end_time = datetime.fromisoformat(result['timing']['end_time'])
            start_time = datetime.fromisoformat(result['timing']['start_time'])
            result['timing']['total_time'] = (end_time - start_time).total_seconds()
        
        return result
    
    def save_pin(self, pinterest_api, pin_id: str, pin: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save a pin with human-like behavior.
        
        Args:
            pinterest_api: Pinterest API instance
            pin_id (str): ID of the pin to save
            pin (Dict[str, Any]): Pin data
            
        Returns:
            Dict[str, Any]: Result of the save operation
        """
        result = {
            'success': False,
            'error': None,
            'timing': {
                'start_time': datetime.now().isoformat(),
                'end_time': None,
                'total_time': 0
            }
        }
        
        try:
            # Add random delay before saving
            save_delay = self.human_delay("preparing to save pin", 1, 3)
            
            print(f"{Fore.CYAN}📌 Saving pin {Fore.YELLOW}{pin_id}{Style.RESET_ALL}")
            
            # Save the pin
            save_result = pinterest_api.save_pin(pin_id)
            
            # Track save_pin event
            print(f"{Fore.YELLOW}📤 Sending save_pin tracking event...{Style.RESET_ALL}")
            try:
                tracking_response = pinterest_api.track_custom_event(
                    event_name="save_pin",
                    event_data={
                        "category": "engagement",
                        "action": "save_pin",
                        "label": pin.get('category', 'uncategorized'),
                        "value": 1
                    },
                    user_id=pinterest_api.get_user_data().get('id')
                )
                print(f"{Fore.GREEN}✅ save_pin tracking successful {Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.YELLOW}⚠️ save_pin tracking failed: {str(e)}{Style.RESET_ALL}")
            
            result['success'] = True
            print(f"{Fore.GREEN}✨ Pin saved successfully{Style.RESET_ALL}")
            
        except Exception as e:
            result['error'] = str(e)
            print(f"{Fore.YELLOW}⚠️ Error saving pin: {str(e)}{Style.RESET_ALL}")
        
        finally:
            result['timing']['end_time'] = datetime.now().isoformat()
            end_time = datetime.fromisoformat(result['timing']['end_time'])
            start_time = datetime.fromisoformat(result['timing']['start_time'])
            result['timing']['total_time'] = (end_time - start_time).total_seconds()
        
        return result
    
    def comment_on_pin(self, pinterest_api, pin: Dict[str, Any], comment_text: str, full_name: str) -> Dict[str, Any]:
        """
        Comment on a pin with human-like behavior.
        
        Args:
            pinterest_api: Pinterest API instance
            pin (Dict[str, Any]): Pin data
            comment_text (str): Text of the comment
            full_name (str): User's full name for logging
            
        Returns:
            Dict[str, Any]: Result of the comment operation
        """
        result = {
            'success': False,
            'error': None,
            'timing': {
                'start_time': datetime.now().isoformat(),
                'end_time': None,
                'total_time': 0
            }
        }
        
        try:
            # Simulate typing delay based on comment length
            typing_delay = len(comment_text) * random.uniform(0.1, 0.3)  # Simulate typing speed
            comment_delay = self.human_delay(f"typing comment: {comment_text}", typing_delay, typing_delay + 2)
            
            print(f"{Fore.CYAN}💬 Commenting on pin {Fore.YELLOW}{pin['id']}{Fore.CYAN} as {Fore.YELLOW}{full_name}{Fore.CYAN}: {Fore.WHITE}{comment_text}{Style.RESET_ALL}")
            
            # Post the comment
            comment_data = pinterest_api.post_comment(pin_data=pin, text=comment_text)
            
            # Track comment event
            print(f"{Fore.YELLOW}📤 Sending PinComment tracking event for pin {pin['id']}...{Style.RESET_ALL}")
            try:
                tracking_response = pinterest_api.track_custom_event(
                    event_name="PinComment",
                    event_data={
                        "PinID": pin['id'],
                        "CommentLength": len(comment_text),
                        "Source": "closeup"
                    },
                    user_id=pinterest_api.get_user_data().get('id')
                )
                print(f"{Fore.GREEN}✅ PinComment tracking successful {Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.YELLOW}⚠️ PinComment tracking failed: {str(e)}{Style.RESET_ALL}")
            
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
            print(f"{Fore.YELLOW}⚠️ Error commenting on pin: {str(e)}{Style.RESET_ALL}")
        
        finally:
            result['timing']['end_time'] = datetime.now().isoformat()
            end_time = datetime.fromisoformat(result['timing']['end_time'])
            start_time = datetime.fromisoformat(result['timing']['start_time'])
            result['timing']['total_time'] = (end_time - start_time).total_seconds()
        
        return result
    
    def open_pin(self, pinterest_api, pin_id: str, full_name: str) -> Dict[str, Any]:
        """
        Open a pin with human-like behavior.
        
        Args:
            pinterest_api: Pinterest API instance
            pin_id (str): ID of the pin to open
            full_name (str): User's full name for logging
            
        Returns:
            Dict[str, Any]: Result of the open operation
        """
        result = {
            'success': False,
            'error': None,
            'timing': {
                'start_time': datetime.now().isoformat(),
                'end_time': None,
                'total_time': 0,
                'load_time': 0,
                'view_time': 0
            }
        }
        
        try:
            print(f"{Fore.CYAN}👁️  Opening pin {Fore.YELLOW}{pin_id}{Fore.CYAN} as {Fore.YELLOW}{full_name}{Style.RESET_ALL}")
            
            # Simulate opening the pin
            open_result = pinterest_api.simulate_pin_open(pin_id)
            
            # Track pin view event
            print(f"{Fore.YELLOW}📤 Sending PinView tracking event for pin {pin_id}...{Style.RESET_ALL}")
            try:
                tracking_response = pinterest_api.track_custom_event(
                    event_name="PinView",
                    event_data={
                        "PinID": pin_id,
                        "ViewSource": "home_feed",
                        "ViewType": "closeup",
                        "TimeSpent": open_result['timing']['total_time']
                    },
                    user_id=pinterest_api.get_user_data().get('id')
                )
                print(f"{Fore.GREEN}✅ PinView tracking successful {Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.YELLOW}⚠️ PinView tracking failed: {str(e)}{Style.RESET_ALL}")
            
            result['success'] = True
            result['timing']['load_time'] = open_result['timing'].get('load_time', 0)
            result['timing']['view_time'] = open_result['timing'].get('view_time', 0)
            
            if result['success']:
                print(f"{Fore.GREEN}✨ Pin opened successfully (Load: {result['timing']['load_time']:.1f}s, View: {result['timing']['view_time']:.1f}s){Style.RESET_ALL}")
            
        except Exception as e:
            result['error'] = str(e)
            print(f"{Fore.YELLOW}⚠️ Error opening pin: {str(e)}{Style.RESET_ALL}")
        
        finally:
            result['timing']['end_time'] = datetime.now().isoformat()
            end_time = datetime.fromisoformat(result['timing']['end_time'])
            start_time = datetime.fromisoformat(result['timing']['start_time'])
            result['timing']['total_time'] = (end_time - start_time).total_seconds()
        
        return result 