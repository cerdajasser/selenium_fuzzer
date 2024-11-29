import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import sys

class JavaScriptChangeDetector:
    def __init__(self, driver, enable_devtools=False):
        self.driver = driver
        self.enable_devtools = enable_devtools
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.previous_page_source = ""

        # Set up console handler for logging important information
        self.console_logger = logging.getLogger('console_logger')
        if not self.console_logger.hasHandlers():
            console_handler = logging.StreamHandler(sys.stdout)  # Output to stdout explicitly
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
            console_handler.setFormatter(console_formatter)
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
            self.devtools('Network.enable', {})
            self.devtools('Log.enable', {})
            self.devtools('Runtime.enable', {})
            self.logger.info("DevTools successfully initialized.")
            self.console_logger.info("🛠️ DevTools successfully initialized for JavaScript and network monitoring.")
        except Exception as e:
            self.logger.error(f"Error initializing DevTools: {e}")
            self.console_logger.error(f"Error initializing DevTools: {e}")

    def capture_network_activity(self):
        """Capture and analyze network activity for anomalies"""
        if not self.enable_devtools:
            return

        try:
            self.console_logger.info("🛠️ Capturing network activity is enabled. Custom event handling not yet implemented.")
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
                    self.console_logger.warning(f"🚨 [JavaScript Error]: '{log_message}'. Please check for potential issues on the page.")
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

        time.sleep(delay)
        page_source = self.driver.page_source.lower()

        if self.previous_page_source and self.previous_page_source != page_source:
            self.logger.info("Detected changes in the page source.")
            self.console_logger.info("✅ [Detected Changes]: The page source has changed. Please review the latest content.")
            self._log_updated_text()
        else:
            self.logger.info("No changes detected in the page source.")
            self.console_logger.info("ℹ️ [No Changes]: The page content appears stable.")

        self.previous_page_source = page_source

        if success_message and success_message.lower() in page_source:
            self.logger.info(f"Success message detected: '{success_message}'")
            self.console_logger.info(f"✅ [Success]: Found success message: '{success_message}'.")

        for keyword in error_keywords:
            if keyword in page_source:
                self.logger.warning(f"Error detected: keyword '{keyword}' found.")
                self.console_logger.warning(f"🚨 [Error Detected]: Keyword '{keyword}' found. Investigate further.")

    def _initialize_js_logging(self):
        """Initialize JavaScript logging to store updates in a global variable."""
        script = "window.updatedTextLogs = [];"
        self.driver.execute_script(script)

    def _log_updated_text(self):
        """Retrieve updated text logged by JavaScript and log it to the console."""
        script = "return window.updatedTextLogs || [];"
        updated_text_logs = self.driver.execute_script(script)
        if updated_text_logs:
            self.console_logger.info("📝 [Detected Changes]: JavaScript updates detected:")
            for log in updated_text_logs:
                if log:
                    self.console_logger.info(f"➡️ [JavaScript Change]: {log}")

        self.driver.execute_script("window.updatedTextLogs = [];")  # Clear logs after retrieval
