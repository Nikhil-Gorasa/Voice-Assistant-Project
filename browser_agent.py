import os
from playwright.sync_api import sync_playwright, Browser, Page
import time

class BrowserAgent:
    def __init__(self, persistent_session=False):
        self.browser = None
        self.page = None
        self.persistent_session = persistent_session
        self.chrome_path = os.getenv('CHROME_PATH', '')
        self.chrome_user_data = os.getenv('CHROME_USER_DATA', '')
        
    def start_browser(self):
        """Start the browser session"""
        try:
            self.playwright = sync_playwright().start()
            
            # Configure browser launch options
            launch_options = {
                "headless": False,
            }
            
            # Add custom Chrome executable if specified
            if self.chrome_path:
                launch_options["executable_path"] = self.chrome_path
                
            # Add user data directory if specified
            if self.chrome_user_data:
                launch_options["user_data_dir"] = self.chrome_user_data
            
            self.browser = self.playwright.chromium.launch(**launch_options)
            self.page = self.browser.new_page()
            return True
        except Exception as e:
            print(f"Error starting browser: {str(e)}")
            return False
            
    def close_browser(self):
        """Close the browser session"""
        try:
            if not self.persistent_session:
                if self.page:
                    self.page.close()
                if self.browser:
                    self.browser.close()
                if self.playwright:
                    self.playwright.stop()
            return True
        except Exception as e:
            print(f"Error closing browser: {str(e)}")
            return False
            
    def navigate(self, url: str) -> bool:
        """Navigate to a URL"""
        try:
            if not self.page:
                if not self.start_browser():
                    return False
            self.page.goto(url)
            return True
        except Exception as e:
            print(f"Error navigating to {url}: {str(e)}")
            return False
            
    def click_element(self, selector: str) -> bool:
        """Click an element on the page"""
        try:
            if not self.page:
                return False
            self.page.click(selector)
            return True
        except Exception as e:
            print(f"Error clicking element {selector}: {str(e)}")
            return False
            
    def type_text(self, selector: str, text: str) -> bool:
        """Type text into an input field"""
        try:
            if not self.page:
                return False
            self.page.fill(selector, text)
            return True
        except Exception as e:
            print(f"Error typing text into {selector}: {str(e)}")
            return False
            
    def get_text(self, selector: str) -> str:
        """Get text content from an element"""
        try:
            if not self.page:
                return ""
            element = self.page.query_selector(selector)
            if element:
                return element.text_content()
            return ""
        except Exception as e:
            print(f"Error getting text from {selector}: {str(e)}")
            return ""
            
    def take_screenshot(self, path: str) -> bool:
        """Take a screenshot of the current page"""
        try:
            if not self.page:
                return False
            self.page.screenshot(path=path)
            return True
        except Exception as e:
            print(f"Error taking screenshot: {str(e)}")
            return False
            
    def scroll_to(self, selector: str) -> bool:
        """Scroll to an element on the page"""
        try:
            if not self.page:
                return False
            element = self.page.query_selector(selector)
            if element:
                element.scroll_into_view_if_needed()
                return True
            return False
        except Exception as e:
            print(f"Error scrolling to {selector}: {str(e)}")
            return False
            
    def wait_for_element(self, selector: str, timeout: int = 30000) -> bool:
        """Wait for an element to appear on the page"""
        try:
            if not self.page:
                return False
            self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception as e:
            print(f"Error waiting for element {selector}: {str(e)}")
            return False 