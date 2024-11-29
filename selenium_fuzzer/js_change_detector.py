import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

class JavaScriptChangeDetector:
    def __init__(self, driver):
        self.driver = driver
        self.logger = logging.getLogger(__name__)
        self.previous_page_source = ""

        # Set up console handler for logging important information
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        self.console_logger = logging.getLogger('console_logger')
        self.console_logger.addHandler(console_handler)
        self.console_logger.setLevel(logging.INFO)

        # Set up Chrome DevTools Protocol (CDP) session
        self.devtools = driver.execute_cdp_cmd
        self._initialize_devtools()

    def _initialize_devtools(self):
        """Initialize Chrome DevTools Protocol for network and JS event analysis"""
        try:
            # Enabling network and JavaScript console logging
            self.devtools('Network.enable', {})
            self.devtools('Log.enable', {})
            self.devtools('Runtime.enable', {})
            self.logger.info("DevTools successfully initialized.")
        except Exception as e:
            self.logger.error(f"Error initializing DevTools: {e}")
            self.console_logger.error(f"Error initializing DevTools: {e}")

    def capture_network_activity(self):
        """Capture and analyze network activity for anomalies"""
        try:
            # Setting up a callback for network requests
            self.devtools('Network.requestWillBeSent', {}, callback=self.on_network_request)
        except Exception as e:
            self.logger.error(f"Error capturing network activity: {e}")

    def on_network_request(self, params):
        """Handle a network request event"""
        try:
            url = params.get('request', {}).get('url', '')
            method = params.get('request', {}).get('method', 'GET')
            self.console_logger.info(f"Network Request: {method} {url}")

            # You can implement custom analysis here for specific URL patterns, payloads, etc.
            if 'error' in url.lower():
                self.console_logger.warning(f"Anomalous URL detected: {url}")

        except Exception as e:
            self.logger.error(f"Error processing network request event: {e}")

    def capture_js_console_logs(self):
        """Capture and analyze JavaScript console logs for errors or anomalies"""
        try:
            console_logs = self.driver.get_log("browser")
            for log_entry in console_logs:
                if "error" in log_entry['message'].lower():
                    self.console_logger.warning(f"JavaScript Error: {log_entry['message']}")
                else:
                    self.console_logger.info(f"JavaScript Log: {log_entry['message']}")
        except Exception as e:
            self.logger.error(f"Error capturing JavaScript console logs: {e}")

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

        # Log the lengths of previous and current page sources for debugging purposes
        self.logger.debug(f"Previous page source length: {len(self.previous_page_source)}")
        self.logger.debug(f"Current page source length: {len(page_source)}")

        # Compare the current page source with the previous one to detect any changes
        if self.previous_page_source and self.previous_page_source != page_source:
            self.logger.info("Detected changes in the page source.")
            self.console_logger.info("Detected changes in the page source.")
            self._log_updated_text()  # Log the updated text from JavaScript changes
        else:
            self.logger.info("No changes detected in the page source.")
            self.console_logger.info("No changes detected in the page source.")
        self.previous_page_source = page_source

        # Check for success messages
        if success_message and success_message.lower() in page_source:
            self.logger.info(f"Success message detected: '{success_message}'")
            self.console_logger.info(f"Success message detected: '{success_message}'")

        # Check for error keywords in the page source
        for keyword in error_keywords:
            if keyword in page_source:
                self.logger.warning(f"Error detected: keyword '{keyword}' found on the page.")
                self.console_logger.warning(f"Error detected: keyword '{keyword}' found on the page.")

    def _initialize_js_logging(self):
        """Initialize JavaScript logging to store updates in a global variable."""
        script = "window.updatedTextLogs = [];"
        self.driver.execute_script(script)

    def _log_updated_text(self):
        """Retrieve updated text logged by JavaScript and log it to the console."""
        script = "return window.updatedTextLogs || [];"
        updated_text_logs = self.driver.execute_script(script)
        if updated_text_logs:
            self.console_logger.info("Logging detected changes:")
            for log in updated_text_logs:
                if log:  # Only log non-empty changes
                    self.console_logger.info(f"Updated text detected: {log}")

        # Clear the logs after retrieval
        self.driver.execute_script("window.updatedTextLogs = [];")
