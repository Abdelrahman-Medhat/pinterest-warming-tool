from pinterest_api import PinterestAPI
from pinterest_api.exceptions import (
    EmailNotFoundError,
    LoginFailedError,
    InvalidResponseError,
    PinterestAuthError,
    IncorrectPasswordError,
    AuthenticationError
)
import requests
import json
from datetime import datetime
import os
import concurrent.futures
from typing import List, Dict, Any
from colorama import init, Fore, Style
import random
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Initialize colorama for cross-platform colored output
init()

def save_data(data: dict, prefix: str = "pinterest_data") -> str:
    """Save data to a JSON file."""
    # Create a results directory if it doesn't exist
    os.makedirs("results", exist_ok=True)
    
    # Generate timestamp for unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save JSON data
    filename = f"results/{prefix}_{timestamp}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return filename

def save_session_to_file(user_data: dict, access_token: str, prefix: str = "pinterest_session") -> str:
    """Save Pinterest session data to a file.
    
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

def load_session_from_file(filename: str) -> tuple:
    """Load Pinterest session data from a file.
    
    Args:
        filename (str): Path to the session file
        
    Returns:
        tuple: (user_data, access_token)
    """
    with open(filename, 'r', encoding='utf-8') as f:
        session_data = json.load(f)
    
    return session_data['user_data'], session_data['access_token']

def human_delay(action: str = "default", min_seconds: float = 3, max_seconds: float = 8) -> float:
    """Add a random human-like delay and log it.
    
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

def setup_browser() -> webdriver.Chrome:
    """Set up Chrome browser with specific options.
    
    Returns:
        webdriver.Chrome: Configured Chrome browser instance
    """
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")  # Start maximized
    chrome_options.add_argument("--disable-notifications")  # Disable notifications
    chrome_options.add_argument("--disable-popup-blocking")  # Disable popup blocking
    chrome_options.add_argument("--disable-infobars")  # Disable infobars
    chrome_options.add_argument("--disable-extensions")  # Disable extensions
    
    # Add user agent to appear more human-like
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    
    return webdriver.Chrome(options=chrome_options)

def human_scroll(driver: webdriver.Chrome, scroll_time: float = 30) -> None:
    """Perform human-like scrolling on a webpage.
    
    Args:
        driver (webdriver.Chrome): Chrome browser instance
        scroll_time (float): Total time to spend scrolling in seconds
    """
    print(f"{Fore.CYAN}📜 Starting human-like scrolling...{Style.RESET_ALL}")
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

