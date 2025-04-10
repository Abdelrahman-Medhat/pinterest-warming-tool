import random
import time
from typing import Dict, Any, Optional
from colorama import Fore, Style
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

class BrowserMixin:
    """
    Mixin for browser-related operations.
    """
    
    def setup_browser(self) -> webdriver.Chrome:
        """
        Set up Chrome browser with specific options.
        
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
    
    def human_scroll(self, driver: webdriver.Chrome, scroll_time: float = 30) -> None:
        """
        Perform human-like scrolling on a webpage.
        
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
    
    def visit_pin_link(self, pin: Dict[str, Any], full_name: str, pinterest_api=None) -> Dict[str, Any]:
        """
        Visit a pin's link in a browser with human-like behavior.
        
        Args:
            pin (Dict[str, Any]): Pin data containing the link
            full_name (str): User's full name for logging
            pinterest_api: Pinterest API instance for tracking
            
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
        
        # Track clickthrough start event if pinterest_api is provided
        if pinterest_api:
            print(f"{Fore.CYAN}📤 Sending clickthrough start event for {link}...{Style.RESET_ALL}")
            pinterest_api.track_clickthrough(
                url=link,
                pin_id=pin['id'],
                is_start=True
            )

        driver = None
        try:
            print(f"{Fore.CYAN}🌐 Opening link in browser for pin {Fore.YELLOW}{pin['id']}{Fore.CYAN}: {Fore.WHITE}{link}{Style.RESET_ALL}")
            
            # Set up and launch browser
            driver = self.setup_browser()
            
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
            self.human_scroll(driver, scroll_time)
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
            
            # Track clickthrough end event if pinterest_api is provided
            if pinterest_api:
                print(f"{Fore.CYAN}📤 Sending clickthrough end event for {link}...{Style.RESET_ALL}")
                pinterest_api.track_clickthrough(
                    url=link,
                    pin_id=pin['id'],
                    is_start=False,
                    duration=int(result['timing']['total_time'])
                )
            
            if result['success']:
                total_interaction = result['timing']['stats']['initial_wait'] + \
                                  result['timing']['stats']['scroll_time'] + \
                                  result['timing']['stats']['final_wait']
                print(f"{Fore.GREEN}✨ Successfully visited link for {total_interaction:.1f} seconds total{Style.RESET_ALL}")
                print(f"   👀 Initial view: {result['timing']['stats']['initial_wait']:.1f}s")
                print(f"   📜 Scrolling: {result['timing']['stats']['scroll_time']:.1f}s")
                print(f"   👋 Final view: {result['timing']['stats']['final_wait']:.1f}s")
        
        return result 