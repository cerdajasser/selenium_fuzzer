import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

class JavaScriptChangeDetector:
    def __init__(self, driver, enable_devtools=False):
        self.driver = driver
        self.enable_devtools = enable_devtools
        self.logger = logging.getLogger(__name__)
        self.previous_page_source = ""

        # Set up console handler for logging important information
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)
        self.console_logger = logging.getLogger('console_logger')
        self.console_logger.addHandler(console_handler)
        self.console_logger.setLevel(logging.INFO)

        if self.enable_devtools:
            # Set up Chrome DevTools Protocol (CDP) session if devtools are enabled
            self.devtools = driver.execute_cdp_cmd
            self._initialize_devtools()

        # Initialize JavaScript log storage on the page
        self._initialize_js_logging()

    def _initialize_devtools(self):
        """Initialize Chrome DevTools Protocol for network and JS event analysis"""
        try:
            # Enabling network and JavaScript console logging
            self.devtools('Network.enable', {})
            self.devtools('Log.enable', {})
            self.devtools('Runtime.enable', {})
            self.logger.info("DevTools successfully initialized.")
            self.console_logger.info("DevTools successfully initialized for JavaScript and network monitoring.")
        except Exception as e:
            self.logger.error(f"Error initializing DevTools: {e}")
            self.console_logger.error(f"Error initializing DevTools: {e}")

    def capture_network_activity(self):
        """Capture and analyze network activity for anomalies"""
        if not self.enable_devtools:
            return

        try:
            # Placeholder for capturing network activity
            self.console_logger.info("Capturing network activity is enabled. Custom event handling not yet implemented.")
        except Exception as e:
            self.logger.error(f"Error capturing network activity: {e}")
            self.console_logger.error(f"Error capturing network activity: {e}")

    def capture_js_console_logs(self):
        """Capture and analyze JavaScript console logs for errors or anomalies"""
        if not self.enable_devtools:
            return

        try:
            console_logs = self.driver.get_log("browser")
            for log_entry in console_logs:
                log_message = log_entry['message']
                if "error" in log_message.lower():
                    self.console_logger.warning(f"🚨 [JavaScript Error]: Something went wrong! The message received: '{log_message}'. Please check for potential issues on the page.")
                else:
                    self.console_logger.info(f"ℹ️ [JavaScript Log]: {log_message}")
        except Exception as e:
            self.logger.error(f"Error capturing JavaScript console logs: {e}")
            self.console_logger.error(f"Error capturing JavaScript console logs: {e}")

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
            self.console_logger.info("✅ [Detected Changes]: The page source has changed. Please review the latest content.")
            self._log_updated_text()  # Log the updated text from JavaScript changes
        else:
            self.logger.info("No changes detected in the page source.")
            self.console_logger.info("ℹ️ [No Changes]: The page content appears to be stable, with no detected changes.")
        self.previous_page_source = page_source

        # Check for success messages
        if success_message and success_message.lower() in page_source:
            self.logger.info(f"Success message detected: '{success_message}'")
            self.console_logger.info(f"✅ [Success]: The expected success message was found: '{success_message}'.")

        # Check for error keywords in the page source
        for keyword in error_keywords:
            if keyword in page_source:
                self.logger.warning(f"Error detected: keyword '{keyword}' found on the page.")
                self.console_logger.warning(f"🚨 [Error Detected]: The keyword '{keyword}' was found on the page, which may indicate an issue. Please investigate further.")

    def _initialize_js_logging(self):
        """Initialize JavaScript logging to store updates in a global variable."""
        script = "window.updatedTextLogs = [];"
        self.driver.execute_script(script)

    def _log_updated_text(self):
        """Retrieve updated text logged by JavaScript and log it to the console."""
        script = "return window.updatedTextLogs || [];"
        updated_text_logs = self.driver.execute_script(script)
        if updated_text_logs:
            self.console_logger.info("📝 [Detected Changes]: Logging changes detected from JavaScript:")
            for log in updated_text_logs:
                if log:  # Only log non-empty changes
                    self.console_logger.info(f"➡️ [JavaScript Change]: {log}")

        # Clear the logs after retrieval
        self.driver.execute_script("window.updatedTextLogs = [];")

    def poll_for_changes(self, polling_interval=2, max_attempts=10):
        """Periodically poll the page source to check for any changes.

        Args:
            polling_interval (int): Interval between polling attempts in seconds.
            max_attempts (int): Maximum number of polling attempts.
        """
        for attempt in range(max_attempts):
            time.sleep(polling_interval)
            current_page_source = self.driver.page_source.lower()
            if self.previous_page_source and self.previous_page_source != current_page_source:
                self.logger.info("Detected changes during polling.")
                self.console_logger.info("🔍 [Polling]: Detected changes during polling.")
                self._log_updated_text()
                self.previous_page_source = current_page_source
                break
            else:
                self.logger.debug(f"Polling attempt {attempt + 1}: No changes detected.")
                self.console_logger.debug(f"[Polling]: Attempt {attempt + 1}: No changes detected.")

    def compare_element_text(self, element_locator, previous_text=""):
        """Compare the text content of a specific element to detect changes.

        Args:
            element_locator (tuple): Locator tuple to find the element (e.g., (By.ID, 'element_id')).
            previous_text (str): The previous text content to compare against.
        """
        try:
            element = self.driver.find_element(*element_locator)
            current_text = element.text.strip()
            if current_text and current_text != previous_text:
                self.console_logger.info(f"🔄 [Element Text Change]: Updated text: {current_text}")
                return current_text
            return previous_text
        except Exception as e:
            self.logger.error(f"Error comparing element text: {e}")
            self.console_logger.error(f"Error comparing element text: {e}")
            return previous_text