def visit_pin_link(pin: Dict[str, Any], full_name: str) -> Dict[str, Any]:
    """Visit a pin's link in a browser with human-like behavior.
    
    Args:
        pin (Dict[str, Any]): Pin data containing the link
        full_name (str): User's full name for logging
        
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
    
    driver = None
    try:
        print(f"{Fore.CYAN}🌐 Opening link in browser for pin {Fore.YELLOW}{pin['id']}{Fore.CYAN}: {Fore.WHITE}{link}{Style.RESET_ALL}")
        
        # Set up and launch browser
        driver = setup_browser()
        
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
        human_scroll(driver, scroll_time)
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
        
        if result['success']:
            total_interaction = result['timing']['stats']['initial_wait'] + \
                              result['timing']['stats']['scroll_time'] + \
                              result['timing']['stats']['final_wait']
            print(f"{Fore.GREEN}✨ Successfully visited link for {total_interaction:.1f} seconds total{Style.RESET_ALL}")
            print(f"   👀 Initial view: {result['timing']['stats']['initial_wait']:.1f}s")
            print(f"   📜 Scrolling: {result['timing']['stats']['scroll_time']:.1f}s")
            print(f"   👋 Final view: {result['timing']['stats']['final_wait']:.1f}s")
    
    return result

def process_account(
    account: Dict[str, str], 
    comments: List[str],
    num_pins_to_process: int = 10,
    retry_count: int = 0, 
    max_retries: int = 3
) -> Dict[str, Any]:
    """Process a single Pinterest account.
    
    Args:
        account (dict): Dictionary containing 'email' and 'password'
        comments (List[str]): List of comments to use (will be cycled through)
        num_pins_to_process (int): Number of pins to process
        retry_count (int): Current retry attempt number
        max_retries (int): Maximum number of retries allowed
    """
    result = {
        'email': account['email'],
        'status': 'failed',
        'error': None,
        'user_data': None,
        'pins_data': [],
        'actions_results': [],
        'timing': {
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'total_delays': 0,
            'delays': []
        }
    }
    
    try:
        pinterest = PinterestAPI(
            email=account['email'],
            password=account['password']
        )
        
        session_file = f"sessions/pinterest_session_{account['email'].replace('@', '_at_').replace('.', '_')}.json"
        print(f"{Fore.CYAN}🔐 Processing account: {Fore.YELLOW}{account['email']}{Style.RESET_ALL}")
        
        try:
            session_exists = os.path.exists(session_file)
            session_data = pinterest.get_or_create_session(session_file)
            
            result['session_type'] = 'loaded' if session_exists else 'created'
            result['user_data'] = session_data['user_data']
            full_name = result['user_data'].get('full_name', 'Unknown User')
            
            print(f"{Fore.GREEN}✨ Session {Fore.BLUE}{result['session_type']}{Fore.GREEN} successfully for {Fore.YELLOW}{account['email']} ({full_name}){Style.RESET_ALL}")
            result['status'] = 'active'

            # Process pins from feed
            pins_processed = 0
            bookmark = None
            max_feed_attempts = 5  # Maximum number of feed pages to try
            feed_attempts = 0
            
            while pins_processed < num_pins_to_process and feed_attempts < max_feed_attempts:
                # Get feed data
                try:
                    print(f"{Fore.CYAN}📱 Fetching feed page {feed_attempts + 1} for {Fore.YELLOW}{full_name}{Style.RESET_ALL}")
                    feed_data = pinterest.get_home_feed(bookmark=bookmark)
                    save_data(feed_data, f"feed_data_{account['email']}_{feed_attempts}")
                    feed_attempts += 1
                except Exception as e:
                    print(f"{Fore.RED}❌ Error fetching feed: {str(e)}{Style.RESET_ALL}")
                    if not bookmark:
                        break
                    continue
                
                # Extract pins and get bookmark for next page
                pins = pinterest.extract_pins_from_feed(feed_data)
                bookmark = getattr(pinterest, '_last_bookmark', None)
                
                if not pins:
                    print(f"{Fore.YELLOW}⚠️ No pins found in feed page {feed_attempts}, trying next page{Style.RESET_ALL}")
                    if not bookmark:
                        print(f"{Fore.RED}❌ No more pages available{Style.RESET_ALL}")
                        break
                    continue

                # Filter pins to only those with links
                pins_with_links = [pin for pin in pins if pin.get('link')]
                if not pins_with_links:
                    print(f"{Fore.YELLOW}⚠️ No pins with links found in feed page {feed_attempts}, trying next page{Style.RESET_ALL}")
                    continue

                # Add random delay before selecting a pin (simulating browsing)
                browse_delay = human_delay("selecting a pin to interact with", 4, 10)
                result['timing']['delays'].append({
                    'action': 'browse_delay',
                    'seconds': browse_delay
                })
                result['timing']['total_delays'] += browse_delay

                # Select one random pin from pins with links
                pin = random.choice(pins_with_links)
                pin_id = pin.get('id')
                print(f"{Fore.CYAN}📌 Selected pin {Fore.YELLOW}{pin_id}{Fore.CYAN} with link: {Fore.WHITE}{pin.get('link')}{Style.RESET_ALL}")

                pin_result = {
                    'pin_id': pin_id,
                    'fetch_success': True,
                    'like_success': False,
                    'comment_success': False,
                    'link_visit_success': False,
                    'pin_open_success': False,
                    'pin_save_success': False,
                    'errors': [],
                    'timing': {
                        'start_time': datetime.now().isoformat(),
                        'end_time': None,
                        'total_delays': 0,
                        'delays': []
                    }
                }

                try:
                    # Simulate opening the pin
                    print(f"{Fore.CYAN}👁️  Opening pin {Fore.YELLOW}{pin_id}{Fore.CYAN} as {Fore.YELLOW}{full_name}{Style.RESET_ALL}")
                    open_result = pinterest.simulate_pin_open(pin_id)
                    pin_result['pin_open_success'] = open_result['success']
                    pin_result['timing']['delays'].append({
                        'action': 'pin_open',
                        'seconds': open_result['timing']['total_time']
                    })
                    pin_result['timing']['total_delays'] += open_result['timing']['total_time']
                    result['timing']['total_delays'] += open_result['timing']['total_time']
                    
                    if open_result['success']:
                        print(f"{Fore.GREEN}✨ Pin opened successfully (Load: {open_result['timing']['load_time']:.1f}s, View: {open_result['timing']['view_time']:.1f}s){Style.RESET_ALL}")

                    # Like the pin
                    like_delay = human_delay("liking the pin", 2, 5)
                    pin_result['timing']['delays'].append({
                        'action': 'like_delay',
                        'seconds': like_delay
                    })
                    pin_result['timing']['total_delays'] += like_delay
                    result['timing']['total_delays'] += like_delay

                    print(f"{Fore.CYAN}❤️  Reacting to pin {Fore.YELLOW}{pin_id}{Fore.CYAN} as {Fore.YELLOW}{full_name}{Style.RESET_ALL}")
                    reaction_data = pinterest.react_to_pin(pin_id)
                    pin_result['like_success'] = True

                    # Save the pin
                    save_delay = human_delay("preparing to save pin", 1, 3)
                    pin_result['timing']['delays'].append({
                        'action': 'save_delay',
                        'seconds': save_delay
                    })
                    pin_result['timing']['total_delays'] += save_delay
                    result['timing']['total_delays'] += save_delay

                    print(f"{Fore.CYAN}📌 Saving pin {Fore.YELLOW}{pin_id}{Style.RESET_ALL}")
                    save_result = pinterest.save_pin(pin_id)
                    pin_result['pin_save_success'] = True
                    print(f"{Fore.GREEN}✨ Pin saved successfully{Style.RESET_ALL}")

                    # Comment on the pin
                    comment_text = comments[pins_processed % len(comments)]
                    typing_delay = len(comment_text) * random.uniform(0.1, 0.3)  # Simulate typing speed
                    comment_delay = human_delay(f"typing comment: {comment_text}", typing_delay, typing_delay + 2)
                    pin_result['timing']['delays'].append({
                        'action': 'comment_delay',
                        'seconds': comment_delay
                    })
                    pin_result['timing']['total_delays'] += comment_delay
                    result['timing']['total_delays'] += comment_delay

                    print(f"{Fore.CYAN}💬 Commenting on pin {Fore.YELLOW}{pin_id}{Fore.CYAN} as {Fore.YELLOW}{full_name}{Fore.CYAN}: {Fore.WHITE}{comment_text}{Style.RESET_ALL}")
                    comment_data = pinterest.post_comment(pin_data=pin, text=comment_text)
                    pin_result['comment_success'] = True

                    # Visit pin link
                    visit_result = visit_pin_link(pin, full_name)
                    pin_result['link_visit_success'] = visit_result['success']
                    pin_result['link_visit_data'] = visit_result
                    
                    if visit_result['success']:
                        result['timing']['total_delays'] += visit_result['timing']['total_time']
                        pin_result['timing']['delays'].append({
                            'action': 'link_visit',
                            'seconds': visit_result['timing']['total_time']
                        })
                        pin_result['timing']['total_delays'] += visit_result['timing']['total_time']

                    pins_processed += 1
                    pin_result['timing']['end_time'] = datetime.now().isoformat()
                    result['pins_data'].append(pin)
                    result['actions_results'].append(pin_result)

                    # Add random delay before moving to next pin (simulating browsing)
                    if pins_processed < num_pins_to_process:
                        scroll_delay = human_delay("scrolling to next page", 5, 12)
                        pin_result['timing']['delays'].append({
                            'action': 'scroll_delay',
                            'seconds': scroll_delay
                        })
                        pin_result['timing']['total_delays'] += scroll_delay
                        result['timing']['total_delays'] += scroll_delay

                except Exception as e:
                    error_msg = f"Error processing pin {pin_id}: {str(e)}"
                    pin_result['errors'].append(error_msg)
                    print(f"{Fore.RED}❌ {error_msg}{Style.RESET_ALL}")
                    pin_result['timing']['end_time'] = datetime.now().isoformat()
                    result['actions_results'].append(pin_result)
                    
        except AuthenticationError as e:
            if retry_count < max_retries:
                print(f"{Fore.YELLOW}⚠️ Session invalid, retrying with new login for {Fore.CYAN}{account['email']}{Style.RESET_ALL}")
                return process_account(account, comments, num_pins_to_process, retry_count + 1, max_retries)
            else:
                raise AuthenticationError(f"Failed to create valid session after {max_retries} attempts")
    
    except EmailNotFoundError as e:
        result['error'] = f"Email not found: {str(e)}"
        print(f"{Fore.RED}❌ {result['error']}{Style.RESET_ALL}")
    except IncorrectPasswordError:
        result['error'] = "Incorrect password"
        print(f"{Fore.RED}❌ {result['error']}{Style.RESET_ALL}")
    except LoginFailedError as e:
        result['error'] = f"Login failed: {str(e)}"
        print(f"{Fore.RED}❌ {result['error']}{Style.RESET_ALL}")
    except InvalidResponseError as e:
        result['error'] = f"Invalid response: {str(e)}"
        print(f"{Fore.RED}❌ {result['error']}{Style.RESET_ALL}")
    except requests.exceptions.RequestException as e:
        result['error'] = f"Network error: {str(e)}"
        print(f"{Fore.RED}❌ {result['error']}{Style.RESET_ALL}")
    except PinterestAuthError as e:
        result['error'] = f"Auth error: {str(e)}"
        print(f"{Fore.RED}❌ {result['error']}{Style.RESET_ALL}")
    except Exception as e:
        result['error'] = f"Unexpected error: {str(e)}"
        print(f"{Fore.RED}❌ {result['error']}{Style.RESET_ALL}")
    
    # Set end time and calculate total duration
    result['timing']['end_time'] = datetime.now().isoformat()
    
    status_color = Fore.GREEN if result['status'] == 'active' else Fore.RED
    full_name = result['user_data'].get('full_name', 'Unknown User') if result['user_data'] else 'Unknown User'
    print(f"{status_color}✨ Finished processing {Fore.YELLOW}{account['email']} ({full_name}){status_color} - Status: {result['status']}{Style.RESET_ALL}")
    
    # Print summary of actions
    if result['status'] == 'active':
        print(f"\n{Fore.CYAN}📊 Actions Summary for {Fore.YELLOW}{full_name}{Style.RESET_ALL}")
        
        # Print overall timing
        start_time = datetime.fromisoformat(result['timing']['start_time'])
        end_time = datetime.fromisoformat(result['timing']['end_time'])
        total_duration = (end_time - start_time).total_seconds()
        print(f"⏱️ Total session time: {total_duration:.1f}s (Delays: {result['timing']['total_delays']:.1f}s)")
        
        # Print individual pin results
        for pin_result in result['actions_results']:
            status = "✅" if all([pin_result['fetch_success'], pin_result['like_success'], pin_result['comment_success']]) else "⚠️"
            print(f"\n{status} Pin {pin_result['pin_id']}: Open_Pin={'✅' if pin_result['fetch_success'] else '❌'} Like={'✅' if pin_result['like_success'] else '❌'} Comment={'✅' if pin_result['comment_success'] else '❌'}")
            
            # Print link visit result if applicable
            if 'link_visit_success' in pin_result:
                print(f"   🌐 Link Visit: {'✅' if pin_result['link_visit_success'] else '❌'}")
                if 'link_visit_data' in pin_result and pin_result['link_visit_data'].get('timing'):
                    visit_timing = pin_result['link_visit_data']['timing']
                    print(f"   ⏱️ Link visit time: {visit_timing['total_time']:.1f}s (Scroll time: {visit_timing.get('scroll_time', 0):.1f}s)")
            
            # Print pin timing information
            if 'timing' in pin_result:
                start_time = datetime.fromisoformat(pin_result['timing']['start_time'])
                end_time = datetime.fromisoformat(pin_result['timing']['end_time'])
                duration = (end_time - start_time).total_seconds()
                print(f"   ⏱️ Pin processing time: {duration:.1f}s (Delays: {pin_result['timing']['total_delays']:.1f}s)")
                for delay in pin_result['timing']['delays']:
                    print(f"   ⌛ {delay['action']}: {delay['seconds']:.1f}s")
            
            if pin_result['errors']:
                for error in pin_result['errors']:
                    print(f"   {Fore.RED}→ {error}{Style.RESET_ALL}")
    
    return result

def process_accounts(
    accounts: List[Dict[str, str]], 
    comments: List[str],
    num_pins_to_process: int = 10,
    max_workers: int = 10
) -> List[Dict[str, Any]]:
    """Process multiple Pinterest accounts in parallel.
    
    Args:
        accounts (list): List of dictionaries, each containing 'email' and 'password'
        comments (List[str]): List of comments to use
        num_pins_to_process (int): Number of pins to process per account
        max_workers (int): Maximum number of concurrent threads
    """
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all accounts for processing
        future_to_account = {
            executor.submit(process_account, account, comments, num_pins_to_process): account 
            for account in accounts
        }
        
        # Collect results as they complete
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
    
    return results

def main():
    # Example accounts list
    accounts = [
        {
            'email': "afb15c3b3b@emaily.pro",
            'password': "afb15c3b3b1593578642",
            'proxy': "krlokchm:kj64VkCG7VpO@3.64.56.200:8888"
        },
        # {
        #     'email': "ursula.belford.73@mail.ru",
        #     'password': "R0iQcLrIw6J4",
        #     'proxy': "vnarcqoj:eFJRQP9TBM2m@18.184.13.167:8888"
        # },
        # {
        #     'email': "crowem2023@mail.ru",
        #     'password': "GcUg2j7AlXRN",
        #     'proxy': "fgxcyzyb:Bd9oQFBUw92v@3.73.0.185:8888"
        # },
        # {
        #     'email': "ordeiro90-00@mail.ru",
        #     'password': "aCA5E8xjwgbt",
        #     'proxy': "yovwzsqo:tS8dCaaSAF6g@3.75.82.16:8888"
        # }
        # Add more accounts here
    ]
    
    # List of comments to use
    comments = [
        "😍",
        "❤️",
        "👏",
        "🌟",
        # Add more comments here
    ]
    
    # Process accounts with max 10 concurrent threads
    print(f"{Fore.CYAN}🚀 Starting to process {Fore.YELLOW}{len(accounts)}{Fore.CYAN} accounts...{Style.RESET_ALL}")
    results = process_accounts(accounts, comments, num_pins_to_process=1, max_workers=10)
    
    # Print summary
    success_count = sum(1 for r in results if r['status'] == 'active')
    print(f"\n{Fore.CYAN}📊 Summary:{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Total accounts: {Fore.YELLOW}{len(accounts)}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}Successful: {Fore.YELLOW}{success_count}{Style.RESET_ALL}")
    print(f"{Fore.RED}Failed: {Fore.YELLOW}{len(accounts) - success_count}{Style.RESET_ALL}")

if __name__ == "__main__":
    main() 