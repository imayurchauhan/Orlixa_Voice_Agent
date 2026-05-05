from playwright.sync_api import sync_playwright
from utils.logger import get_logger
import time

logger = get_logger()

class BrowserActions:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

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
        if not self.browser or not self.browser.is_connected():
            logger.info("Launching new browser instance...")
            try:
                self.browser = self.playwright.chromium.launch(headless=False, channel="chrome")
                self.context = self.browser.new_context()
                self.page = self.context.new_page()
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
                self.page.goto(url)
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
            self.page.goto(url)
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
        try:
            if not self._ensure_browser():
                return False, "Browser is not running."
            logger.info(f"Clicking selector: {selector}")
            self.page.click(selector)
            self._wait_for_page_ready()
            return True, f"Clicked element {selector}"
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to click {selector}: {error_msg}")
            if "closed" in error_msg.lower():
                self.browser = None
                self.context = None
                self.page = None
            return False, f"Failed to click: {error_msg}"

    def type_text(self, selector, text):
        try:
            if not self._ensure_browser():
                return False, "Browser is not running."
            logger.info(f"Typing into selector: {selector}")
            self.page.fill(selector, text)
            self.page.wait_for_timeout(1000) # small delay after typing
            return True, f"Typed text into {selector}"
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to type in {selector}: {error_msg}")
            if "closed" in error_msg.lower():
                self.browser = None
                self.context = None
                self.page = None
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

    def close(self):
        try:
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            logger.info("Browser closed.")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
