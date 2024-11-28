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
        console_formatter = CustomFormatter()
        console_handler.setFormatter(console_formatter)
        self.console_logger = logging.getLogger('console_logger')
        self.console_logger.addHandler(console_handler)
        self.console_logger.setLevel(logging.INFO)

        # Initialize JavaScript log storage on the page
        self._initialize_js_logging()

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
            self.console_logger.info("🔄 Page changes detected!")
            self._log_updated_text()  # Log the updated text from JavaScript changes
        else:
            self.console_logger.info("✅ No changes detected on the page.")
        self.previous_page_source = page_source

        # Check for success messages
        if success_message and success_message.lower() in page_source:
            self.console_logger.info(f"🟢 Success: Found the message '{success_message}' on the page.")

        # Check for error keywords in the page source
        for keyword in error_keywords:
            if keyword in page_source:
                self.console_logger.warning(f"⚠️ Warning: Keyword '{keyword}' found on the page!")

    def observe_element_changes(self, element_locator, timeout=10):
        """Observe specific elements for changes using Selenium's explicit waits.

        Args:
            element_locator (tuple): Locator tuple to find the element (e.g., (By.ID, 'element_id')).
            timeout (int): Time in seconds to wait for the element to change.
        """
        try:
            WebDriverWait(self.driver, timeout).until(EC.staleness_of(self.driver.find_element(*element_locator)))
            self.console_logger.info("🔄 Detected a change in the targeted element.")
        except TimeoutException:
            self.console_logger.info("⏱️ No change detected in the targeted element within the timeout period.")

    def add_mutation_observer(self, target_selector):
        """Inject JavaScript to add a MutationObserver to the target element.

        Args:
            target_selector (str): CSS selector for the target element to observe.
        """
        script = f"""
        var targetNode = document.querySelector('{target_selector}');
        if (targetNode) {{
            var config = {{ attributes: true, childList: true, subtree: true, characterData: true }};
            var callback = function(mutationsList, observer) {{
                mutationsList.forEach(function(mutation) {{
                    if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {{
                        mutation.addedNodes.forEach(function(node) {{
                            if (node.nodeType === Node.TEXT_NODE || node.nodeType === Node.ELEMENT_NODE) {{
                                var logMessage = 'Mutation detected: ' + node.textContent.trim();
                                console.log(logMessage);
                                window.updatedTextLogs.push(logMessage);
                            }}
                        }});
                    }} else if (mutation.type === 'attributes') {{
                        var updatedAttribute = 'The ' + mutation.attributeName + ' attribute was modified. Updated value: ' + mutation.target.getAttribute(mutation.attributeName);
                        console.log(updatedAttribute);
                        window.updatedTextLogs.push(updatedAttribute);
                    }} else if (mutation.type === 'characterData') {{
                        var charDataMessage = 'Character data changed: ' + mutation.target.data;
                        console.log(charDataMessage);
                        window.updatedTextLogs.push(charDataMessage);
                    }}
                }});
            }};
            var observer = new MutationObserver(callback);
            observer.observe(targetNode, config);
            console.log('MutationObserver added to target node: {target_selector}');
        }} else {{
            console.log('Target node not found: {target_selector}');
        }}
        """
        self.driver.execute_script(script)
        self.console_logger.info(f"👀 MutationObserver added to target element: {target_selector}")

    def add_observers_for_dynamic_elements(self):
        """Add mutation observers to elements that are known to change dynamically."""
        # Add observer for the validity display span
        self.add_mutation_observer(".input-item__validity-display")
        # Add observer for the form controls that might change dynamically
        self.add_mutation_observer(".input-item__controls")
        self.add_mutation_observer(".input-item__display-input")
        # Add observer for changes in the <pre> tag
        self.add_mutation_observer("pre")

    def _initialize_js_logging(self):
        """Initialize JavaScript logging to store updates in a global variable."""
        script = "window.updatedTextLogs = [];"
        self.driver.execute_script(script)

    def _log_updated_text(self):
        """Retrieve updated text logged by JavaScript and log it to the console."""
        script = "return window.updatedTextLogs || [];"
        updated_text_logs = self.driver.execute_script(script)
        if updated_text_logs:
            self.console_logger.info("📋 Logging detected changes:")
            for log in updated_text_logs:
                if log:  # Only log non-empty changes
                    self.console_logger.info(f"  ➜ {log}")

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
                self.console_logger.info("🔄 Detected changes during polling.")
                self._log_updated_text()
                self.previous_page_source = current_page_source
                break
            else:
                self.console_logger.debug(f"Polling attempt {attempt + 1}: No changes detected.")

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
                self.console_logger.info(f"🔄 Element text updated: {current_text}")
                return current_text
            return previous_text
        except Exception as e:
            self.logger.error(f"Error comparing element text: {e}")
            return previous_text

class CustomFormatter(logging.Formatter):
    """Custom Formatter for making console logs more human-readable."""

    grey = "\x1b[38;20m"
    green = "\x1b[32;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(levelname)s - %(message)s"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: green + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, self.format)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)
