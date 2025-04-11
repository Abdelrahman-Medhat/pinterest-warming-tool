import os
import time
from typing import Dict, Any, List, Optional
from colorama import Fore, Style
import json
from pinterest_api.exceptions import (
    EmailNotFoundError,
    LoginFailedError,
    InvalidResponseError,
    PinterestAuthError,
    IncorrectPasswordError,
    AuthenticationError
)
from datetime import datetime
import random
from .pin_interaction_mixin import PinInteractionMixin
import config
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class AccountProcessorMixin(PinInteractionMixin):
    def __init__(self, num_pins_to_process: int = 10):
        self.num_pins_to_process = num_pins_to_process
    """
    Mixin for account-related operations.
    """
    
    def login_account(self, api: Any, email: str, password: str, proxy: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Login to a Pinterest account.
        
        Args:
            api (Any): Pinterest API instance
            email (str): Account email
            password (str): Account password
            proxy (Optional[Dict[str, str]]): Proxy configuration
            
        Returns:
            Dict[str, Any]: Login result containing user data and access token
        """
        result = {
            'success': False,
            'error': None,
            'user_data': None,
            'access_token': None
        }
        
        try:
            print(f"{Fore.CYAN}🔑 Logging in to account: {email}{Style.RESET_ALL}")
            
            # Set credentials
            api.email = email
            api.password = password
            
            # Set device info if available
            if hasattr(api, 'account') and 'device_info' in api.account:
                print(f"{Fore.CYAN}📱 Setting device info for {email}{Style.RESET_ALL}")
                api.set_device_info(api.account['device_info'])
            
            # Use the session file path - store at project root
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
            session_dir = os.path.join(project_root, "sessions")
            os.makedirs(session_dir, exist_ok=True)
            session_file = os.path.join(session_dir, f"{email.replace('@', '_at_').replace('.', '_')}.json")
            
            # First check if we have a valid session file
            if os.path.exists(session_file):
                print(f"{Fore.YELLOW}📂 Found existing session file for {email}{Style.RESET_ALL}")
                try:
                    # Load session directly
                    with open(session_file, 'r') as f:
                        session_data = json.load(f)
                    
                    # Set user data and access token directly on the API instance
                    if 'user_data' in session_data and 'access_token' in session_data:
                        print(f"{Fore.CYAN}🔄 Loading session data from file...{Style.RESET_ALL}")
                        
                        # Ensure API instance has these attributes
                        if not hasattr(api, '_user_data'):
                            api._user_data = None
                        if not hasattr(api, '_access_token'):
                            api._access_token = None
                            
                        # Set the data directly on the API instance
                        api._user_data = session_data['user_data']
                        api._access_token = session_data['access_token']
                        
                        # Set up auth header
                        api.session.headers['Authorization'] = f"Bearer {session_data['access_token']}"
                        
                        # Update result
                        result['user_data'] = session_data['user_data']
                        result['access_token'] = session_data['access_token']
                        result['success'] = True
                        
                        print(f"{Fore.GREEN}✅ Successfully loaded session from file for: {email}{Style.RESET_ALL}")
                        return result
                except Exception as e:
                    print(f"{Fore.YELLOW}⚠️ Error loading session file: {str(e)}, will create new session{Style.RESET_ALL}")
            
            # Use get_or_create_session which handles session loading, validation, and creation
            try:
                print(f"{Fore.CYAN}🔐 Getting or creating session...{Style.RESET_ALL}")
                # This will either load a valid session or create a new one by logging in
                session_data = api.get_or_create_session(session_file)
                
                # Update result with session data
                result['user_data'] = session_data.get('user_data')
                result['access_token'] = session_data.get('access_token')
                result['success'] = True
                
                print(f"{Fore.GREEN}✅ Successfully logged in to account: {email}{Style.RESET_ALL}")
                
            except EmailNotFoundError as e:
                result['error'] = f"Email not found: {str(e)}"
                print(f"{Fore.RED}❌ {result['error']}{Style.RESET_ALL}")
            except IncorrectPasswordError:
                result['error'] = "Incorrect password"
                print(f"{Fore.RED}❌ {result['error']}{Style.RESET_ALL}")
            except LoginFailedError as e:
                result['error'] = f"Login failed: {str(e)}"
                print(f"{Fore.RED}❌ {result['error']}{Style.RESET_ALL}")
            except AuthenticationError as e:
                result['error'] = f"Authentication error: {str(e)}"
                print(f"{Fore.RED}❌ {result['error']}{Style.RESET_ALL}")
            except Exception as e:
                result['error'] = f"Error during session creation: {str(e)}"
                print(f"{Fore.RED}❌ {result['error']}{Style.RESET_ALL}")
            
        except Exception as e:
            result['error'] = str(e)
            print(f"{Fore.RED}❌ Error logging in to account: {email} - {str(e)}{Style.RESET_ALL}")
        
        return result
    
    def visit_pin_link(self, pin: Dict[str, Any], full_name: str, api: Any) -> Dict[str, Any]:
        """
        Visit a pin's link in a browser with human-like behavior.
        
        Args:
            pin (Dict[str, Any]): Pin data containing the link
            full_name (str): User's full name for logging
            api (Any): Pinterest API instance for tracking
            
        Returns:
            Dict[str, Any]: Visit result data
        """
        result = {
            'success': False,
            'error': None,
            'timing': {
                'start_time': datetime.now().isoformat(),
                'end_time': None,
                'total_time': 0,
                'scroll_time': 0,
                'stats': {
                    'initial_wait': 0,
                    'scroll_time': 0,
                    'final_wait': 0
                }
            }
        }
        
        link = pin.get('link')
        if not link:
            result['error'] = "No link found in pin data"
            return result
        
        # Track clickthrough start event if api is provided
        if api:
            print(f"{Fore.CYAN}📤 Sending clickthrough start event for {link}...{Style.RESET_ALL}")
            try:
                api.track_clickthrough(
                    url=link,
                    pin_id=pin['id'],
                    is_start=True
                )
            except Exception as e:
                print(f"{Fore.YELLOW}⚠️ Error tracking clickthrough start: {str(e)}{Style.RESET_ALL}")

        driver = None
        try:
            # Check if pin link visits are enabled
            if not config.ENABLE_PIN_LINK_VISITS:
                print(f"{Fore.YELLOW}⚠️ Pin link visits are disabled. Skipping browser visit for pin {pin['id']}{Style.RESET_ALL}")
                
                # Simulate a reasonable visit duration for tracking purposes
                simulated_duration = random.uniform(30, 60)
                print(f"{Fore.CYAN}⏱️ Simulating {simulated_duration:.1f} seconds visit duration{Style.RESET_ALL}")
                
                # Wait for a short time to simulate the visit
                time.sleep(2)
                
                # Track clickthrough end event
                if api:
                    print(f"{Fore.CYAN}📤 Sending clickthrough end event for {link}...{Style.RESET_ALL}")
                    try:
                        api.track_clickthrough(
                            url=link,
                            pin_id=pin['id'],
                            is_start=False,
                            duration=int(simulated_duration)
                        )
                    except Exception as e:
                        print(f"{Fore.YELLOW}⚠️ Error tracking clickthrough end: {str(e)}{Style.RESET_ALL}")
                
                # Track experience event
                if api:
                    print(f"{Fore.CYAN}📤 Sending experience event for pin {pin['id']}...{Style.RESET_ALL}")
                    try:
                        self.track_experience(
                            api=api,
                            pin_id=pin['id'],
                            did_pin_clickthrough=True,
                            creator_username=pin.get('creator_username', '')
                        )
                    except Exception as e:
                        print(f"{Fore.YELLOW}⚠️ Error tracking experience: {str(e)}{Style.RESET_ALL}")
                
                # Update result with simulated timing
                result['timing']['end_time'] = datetime.now().isoformat()
                end_time = datetime.fromisoformat(result['timing']['end_time'])
                start_time = datetime.fromisoformat(result['timing']['start_time'])
                result['timing']['total_time'] = (end_time - start_time).total_seconds()
                result['timing']['stats']['scroll_time'] = simulated_duration
                result['success'] = True
                
                print(f"{Fore.GREEN}✨ Successfully simulated link visit for {simulated_duration:.1f} seconds{Style.RESET_ALL}")
                return result

            # Check if headless mode is enabled
            if config.HEADLESS_BROWSER:
                print(f"{Fore.YELLOW}👻 Running browser in headless mode{Style.RESET_ALL}")
                chrome_options = webdriver.ChromeOptions()
                chrome_options.add_argument("--headless")
            else:
                print(f"{Fore.CYAN}👁️ Running browser in visible mode{Style.RESET_ALL}")
                chrome_options = webdriver.ChromeOptions()

            # Set up Chrome options
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-infobars")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-popup-blocking")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")

            driver = webdriver.Chrome(options=chrome_options)
            
            # Visit the link and wait for page load
            driver.get(link)
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                print(f"{Fore.GREEN}✨ Page loaded successfully{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}⚠️ Page load timeout, but continuing: {str(e)}{Style.RESET_ALL}")
            
            # Random initial wait to simulate reading the initial view
            initial_wait = random.uniform(2, 4)
            print(f"{Fore.YELLOW}👀 Reading initial view for {initial_wait:.1f} seconds{Style.RESET_ALL}")
            time.sleep(initial_wait)
            result['timing']['stats']['initial_wait'] = initial_wait
            
            # Try to get page title
            try:
                page_title = driver.title
                print(f"{Fore.CYAN}📑 Page title: {Fore.WHITE}{page_title}{Style.RESET_ALL}")
            except Exception:
                pass
            
            # Scroll like a human
            scroll_time = random.uniform(20, 40)  # Random scroll time between 20-40 seconds
            print(f"{Fore.CYAN}🖱️ Starting page interaction for {scroll_time:.1f} seconds{Style.RESET_ALL}")
            
            # Perform human-like scrolling
            start_time = time.time()
            last_scroll = 0
            scroll_count = 0
            
            try:
                while time.time() - start_time < scroll_time:
                    # Get current scroll height
                    scroll_height = driver.execute_script("return document.documentElement.scrollHeight")
                    viewport_height = driver.execute_script("return window.innerHeight")
                    
                    # Calculate a random scroll amount (between 100 and viewport height)
                    scroll_amount = random.randint(100, viewport_height)
                    
                    # Don't scroll past the bottom
                    new_scroll = min(last_scroll + scroll_amount, scroll_height - viewport_height)
                    
                    # Scroll smoothly with random speed
                    scroll_behavior = random.choice(['smooth', 'auto'])  # Mix smooth and instant scrolling
                    driver.execute_script(f"window.scrollTo({{top: {new_scroll}, behavior: '{scroll_behavior}'}})")
                    
                    scroll_count += 1
                    print(f"{Fore.YELLOW}⏳ Scroll {scroll_count}: {scroll_amount}px ({scroll_behavior}){Style.RESET_ALL}")
                    
                    # Random pause between scrolls (0.5 to 2 seconds)
                    pause_time = random.uniform(0.5, 2)
                    time.sleep(pause_time)
                    
                    # Occasionally scroll back up a little (20% chance)
                    if random.random() < 0.2:
                        up_amount = random.randint(100, 300)
                        new_scroll = max(0, new_scroll - up_amount)
                        driver.execute_script(f"window.scrollTo({{top: {new_scroll}, behavior: 'smooth'}})")
                        print(f"{Fore.YELLOW}⏫ Scrolling back up {up_amount}px{Style.RESET_ALL}")
                        time.sleep(random.uniform(0.5, 1.5))
                    
                    # Occasionally pause for longer to simulate reading (10% chance)
                    if random.random() < 0.1:
                        read_time = random.uniform(2, 4)
                        print(f"{Fore.YELLOW}📖 Pausing to read for {read_time:.1f}s{Style.RESET_ALL}")
                        time.sleep(read_time)
                    
                    last_scroll = new_scroll
                    
                    # If we've reached the bottom, scroll back up partway and continue
                    if new_scroll >= (scroll_height - viewport_height - 100):
                        print(f"{Fore.YELLOW}🔄 Reached bottom, scrolling back up...{Style.RESET_ALL}")
                        new_scroll = random.randint(int(scroll_height * 0.2), int(scroll_height * 0.4))
                        driver.execute_script(f"window.scrollTo({{top: {new_scroll}, behavior: 'smooth'}})")
                        time.sleep(random.uniform(1, 2))
                        last_scroll = new_scroll
            except Exception as e:
                print(f"{Fore.RED}⚠️ Error during scrolling: {str(e)}{Style.RESET_ALL}")
            
            result['timing']['stats']['scroll_time'] = scroll_time
            
            # Random final wait before closing
            final_wait = random.uniform(2, 5)
            print(f"{Fore.YELLOW}👋 Final view before closing for {final_wait:.1f} seconds{Style.RESET_ALL}")
            time.sleep(final_wait)
            result['timing']['stats']['final_wait'] = final_wait
            
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
            print(f"{Fore.RED}❌ Error visiting link: {str(e)}{Style.RESET_ALL}")
        
        finally:
            if driver:
                try:
                    driver.quit()
                    print(f"{Fore.GREEN}✨ Browser closed successfully{Style.RESET_ALL}")
                except Exception:
                    print(f"{Fore.RED}⚠️ Error closing browser{Style.RESET_ALL}")
            
            result['timing']['end_time'] = datetime.now().isoformat()
            end_time = datetime.fromisoformat(result['timing']['end_time'])
            start_time = datetime.fromisoformat(result['timing']['start_time'])
            result['timing']['total_time'] = (end_time - start_time).total_seconds()
            
            # Track clickthrough end event if api is provided
            if api:
                print(f"{Fore.CYAN}📤 Sending clickthrough end event for {link}...{Style.RESET_ALL}")
                try:
                    api.track_clickthrough(
                        url=link,
                        pin_id=pin['id'],
                        is_start=False,
                        duration=int(result['timing']['total_time'])
                    )
                    
                    # Track experience event after visiting the link
                    print(f"{Fore.CYAN}📤 Sending experience event for pin {pin['id']}...{Style.RESET_ALL}")
                    try:
                        self.track_experience(
                            api=api,
                            pin_id=pin['id'],
                            did_pin_clickthrough=True,
                            creator_username=pin.get('creator_username', '')
                        )
                    except Exception as e:
                        print(f"{Fore.YELLOW}⚠️ Error tracking experience: {str(e)}{Style.RESET_ALL}")
                except Exception as e:
                    print(f"{Fore.YELLOW}⚠️ Error tracking clickthrough end: {str(e)}{Style.RESET_ALL}")
            
            if result['success']:
                total_interaction = result['timing']['stats']['initial_wait'] + \
                                  result['timing']['stats']['scroll_time'] + \
                                  result['timing']['stats']['final_wait']
                print(f"{Fore.GREEN}✨ Successfully visited link for {total_interaction:.1f} seconds total{Style.RESET_ALL}")
                print(f"   👀 Initial view: {result['timing']['stats']['initial_wait']:.1f}s")
                print(f"   📜 Scrolling: {result['timing']['stats']['scroll_time']:.1f}s")
                print(f"   👋 Final view: {result['timing']['stats']['final_wait']:.1f}s")
        
        return result
    
    def process_account(self, account: Dict[str, Any], api: Any, result: Dict[str, Any] = None, retry_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a single account with all interactions.
        
        Args:
            account (Dict[str, Any]): Account dictionary with credentials and proxy info
            api (Any): Pinterest API instance
            result (Dict[str, Any], optional): Result dictionary to update
            retry_params (Dict[str, Any], optional): Parameters for retry logic
            
        Returns:
            Dict[str, Any]: Result of account processing
        """
        # Initialize result structure if not provided
        if result is None:
            result = {}
            
        try:
            # Get account behaviors
            account_behaviors = account.get('behaviors', {})
            
            # Initialize result structure
            result.update({
                'account_email': account['email'],
                'account_behaviors': account_behaviors,  # Add account behaviors to result
                'status': 'success',  # Start with success status
                'pins_processed': 0,
                'total_pins': 0,
                'total_actions': 0,
                'successful_actions': 0,
                'failed_actions': 0,
                'errors': [],
                'timing': {
                    'total_delays': 0,
                    'total_processing_time': 0
                },
                'actions_results': []
            })
            
            # Get user data if not already in result
            if 'user_data' not in result or not result['user_data']:
                try:
                    user_data = api.get_user_data()
                    if user_data:
                        result['user_data'] = user_data
                        print(f"{Fore.GREEN}✅ Retrieved user data for {account['email']}{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.YELLOW}⚠️ Could not retrieve user data for {account['email']}{Style.RESET_ALL}")
                        result['status'] = 'failed'  # Mark as failed if no user data
                except Exception as e:
                    print(f"{Fore.YELLOW}⚠️ Error getting user data: {str(e)}{Style.RESET_ALL}")
                    result['status'] = 'failed'  # Mark as failed on error
            
            # Get full name from user data
            full_name = result.get('user_data', {}).get('full_name', 'Unknown User')
            print(f"{Fore.CYAN}👤 Processing account for user: {full_name}{Style.RESET_ALL}")
            
            # Print account behaviors
            print(f"{Fore.CYAN}⚙️ Account behaviors for {account['email']}:{Style.RESET_ALL}")
            for behavior, probability in account_behaviors.items():
                status = f"{Fore.GREEN}{probability}%{Style.RESET_ALL}"
                print(f"  - {behavior}: {status}")
            
            # Get pins with links
            pins_with_links = self.get_pins_with_links(api, result)
            if not pins_with_links:
                result['status'] = 'failed'
                result['errors'].append("No pins with links found")
                return result
                
            result['total_pins'] = len(pins_with_links)
            
            # Process each pin
            for pin in pins_with_links:
                # Extract pin ID from pin data
                pin_id = pin.get('id')
                if not pin_id:
                    print(f"{Fore.YELLOW}⚠️ Skipping pin without ID{Style.RESET_ALL}")
                    continue
                            
                # Process the pin using the extracted method
                pin_result = self._process_single_pin(pin, result, pin_id, api)
                
                # Add pin result to actions_results
                result['actions_results'].append(pin_result)
                
                # Update counters based on actual actions performed
                result['pins_processed'] += 1
                
                # Count successful and failed actions
                successful_actions = sum([
                    pin_result['open_success'],
                    pin_result['like_success'],
                    pin_result['save_success'],
                    pin_result['comment_success'],
                    pin_result.get('link_visit_success', False)
                ])
                
                failed_actions = sum([
                    not pin_result['open_success'] if pin_result.get('open_attempted', False) else 0,
                    not pin_result['like_success'] if pin_result.get('like_attempted', False) else 0,
                    not pin_result['save_success'] if pin_result.get('save_attempted', False) else 0,
                    not pin_result['comment_success'] if pin_result.get('comment_attempted', False) else 0,
                    not pin_result.get('link_visit_success', True) if pin.get('link') and pin_result.get('link_visit_attempted', False) else 0
                ])
                
                result['successful_actions'] += successful_actions
                result['failed_actions'] += failed_actions
                result['total_actions'] += successful_actions + failed_actions
                
                # Add any errors from pin processing
                result['errors'].extend(pin_result['errors'])
            
            # Update status based on results
            if result['pins_processed'] > 0 and result['successful_actions'] > 0:
                result['status'] = 'success'
                print(f"{Fore.GREEN}✅ Account processing completed successfully{Style.RESET_ALL}")
            else:
                result['status'] = 'failed'
                print(f"{Fore.RED}❌ Account processing failed - no successful actions{Style.RESET_ALL}")
            
            # Calculate success rate
            if result['total_actions'] > 0:
                result['success_rate'] = (result['successful_actions'] / result['total_actions']) * 100
            else:
                result['success_rate'] = 0
            
            # Print final status
            print(f"{Fore.CYAN}📊 Account processing result for {account['email']}:{Style.RESET_ALL}")
            print(f"  Status: {Fore.GREEN if result['status'] == 'success' else Fore.RED}{result['status']}{Style.RESET_ALL}")
            print(f"  Pins processed: {result['pins_processed']}/{result['total_pins']}")
            print(f"  Success rate: {result['success_rate']:.1f}%")
            
            # Ensure status is properly set for the final summary
            if result['pins_processed'] > 0 and result['successful_actions'] > 0:
                result['status'] = 'success'
            
            return result
            
        except Exception as e:
            error_msg = f"Error processing account: {str(e)}"
            print(f"{Fore.RED}❌ {error_msg}{Style.RESET_ALL}")
            result['status'] = 'failed'
            result['errors'].append(error_msg)
            return result
    
    def process_accounts(self, pinterest_api, accounts: List[Dict[str, str]], proxies: List[Dict[str, str]], max_workers: int = 1) -> List[Dict[str, Any]]:
        """
        Process multiple accounts in parallel or sequentially.
        
        Args:
            pinterest_api: Pinterest API instance
            accounts (List[Dict[str, str]]): List of account credentials
            proxies (List[Dict[str, str]]): List of proxy configurations
            max_workers (int): Maximum number of parallel workers
            
        Returns:
            List[Dict[str, Any]]: List of processing results
        """
        results = []
        
        if max_workers > 1 and len(proxies) > 1:
            # Process accounts in parallel
            from concurrent.futures import ThreadPoolExecutor
            
            def process_with_proxy(account_proxy_pair):
                account, proxy = account_proxy_pair
                return self.process_account(account, pinterest_api)
            
            # Create account-proxy pairs
            account_proxy_pairs = []
            for i, account in enumerate(accounts):
                proxy = proxies[i % len(proxies)]
                account_proxy_pairs.append((account, proxy))
            
            # Process in parallel
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                results = list(executor.map(process_with_proxy, account_proxy_pairs))
            
        else:
            # Process accounts sequentially
            for i, account in enumerate(accounts):
                proxy = proxies[i % len(proxies)] if proxies else None
                result = self.process_account(account, pinterest_api)
                results.append(result)
        
        # Debug output to check status values
        print(f"\n{Fore.YELLOW}🔍 DEBUG: Checking account statuses:{Style.RESET_ALL}")
        for i, r in enumerate(results):
            print(f"  Account {i+1}: email = '{r.get('account_email', 'unknown')}'")
            print(f"  Account {i+1} raw status: {r.get('status')}")
            print(f"  Account {i+1} pins_processed: {r.get('pins_processed', 0)}")
            print(f"  Account {i+1} successful_actions: {r.get('successful_actions', 0)}")
        
        # Manually calculate success/failure based on actual results
        successful = 0
        failed = 0
        
        for i, r in enumerate(results):
            pins_processed = r.get('pins_processed', 0)
            successful_actions = r.get('successful_actions', 0)
            
            # An account is successful if it processed at least one pin with at least one successful action
            if pins_processed > 0 and successful_actions > 0:
                successful += 1
                r['status'] = 'success'  # Ensure status is set correctly
                print(f"  {Fore.GREEN}✅ SUCCESS: {r.get('account_email', 'unknown')}{Style.RESET_ALL}")
            else:
                failed += 1
                r['status'] = 'failed'  # Ensure status is set correctly
                print(f"  {Fore.RED}❌ FAILED: {r.get('account_email', 'unknown')}{Style.RESET_ALL}")
        
        # Calculate total time
        total_time = sum(r.get('timing', {}).get('total_processing_time', 0) for r in results)
        
        # Print summary
        print(f"\n{Fore.CYAN}📊 Summary:{Style.RESET_ALL}")
        print(f"Total accounts: {len(results)}")
        print(f"Successful: {Fore.GREEN}{successful}{Style.RESET_ALL}")
        print(f"Failed: {Fore.RED}{failed}{Style.RESET_ALL}")
        print(f"Total time: {total_time:.2f} seconds")
        
        # Print final summary - DIRECTLY OVERRIDE THE SUCCESS/FAIL COUNT BASED ON ACTUAL RESULTS
        # Recount again to ensure there are no discrepancies 
        successful = 0 
        failed = 0
        for r in results:
            # Additional debug output
            print(f"{Fore.YELLOW}⚙️ DEBUG STATUS: {r.get('account_email')}: raw_status={repr(r.get('status'))}, pins={r.get('pins_processed', 0)}, actions={r.get('successful_actions', 0)}{Style.RESET_ALL}")
            
            # EXPLICITLY CHECK THE ACTUAL NUMBERS - ignore the status field completely
            if r.get('pins_processed', 0) > 0 and r.get('successful_actions', 0) > 0:
                successful += 1
                print(f"{Fore.GREEN}✅ COUNTED AS SUCCESS: {r.get('account_email')}{Style.RESET_ALL}")
            else:
                failed += 1
                print(f"{Fore.RED}❌ COUNTED AS FAILURE: {r.get('account_email')}{Style.RESET_ALL}")
                
        # If we have processed pins and successful actions, but successful count is 0, force it to 1
        if len(results) == 1 and results[0].get('pins_processed', 0) > 0 and results[0].get('successful_actions', 0) > 0 and successful == 0:
            print(f"{Fore.YELLOW}⚠️ Forcing successful count from 0 to 1 since we have successful actions{Style.RESET_ALL}")
            successful = 1
            failed = 0
        
        print(f"\n{Fore.CYAN}📊 Final Summary:{Style.RESET_ALL}")
        print(f"Total accounts: {len(results)}")
        print(f"Successful: {Fore.GREEN}{successful}{Style.RESET_ALL}")
        print(f"Failed: {Fore.RED}{failed}{Style.RESET_ALL}")
        print(f"Total time: {total_time:.2f} seconds")
        
        # Print overall status based on the recounted values
        if successful > 0:
            print(f"\n{Fore.GREEN}✅ Pinterest Automation completed successfully!{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}❌ Pinterest Automation completed with errors.{Style.RESET_ALL}")
        
        return results
    
    def save_session_to_file(self, api: Any, session_file: str) -> None:
        """
        Save session data to a file.
        
        Args:
            api (Any): Pinterest API instance
            session_file (str): Path to save the session file
        """
        try:
            # Get session data
            session_data = {
                'headers': dict(api.session.headers),
                'cookies': {},
                'timestamp': int(time.time())
            }
            
            # Handle duplicate cookie names by using a dictionary
            for cookie in api.session.cookies:
                # Use the most recent cookie if there are duplicates
                session_data['cookies'][cookie.name] = cookie.value
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(session_file), exist_ok=True)
            
            # Save to file
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
                
            print(f"{Fore.GREEN}✅ Session saved to {session_file}{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error saving session: {str(e)}{Style.RESET_ALL}")
    
    def load_session_from_file(self, session_file: str) -> Optional[Dict[str, Any]]:
        """
        Load session data from a file.
        
        Args:
            session_file (str): Path to the session file
            
        Returns:
            Optional[Dict[str, Any]]: Session data or None if file doesn't exist or is invalid
        """
        try:
            if not os.path.exists(session_file):
                return None
                
            with open(session_file, 'r') as f:
                session_data = json.load(f)
                
            # Check if session is expired (24 hours)
            if time.time() - session_data.get('timestamp', 0) > 86400:
                print(f"{Fore.YELLOW}⚠️ Session expired{Style.RESET_ALL}")
                return None
                
            # Validate required session data
            if not all(key in session_data for key in ['headers', 'cookies', 'timestamp']):
                print(f"{Fore.YELLOW}⚠️ Invalid session data format{Style.RESET_ALL}")
                return None
                
            return session_data
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error loading session: {str(e)}{Style.RESET_ALL}")
            return None
    
    def _process_single_pin(self, pin: Dict[str, Any], result: Dict[str, Any], pin_id: str, api: Any) -> Dict[str, Any]:
        """
        Process a single pin with all interactions.
        
        Args:
            pin (Dict[str, Any]): Pin data
            result (Dict[str, Any]): Result dictionary to update
            pin_id (str): Pin ID
            api (Any): Pinterest API instance
            
        Returns:
            Dict[str, Any]: Result of pin processing
        """
        pin_result = {
            'pin_id': pin_id,
            'open_success': False,
            'like_success': False,
            'save_success': False,
            'comment_success': False,
            'link_visit_success': False,
            'open_attempted': False,
            'like_attempted': False,
            'save_attempted': False,
            'comment_attempted': False,
            'link_visit_attempted': False,
            'errors': []
        }
        
        # Add delay between actions to avoid rate limiting
        def add_delay():
            delay = random.uniform(2, 5)
            print(f"{Fore.YELLOW}⏳ Waiting {delay:.1f} seconds to avoid rate limiting...{Style.RESET_ALL}")
            time.sleep(delay)
        
        try:
            # Get full name from user data
            full_name = result.get('user_data', {}).get('full_name', 'Unknown User')
            
            # Get account behaviors from result
            account_email = result.get('account_email', '')
            account_behaviors = result.get('account_behaviors', {})
            
            # Default behaviors if not specified (as percentages)
            default_behaviors = {
                'open_pin': 100,
                'like_pin': 100,
                'save_pin': 100,
                'comment_pin': 100,
                'visit_link': 100  # Always 100% as per requirement
            }
            
            # Merge default behaviors with account-specific behaviors
            behaviors = {**default_behaviors, **account_behaviors}
            
            # Ensure visit_link is always 100% as per requirement
            behaviors['visit_link'] = 100
            
            # Function to determine if an action should be performed based on probability
            def should_perform_action(action_name):
                probability = behaviors.get(action_name, 100)
                # Convert percentage to decimal (0-1)
                probability_decimal = probability / 100.0
                # Generate random number between 0 and 1
                random_value = random.random()
                # Return True if random value is less than probability
                return random_value < probability_decimal
            
            # Open pin
            if should_perform_action('open_pin'):
                pin_result['open_attempted'] = True
                try:
                    add_delay()
                    open_result = self.open_pin(api, pin_id, full_name)
                    pin_result['open_success'] = open_result.get('success', False)
                    if pin_result['open_success']:
                        print(f"{Fore.GREEN}✅ Opened pin {pin_id}{Style.RESET_ALL}")
                    else:
                        error_msg = open_result.get('error', 'Unknown error')
                        print(f"{Fore.RED}❌ Error opening pin {pin_id}: {error_msg}{Style.RESET_ALL}")
                        pin_result['errors'].append(f"Error opening pin {pin_id}: {error_msg}")
                except Exception as e:
                    error_msg = f"Error opening pin {pin_id}: {str(e)}"
                    print(f"{Fore.RED}❌ {error_msg}{Style.RESET_ALL}")
                    pin_result['errors'].append(error_msg)
                    if "429" in str(e):
                        print(f"{Fore.YELLOW}⚠️ Rate limited, waiting longer...{Style.RESET_ALL}")
                        time.sleep(random.uniform(10, 15))
            else:
                print(f"{Fore.YELLOW}⏭️ Skipping open pin action for account {account_email} (probability: {behaviors.get('open_pin', 100)}%){Style.RESET_ALL}")
            
            # Like pin
            if should_perform_action('like_pin'):
                pin_result['like_attempted'] = True
                try:
                    add_delay()
                    like_result = self.like_pin(api, pin_id, full_name)
                    pin_result['like_success'] = like_result.get('success', False)
                    if pin_result['like_success']:
                        print(f"{Fore.GREEN}✅ Liked pin {pin_id}{Style.RESET_ALL}")
                    else:
                        error_msg = like_result.get('error', 'Unknown error')
                        print(f"{Fore.RED}❌ Error liking pin {pin_id}: {error_msg}{Style.RESET_ALL}")
                        pin_result['errors'].append(f"Error liking pin {pin_id}: {error_msg}")
                except Exception as e:
                    error_msg = f"Error liking pin {pin_id}: {str(e)}"
                    print(f"{Fore.RED}❌ {error_msg}{Style.RESET_ALL}")
                    pin_result['errors'].append(error_msg)
                    if "429" in str(e):
                        print(f"{Fore.YELLOW}⚠️ Rate limited, waiting longer...{Style.RESET_ALL}")
                        time.sleep(random.uniform(10, 15))
            else:
                print(f"{Fore.YELLOW}⏭️ Skipping like pin action for account {account_email} (probability: {behaviors.get('like_pin', 100)}%){Style.RESET_ALL}")
            
            # Save pin
            if should_perform_action('save_pin'):
                pin_result['save_attempted'] = True
                try:
                    add_delay()
                    save_result = self.save_pin(api, pin_id, pin)
                    pin_result['save_success'] = save_result.get('success', False)
                    if pin_result['save_success']:
                        print(f"{Fore.GREEN}✅ Saved pin {pin_id}{Style.RESET_ALL}")
                    else:
                        error_msg = save_result.get('error', 'Unknown error')
                        print(f"{Fore.RED}❌ Error saving pin {pin_id}: {error_msg}{Style.RESET_ALL}")
                        pin_result['errors'].append(f"Error saving pin {pin_id}: {error_msg}")
                except Exception as e:
                    error_msg = f"Error saving pin {pin_id}: {str(e)}"
                    print(f"{Fore.RED}❌ {error_msg}{Style.RESET_ALL}")
                    pin_result['errors'].append(error_msg)
                    if "429" in str(e):
                        print(f"{Fore.YELLOW}⚠️ Rate limited, waiting longer...{Style.RESET_ALL}")
                        time.sleep(random.uniform(10, 15))
            else:
                print(f"{Fore.YELLOW}⏭️ Skipping save pin action for account {account_email} (probability: {behaviors.get('save_pin', 100)}%){Style.RESET_ALL}")
            
            # Comment on pin
            if should_perform_action('comment_pin'):
                pin_result['comment_attempted'] = True
                try:
                    add_delay()
                    comment = "Great pin! Thanks for sharing."
                    comment_result = self.comment_on_pin(api, pin, comment, full_name)
                    pin_result['comment_success'] = comment_result.get('success', False)
                    if pin_result['comment_success']:
                        print(f"{Fore.GREEN}✅ Commented on pin {pin_id}{Style.RESET_ALL}")
                    else:
                        error_msg = comment_result.get('error', 'Unknown error')
                        print(f"{Fore.RED}❌ Error commenting on pin {pin_id}: {error_msg}{Style.RESET_ALL}")
                        pin_result['errors'].append(f"Error commenting on pin {pin_id}: {error_msg}")
                except Exception as e:
                    error_msg = f"Error commenting on pin {pin_id}: {str(e)}"
                    print(f"{Fore.RED}❌ {error_msg}{Style.RESET_ALL}")
                    pin_result['errors'].append(error_msg)
                    if "429" in str(e):
                        print(f"{Fore.YELLOW}⚠️ Rate limited, waiting longer...{Style.RESET_ALL}")
                        time.sleep(random.uniform(10, 15))
            else:
                print(f"{Fore.YELLOW}⏭️ Skipping comment pin action for account {account_email} (probability: {behaviors.get('comment_pin', 100)}%){Style.RESET_ALL}")
            
            # Visit link if available (always required)
            if pin.get('link'):
                pin_result['link_visit_attempted'] = True
                try:
                    add_delay()
                    visit_result = self.visit_pin_link(pin, full_name, api)
                    pin_result['link_visit_success'] = visit_result.get('success', False)
                    if pin_result['link_visit_success']:
                        print(f"{Fore.GREEN}✅ Visited link for pin {pin_id}{Style.RESET_ALL}")
                    else:
                        error_msg = visit_result.get('error', 'Unknown error')
                        print(f"{Fore.RED}❌ Error visiting link for pin {pin_id}: {error_msg}{Style.RESET_ALL}")
                        pin_result['errors'].append(f"Error visiting link for pin {pin_id}: {error_msg}")
                except Exception as e:
                    error_msg = f"Error visiting link for pin {pin_id}: {str(e)}"
                    print(f"{Fore.RED}❌ {error_msg}{Style.RESET_ALL}")
                    pin_result['errors'].append(error_msg)
                    if "429" in str(e):
                        print(f"{Fore.YELLOW}⚠️ Rate limited, waiting longer...{Style.RESET_ALL}")
                        time.sleep(random.uniform(10, 15))
            else:
                print(f"{Fore.YELLOW}⚠️ No link available for pin {pin_id}{Style.RESET_ALL}")
            
            return pin_result
            
        except Exception as e:
            error_msg = f"Error processing pin {pin_id}: {str(e)}"
            print(f"{Fore.RED}❌ {error_msg}{Style.RESET_ALL}")
            pin_result['errors'].append(error_msg)
            return pin_result
    
    def _handle_relogin(self, api: Any, result: Dict[str, Any], error_msg: str) -> bool:
        """
        Handle re-login when authentication is required.
        
        Args:
            api (Any): Pinterest API instance
            result (Dict[str, Any]): Result dictionary containing account info
            error_msg (str): Error message that triggered re-login
            
        Returns:
            bool: True if re-login was successful, False otherwise
        """
        if "Authentication required" not in error_msg:
            return False
            
        if not hasattr(self, '_auth_retries'):
            self._auth_retries = 0
            
        max_auth_retries = 2
        if self._auth_retries >= max_auth_retries:
            print(f"{Fore.RED}❌ Max re-login attempts ({max_auth_retries}) reached{Style.RESET_ALL}")
            return False
            
        self._auth_retries += 1
        print(f"{Fore.YELLOW}🔄 Attempting to re-login (attempt {self._auth_retries}/{max_auth_retries})...{Style.RESET_ALL}")
        
        # Get credentials from result
        if not result.get('account_email') or not hasattr(api, 'password'):
            print(f"{Fore.RED}❌ Missing credentials for re-login{Style.RESET_ALL}")
            return False
        
        # Attempt to re-login
        login_result = self.login_account(api, result['account_email'], api.password)
        if login_result['success']:
            print(f"{Fore.GREEN}✅ Re-login successful{Style.RESET_ALL}")
            # Update result with new user data
            result['user_data'] = login_result['user_data']
            result['access_token'] = login_result['access_token']
            # Reset auth retries on success
            self._auth_retries = 0
            return True
        else:
            print(f"{Fore.RED}❌ Re-login failed: {login_result.get('error', 'Unknown error')}{Style.RESET_ALL}")
            return False

    def get_pins_with_links(self, api: Any, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get pins with links from the user's feed.
        
        Args:
            api (Any): Pinterest API instance
            result (Dict[str, Any]): Result dictionary to update with errors
            
        Returns:
            List[Dict[str, Any]]: List of pins that have links
        """
        pins_with_links = []
        bookmark = None
        max_feed_attempts = 5  # Maximum number of feed pages to try
        feed_attempts = 0
        
        try:
            while len(pins_with_links) < self.num_pins_to_process and feed_attempts < max_feed_attempts:
                print(f"{Fore.CYAN}📱 Fetching feed page {feed_attempts + 1}...{Style.RESET_ALL}")
                
                # Get feed data
                try:
                    feed_data = api.get_home_feed(bookmark=bookmark)
                    feed_attempts += 1
                except (AuthenticationError, Exception) as e:
                    error_msg = str(e)
                    print(f"{Fore.YELLOW}⚠️ {error_msg}{Style.RESET_ALL}")
                    
                    # Handle re-login if needed
                    if self._handle_relogin(api, result, error_msg):
                        continue  # Retry the feed fetch
                    
                    # For other errors or if max retries reached
                    if result and 'errors' in result:
                        result['errors'].append(error_msg)
                    break

                if not feed_data:
                    print(f"{Fore.YELLOW}⚠️ No feed data returned{Style.RESET_ALL}")
                    break
                
                # Extract pins from feed
                try:
                    pins = api.extract_pins_from_feed(feed_data)
                    bookmark = getattr(api, '_last_bookmark', None)
                except Exception as e:
                    error_msg = f"Error extracting pins: {str(e)}"
                    print(f"{Fore.YELLOW}⚠️ {error_msg}{Style.RESET_ALL}")
                    if result and 'errors' in result:
                        result['errors'].append(error_msg)
                    break
                
                if not pins:
                    print(f"{Fore.YELLOW}⚠️ No pins found in feed page {feed_attempts}{Style.RESET_ALL}")
                    if not bookmark:
                        break
                    continue
                
                # Filter pins to only those with links
                page_pins_with_links = [pin for pin in pins if pin.get('link')]
                pins_with_links.extend(page_pins_with_links)
                
                print(f"{Fore.GREEN}✨ Found {len(page_pins_with_links)} pins with links on page {feed_attempts}{Style.RESET_ALL}")
                
                # Break if we have enough pins or no more pages
                if len(pins_with_links) >= self.num_pins_to_process or not bookmark:
                    break
                
                # Add delay between feed fetches
                delay = random.uniform(1, 3)
                print(f"{Fore.YELLOW}⏳ Waiting {delay:.1f} seconds before next feed fetch...{Style.RESET_ALL}")
                time.sleep(delay)
            
            # Trim to requested number of pins
            pins_with_links = pins_with_links[:self.num_pins_to_process]
            print(f"{Fore.GREEN}✨ Total pins with links found: {len(pins_with_links)}{Style.RESET_ALL}")
            
            return pins_with_links
            
        except Exception as e:
            error_msg = f"Error getting pins with links: {str(e)}"
            print(f"{Fore.RED}❌ {error_msg}{Style.RESET_ALL}")
            if result and 'errors' in result:
                result['errors'].append(error_msg)
            return []

    def track_experience(
        self,
        api: Any,
        pin_id: str,
        placement_ids: list = [12],
        did_long_clickthrough: bool = False,
        did_pin_clickthrough: bool = True,
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
            api (Any): Pinterest API instance
            pin_id (str): The Pinterest pin ID
            placement_ids (list, optional): List of placement IDs. Defaults to [12].
            did_long_clickthrough (bool, optional): Whether user did a long clickthrough. Defaults to False.
            did_pin_clickthrough (bool, optional): Whether user did a pin clickthrough. Defaults to True.
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
        import uuid
        import json
        from urllib.parse import quote
        
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
            "X-Pinterest-Advertising-Id": api.session.headers.get('X-Pinterest-Advertising-Id', ''),
            "X-Pinterest-App-Type-Detailed": "3",
            "X-Pinterest-Device": "sdk_gphone64_arm64",
            "X-Pinterest-Device-Hardwareid": api.session.headers.get('X-Pinterest-Device-Hardwareid', ''),
            "X-Pinterest-Device-Manufacturer": "Google",
            "X-Pinterest-Installid": api.session.headers.get('X-Pinterest-Installid', ''),
            "X-Pinterest-Appstate": app_state,
            "X-Node-Id": "true",
            "Authorization": api.session.headers.get('Authorization', ''),
            "Accept-Encoding": "gzip, deflate, br",
            "Priority": "u=1, i",
            "Content-Type": "application/json"
        }
        
        try:
            # Send the request
            import requests
            response = requests.post(
                url=url,
                headers=headers,
                json=payload
            )
            
            print(f"{Fore.GREEN}✨ Experience tracking request sent successfully{Style.RESET_ALL}")
            
            return {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'response_data': response.json() if response.content else None
            }
            
        except Exception as e:
            print(f"{Fore.RED}❌ Experience tracking request failed: {str(e)}{Style.RESET_ALL}")
            return {
                'status_code': 0,
                'error': str(e)
            } 