import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class JavaScriptChangeDetector:
    def __init__(self, driver):
        self.driver = driver
        self.logger = logging.getLogger(__name__)
        self.previous_page_source = ""

    def check_for_js_changes(self, success_message=None, error_keywords=None, delay=2):
        """Check for JavaScript changes or error messages on the page.
        
        Args:
            success_message (str): The expected success message after changes are applied.
            error_keywords (list of str): List of keywords indicating errors.
            delay (int): Time in seconds to wait for changes to appear.
        """
        if error_keywords is None:
            error_keywords = ["error", "failed", "invalid"]
        
        # Wait for potential changes on the page
        time.sleep(delay)

        # Capture the current state of the page source
        page_source = self.driver.page_source.lower()

        # Compare the current page source with the previous one to detect any changes
        if self.previous_page_source and self.previous_page_source != page_source:
            self.logger.info("Detected changes in the page source.")
        else:
            self.logger.info("No changes detected in the page source.")
        self.previous_page_source = page_source

        # Check for success messages
        if success_message and success_message.lower() in page_source:
            self.logger.info(f"Success message detected: '{success_message}'")
        
        # Check for error keywords in the page source
        for keyword in error_keywords:
            if keyword in page_source:
                self.logger.warning(f"Error detected: keyword '{keyword}' found on the page.")
                
        # Check for red text on the page as an indicator of potential errors
        try:
            red_text_elements = self.driver.find_elements(By.XPATH, "//*[contains(@style, 'color: red')] | //*[contains(@class, 'error')] | //*[contains(@class, 'alert')] | //*[contains(@role, 'alert')]")
            if red_text_elements:
                self.logger.warning("Red text or alert detected on the page, which could indicate an error.")
                for element in red_text_elements:
                    self.logger.warning(f"Error content: {element.text}")
        except Exception as e:
            self.logger.error(f"Error while detecting red text elements: {e}")
        
        # Log any changes detected in the console log
        try:
            logs = self.driver.get_log('browser')
            if not logs:
                self.logger.info("No console log entries detected.")
            for entry in logs:
                self.logger.info(f"Console log entry: {entry['message']}")
        except Exception as e:
            self.logger.error(f"Error while retrieving console logs: {e}")
