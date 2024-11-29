import logging
import time
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from urllib.parse import urlparse
import difflib
from selenium.webdriver.remote.webelement import WebElement

class Fuzzer:
    def __init__(self, driver, js_change_detector, url, track_state=True):
        """
        Initialize the Fuzzer with a given driver, JS change detector, URL, and state tracking option.
        """
        self.driver = driver
        self.url = url
        self.js_change_detector = js_change_detector
        self.track_state = track_state
        self.logger = self.setup_logger()
        self.console_logger = self.setup_console_logger()
        self.previous_state = None

        # Inject JS for capturing console logs
        self._initialize_js_logging()

    def setup_logger(self):
        """
        Set up a logger that creates a new log file for each website.
        """
        parsed_url = urlparse(self.url)
        domain = parsed_url.netloc.replace(":", "_").replace(".", "_")
        log_filename = f"fuzzing_log_{domain}_{time.strftime('%Y%m%d_%H%M%S')}.log"

        logger = logging.getLogger(f"fuzzer_{domain}")
        logger.setLevel(logging.DEBUG)

        # Create a file handler for the logger
        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(logging.DEBUG)

        # Set formatter for handlers
        formatter = logging.Formatter('[%(asctime)s] %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)

        # Add handlers to the logger
        if not any(isinstance(handler, logging.FileHandler) for handler in logger.handlers):
            logger.addHandler(file_handler)

        return logger

    def setup_console_logger(self):
        """
        Set up a console logger for more readable console output.
        """
        console_logger = logging.getLogger('console_logger')
        console_logger.setLevel(logging.INFO)

        # Create a console handler for additional output
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Set a simpler formatter for console output
        console_formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)

        # Avoid adding multiple handlers if the logger already has one
        if not console_logger.hasHandlers():
            console_logger.addHandler(console_handler)

        return console_logger

    def _initialize_js_logging(self):
        """
        Inject JavaScript code to capture all console log messages.
        """
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

    def _log_browser_console(self):
        """
        Capture and log browser console logs from the injected JavaScript.
        """
        try:
            self.console_logger.info("ℹ️ [JavaScript Log]: Attempting to retrieve browser console logs.")
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

    def detect_inputs(self):
        """
        Detect all input fields on the page.
        """
        try:
            input_fields = self.driver.find_elements(By.TAG_NAME, "input")
            suitable_fields = [field for field in input_fields if field.is_displayed() and field.is_enabled() and field.get_attribute("type") in ["text", "password", "email", "url", "number"]]
            self.logger.info(f"Found {len(suitable_fields)} suitable input elements.")
            self.console_logger.info(f"Found {len(suitable_fields)} suitable input elements on the page.")
            return suitable_fields
        except Exception as e:
            self.logger.error(f"Error detecting input fields: {e}")
            self.console_logger.error(f"Error detecting input fields: {e}")
            return []

    def fuzz_field(self, input_element, payloads, delay=1):
        """
        Fuzz a given input field with a list of payloads.

        Args:
            input_element (WebElement): The input field to fuzz.
            payloads (list): The payloads to input into the field.
            delay (int): Time in seconds to wait between fuzzing attempts.
        """
        MAX_RETRIES = 3
        before_snapshot = self.take_snapshot(elements_to_track=[input_element]) if self.track_state else None

        for payload in payloads:
            try:
                retry_count = 0
                success = False

                while retry_count < MAX_RETRIES and not success:
                    # Clear the input field using JavaScript to ensure it's empty
                    self.driver.execute_script("arguments[0].value = '';", input_element)
                    WebDriverWait(self.driver, delay).until(lambda d: self.driver.execute_script("return arguments[0].value;", input_element) == "")

                    # Set value using JavaScript to avoid front-end interference
                    self.driver.execute_script("arguments[0].value = arguments[1];", input_element, payload)
                    input_element.send_keys(Keys.TAB)
                    input_element.send_keys(Keys.ENTER)
                    WebDriverWait(self.driver, delay).until(lambda d: self.driver.execute_script("return arguments[0].value;", input_element) == payload)

                    # Verify the value
                    entered_value = self.driver.execute_script("return arguments[0].value;", input_element)
                    success = (entered_value == payload)

                    if not success:
                        retry_count += 1

                if success:
                    self.logger.info(f"Payload '{payload}' successfully entered into field '{input_element.get_attribute('name') or 'Unnamed'}'.")
                    self.console_logger.info(f"✅ Successfully entered payload '{payload}' into field '{input_element.get_attribute('name') or 'Unnamed'}'.")
                else:
                    self.logger.warning(f"Payload Verification Failed after {MAX_RETRIES} retries: '{payload}' in field '{input_element.get_attribute('name') or 'Unnamed'}'. Entered Value: '{entered_value}'")
                    self.console_logger.warning(f"⚠️ Failed to verify payload '{payload}' in field '{input_element.get_attribute('name') or 'Unnamed'}' after {MAX_RETRIES} retries.")

                # Check for JavaScript changes after input
                self.js_change_detector.check_for_js_changes(delay=delay)
                self.js_change_detector.capture_js_console_logs()

                # Retrieve and log browser console logs
                self._log_browser_console()

            except (NoSuchElementException, TimeoutException, WebDriverException) as e:
                self.logger.error(f"Error inserting payload into field '{input_element.get_attribute('name') or 'Unnamed'}': {e}")
                self.console_logger.error(f"❌ Error inserting payload into field '{input_element.get_attribute('name') or 'Unnamed'}': {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error inserting payload into field '{input_element.get_attribute('name') or 'Unnamed'}': {e}")
                self.console_logger.error(f"❌ Unexpected error inserting payload into field '{input_element.get_attribute('name') or 'Unnamed'}': {e}")

        after_snapshot = self.take_snapshot(elements_to_track=[input_element]) if self.track_state else None
        if self.track_state:
            self.compare_snapshots(before_snapshot, after_snapshot)

    def fuzz_dropdowns(self, selector="select", delay=1):
        """
        Detect dropdown elements using the provided selector and interact with them.

        Args:
            selector (str): CSS selector to locate dropdowns.
            delay (int): Time in seconds to wait between dropdown interactions.
        """
        try:
            dropdown_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            self.logger.info(f"Found {len(dropdown_elements)} dropdown elements using selector '{selector}'.")
            self.console_logger.info(f"Found {len(dropdown_elements)} dropdown elements on the page.")

            for idx, dropdown_element in enumerate(dropdown_elements):
                self.logger.info(f"Interacting with dropdown {idx + 1} on the page.")
                self.console_logger.info(f"👉 Interacting with dropdown {idx + 1} on the page.")
                self.fuzz_dropdown(dropdown_element, delay)

        except Exception as e:
            self.logger.error(f"Error detecting dropdowns: {e}")
            self.console_logger.error(f"❌ Error detecting dropdowns: {e}")

    def fuzz_dropdown(self, dropdown_element, delay=1):
        """
        Interact with a dropdown element by selecting each option.

        Args:
            dropdown_element (WebElement): The dropdown element to fuzz.
            delay (int): Time in seconds to wait between selections.
        """
        before_snapshot = self.take_snapshot(elements_to_track=[dropdown_element]) if self.track_state else None

        try:
            select = Select(dropdown_element)
            options = select.options
            for index, option in enumerate(options):
                select.select_by_index(index)
                self.logger.info(f"Selected option '{option.text}' from dropdown.")
                self.console_logger.info(f"✅ Selected option '{option.text}' from dropdown.")
                WebDriverWait(self.driver, delay).until(lambda d: True)

                # Check for JavaScript changes after interacting with dropdown
                self.js_change_detector.check_for_js_changes(delay=delay)
                self.js_change_detector.capture_js_console_logs()

                # Retrieve and log browser console logs
                self._log_browser_console()

        except Exception as e:
            self.logger.error(f"Error fuzzing dropdown: {e}")
            self.console_logger.error(f"❌ Error fuzzing dropdown: {e}")

        after_snapshot = self.take_snapshot(elements_to_track=[dropdown_element]) if self.track_state else None
        if self.track_state:
            self.compare_snapshots(before_snapshot, after_snapshot)

    # The methods `take_snapshot` and `compare_snapshots` remain unchanged
