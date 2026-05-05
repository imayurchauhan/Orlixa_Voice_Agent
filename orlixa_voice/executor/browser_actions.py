from playwright.sync_api import sync_playwright
from utils.logger import get_logger
import time
import os

logger = get_logger()

class BrowserActions:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def _format_selector(self, selector):
        """Helper to format simple selectors into valid Playwright CSS/Text selectors."""
        if not selector:
            return selector
        # If it looks like an attribute selector (e.g. name=q) but isn't wrapped in []
        if "=" in selector and not selector.startswith("text=") and "[" not in selector:
            key, val = selector.split("=", 1)
            # Remove quotes if they exist
            val = val.strip("'\"")
            return f"[{key}='{val}']"
        return selector

    def _ensure_browser(self):
        """Ensures that playwright, browser, context, and page are all active and valid."""
        # 1. Start Playwright if not started
        if not self.playwright:
            try:
                self.playwright = sync_playwright().start()
            except Exception as e:
                logger.error(f"Failed to start Playwright engine: {e}")
                return False

        # 2. Start or Re-start Browser if disconnected
        if not self.context:
            logger.info("Launching new browser instance...")
            try:
                # Use a persistent context to stay logged in and avoid bot detection
                user_data_dir = os.path.join(os.getcwd(), "browser_data")
                
                self.context = self.playwright.chromium.launch_persistent_context(
                    user_data_dir,
                    channel="chrome",
                    headless=False,
                    viewport={"width": 1280, "height": 720},
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-infobars"
                    ]
                )
                
                # Setup the page from the context
                if self.context.pages:
                    self.page = self.context.pages[0]
                else:
                    self.page = self.context.new_page()
                
                # Additional stealth: override navigator.webdriver
                self.page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                
                logger.info(f"Browser session started. Data saved in: {user_data_dir}")
                return True
            except Exception as e:
                logger.error(f"Failed to launch browser: {e}")
                return False
        
        # 3. Ensure a valid context and page exist if browser is still connected
        try:
            # Test if context is still valid by attempting to check pages
            # If the context is closed, this will throw an error
            self.context.pages
            
            if not self.page or self.page.is_closed():
                logger.info("Opening new page in existing browser...")
                self.page = self.context.new_page()
        except Exception as e:
            # If something is deeply wrong with the context, recreate everything
            logger.warning(f"Browser context or page lost ({e}). Re-initializing...")
            try:
                # Try to cleanup the old browser if it's still hanging
                if self.browser:
                    self.browser.close()
            except:
                pass
            self.browser = None
            self.context = None
            self.page = None
            return self._ensure_browser()

        return True

    def _wait_for_page_ready(self):
        """Helper to ensure page finishes loading and dynamic content renders."""
        if self.page:
            try:
                # Wait for network requests to settle
                self.page.wait_for_load_state("networkidle", timeout=5000)
            except Exception:
                pass # Ignore timeout if site has constant background requests
            
            # Explicit delay for Javascript frameworks to render the DOM
            self.page.wait_for_timeout(2000)

    def open_browser(self, url=None):
        try:
            if not self._ensure_browser():
                return False, "Failed to start browser engine."
            
            if url:
                self.page.goto(url, timeout=30000)
                # Wait for the page to be somewhat stable
                try:
                    self.page.wait_for_load_state("networkidle", timeout=5000)
                except:
                    pass # Continue even if network doesn't go idle
                self._wait_for_page_ready()
                logger.info(f"Opened browser and navigated to {url}")
                return True, f"Opened browser at {url}"
            else:
                logger.info("Opened browser.")
                return True, "Opened browser."
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error opening browser/navigating: {error_msg}")
            if "closed" in error_msg.lower():
                self.browser = None
                self.context = None
                self.page = None
            return False, f"Failed to open browser: {error_msg}"

    def navigate(self, url):
        try:
            if not self._ensure_browser():
                return False, "Browser is not running."
            logger.info(f"Navigating to {url}")
            self.page.goto(url, timeout=30000)
            try:
                self.page.wait_for_load_state("networkidle", timeout=5000)
            except:
                pass
            self._wait_for_page_ready()
            return True, f"Navigated to {url}"
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to navigate to {url}: {error_msg}")
            if "closed" in error_msg.lower():
                self.browser = None
                self.context = None
                self.page = None
            return False, f"Failed to navigate: {error_msg}"

    def click(self, selector):
        if not self._ensure_browser():
            return False, "Browser not available."
        
        selector = self._format_selector(selector)
        try:
            logger.info(f"Clicking selector: {selector}")
            self.page.click(selector, timeout=10000)
            return True, f"Clicked element {selector}"
        except Exception as e:
            logger.error(f"Failed to click {selector}: {e}")
            return False, f"Failed to click: {e}"

    def type(self, selector, text):
        if not self._ensure_browser():
            return False, "Browser not available."
        
        selector = self._format_selector(selector)
        try:
            logger.info(f"Typing into selector: {selector}")
            self.page.fill(selector, text, timeout=10000)
            return True, f"Typed into {selector}"
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to type in {selector}: {error_msg}")
            return False, f"Failed to type: {error_msg}"

    def send_message(self, contact, message):
        # A specific implementation for an app like WhatsApp Web might look like this
        # Note: This is highly dependent on the website's DOM
        try:
            if not self._ensure_browser():
                return False, "Browser is not running."
            
            logger.info(f"Attempting to send message to {contact}")
            
            # Example logic for WhatsApp Web (simplified)
            # 1. Search for contact
            search_box = 'div[contenteditable="true"][data-tab="3"]'
            self.page.fill(search_box, contact)
            self.page.press(search_box, "Enter")
            time.sleep(2)
            
            # 2. Type message
            msg_box = 'div[contenteditable="true"][data-tab="10"]'
            self.page.fill(msg_box, message)
            self.page.press(msg_box, "Enter")
            
            return True, f"Sent message to {contact}"
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False, f"Failed to send message: {e}"

    def get_page_content(self):
        """Extracts text content from the current page for analysis."""
        try:
            if not self.page or self.page.is_closed():
                return "No page open."
            
            # Get text from body
            content = self.page.inner_text("body")
            # Truncate if too long for LLM (e.g., 5000 chars)
            return content[:5000]
        except Exception as e:
            logger.error(f"Failed to get page content: {e}")
            return f"Error reading page: {e}"

    def close(self):
        try:
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            logger.info("Browser closed.")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
