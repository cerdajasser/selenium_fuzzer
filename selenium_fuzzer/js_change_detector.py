import logging
import time

class JavaScriptChangeDetector:
    def __init__(self, driver):
        self.driver = driver
        self.logger = logging.getLogger(__name__)

    def check_for_js_changes(self, success_message=None, error_keywords=None, delay=2):
        """Check for JavaScript changes or error messages on the page.
        
        Args:
            success_message (str): The expected success message after changes.
            error_keywords (list of str): Keywords indicating errors on the page.
            delay (int): Time to wait for JavaScript changes.

        """
        time.sleep(delay)  # Wait for any JavaScript changes to take effect
        page_source = self.driver.page_source

        if success_message and success_message in page_source:
            self.logger.info(f"Success message detected: '{success_message}'")
        
        if error_keywords:
            for error in error_keywords:
                if error.lower() in page_source.lower():
                    self.logger.warning(f"Error detected: '{error}'")

