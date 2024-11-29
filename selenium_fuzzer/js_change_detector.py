import logging
import time
from selenium.common.exceptions import WebDriverException
import sys

class JavaScriptChangeDetector:
    def __init__(self, driver, enable_devtools=False):
        """
        Initialize the JavaScriptChangeDetector with a given Selenium WebDriver.
        """
        self.driver = driver
        self.enable_devtools = enable_devtools
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        # Set up console handler for logging important information
        self.console_logger = logging.getLogger('console_logger')
        if not self.console_logger.hasHandlers():
            console_handler = logging.StreamHandler(sys.stdout)  # Output to stdout explicitly
            console_handler.setLevel(logging.DEBUG)
            console_formatter = logging.Formatter('[%(asctime)s] %(name)s - %(levelname)s: %(message)s')
            console_handler.setFormatter(console_formatter)
            self.console_logger.addHandler(console_handler)
        self.console_logger.setLevel(logging.DEBUG)

        # Initialize Chrome DevTools Protocol (CDP) session if devtools are enabled
        if self.enable_devtools:
            self.devtools = driver.execute_cdp_cmd
            self._initialize_devtools()

        # Inject JavaScript logging initialization to capture console logs
        self._initialize_js_logging()

    def _initialize_devtools(self):
        """Initialize Chrome DevTools Protocol for network and JS event analysis"""
        try:
            self.devtools('Network.enable', {})
            self.devtools('Log.enable', {})
            self.devtools('Runtime.enable', {})
            self.logger.info("DevTools successfully initialized.")
            self.console_logger.info("🛠️ DevTools successfully initialized for JavaScript and network monitoring.")
        except WebDriverException as e:
            self.logger.error(f"Error initializing DevTools: {e}")
            self.console_logger.error(f"Error initializing DevTools: {e}")

    def _initialize_js_logging(self):
        """
        Inject JavaScript code to capture all console log messages.
        """
        try:
            script = """
                (function() {
                    var oldLog = console.log;
                    var oldError = console.error;
                    window.loggedMessages = [];
                    console.log = function(message) {
                        window.loggedMessages.push({level: "INFO", message: message});
                        oldLog.apply(console, arguments);
                    };
                    console.error = function(message) {
                        window.loggedMessages.push({level: "ERROR", message: message});
                        oldError.apply(console, arguments);
                    };
                })();
            """
            self.driver.execute_script(script)
            self.logger.info("JavaScript for logging successfully injected.")
            self.console_logger.info("ℹ️ JavaScript for logging successfully injected.")
        except WebDriverException as e:
            self.logger.error(f"Error injecting JavaScript for logging: {e}")
            self.console_logger.error(f"Error injecting JavaScript for logging: {e}")

    def capture_js_console_logs(self):
        """Capture and analyze JavaScript console logs for errors or anomalies"""
        try:
            # Get logged messages from the browser console via injected JavaScript
            script = "return window.loggedMessages || [];"
            console_logs = self.driver.execute_script(script)

            if not console_logs:
                self.console_logger.info("ℹ️ [JavaScript Log]: No console logs detected.")
            else:
                for log_entry in console_logs:
                    log_level = log_entry.get('level', '').upper()
                    log_message = log_entry.get('message', '')

                    if log_level == "ERROR":
                        self.logger.error(f"JavaScript Error: {log_message}")
                        self.console_logger.error(f"🚨 [JavaScript Error]: {log_message}")
                    else:
                        self.logger.info(f"JavaScript Log: {log_message}")
                        self.console_logger.info(f"ℹ️ [JavaScript Log]: {log_message}")

            # Clear the logged messages after retrieval
            self.driver.execute_script("window.loggedMessages = [];")
            self.console_logger.info("ℹ️ [JavaScript Log]: Console log retrieval completed.")
        except WebDriverException as e:
            self.logger.error(f"Error capturing JavaScript console logs: {e}")
            self.console_logger.error(f"Error capturing JavaScript console logs: {e}")

    def check_for_js_changes(self, success_message=None, error_keywords=None, delay=2):
        """
        Check for JavaScript changes or error messages on the page.

        Args:
            success_message (str): The expected success message after changes are applied.
            error_keywords (list of str): List of keywords indicating errors.
            delay (int): Time in seconds to wait for changes to appear.
        """
        if error_keywords is None:
            error_keywords = ["error", "failed", "invalid"]

        time.sleep(delay)
        try:
            page_source = self.driver.page_source.lower()

            if hasattr(self, 'previous_page_source') and self.previous_page_source != page_source:
                self.logger.info("Detected changes in the page source.")
                self.console_logger.info("✅ [Detected Changes]: The page source has changed. Please review the latest content.")
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

        except WebDriverException as e:
            self.logger.error(f"Error checking for JavaScript changes: {e}")
            self.console_logger.error(f"Error checking for JavaScript changes: {e}")
