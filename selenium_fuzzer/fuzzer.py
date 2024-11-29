import logging
import time
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from urllib.parse import urlparse
import difflib  # For comparing page sources
from selenium.webdriver.remote.webelement import WebElement
import sys

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
        self.previous_state = None  # For storing snapshots of the page

    def setup_logger(self):
        parsed_url = urlparse(self.url)
        domain = parsed_url.netloc.replace(":", "_").replace(".", "_")  # Replace dots and colons for filename compatibility
        log_filename = f"fuzzing_log_{domain}_{time.strftime('%Y%m%d_%H%M%S')}.log"

        logger = logging.getLogger(f"fuzzer_{domain}")
        logger.setLevel(logging.DEBUG)

        # Create a file handler for the logger
        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(logging.DEBUG)

        # Set formatter for handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)

        # Add handlers to the logger if not already added
        if not logger.handlers:
            logger.addHandler(file_handler)

        return logger

    def setup_console_logger(self):
        console_logger = logging.getLogger('console_logger')
        console_logger.setLevel(logging.INFO)

        # Create a console handler for additional output
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # Set a simpler formatter for console output
        console_formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)

        # Add the console handler if it hasn't been added already
        if not console_logger.handlers:
            console_logger.addHandler(console_handler)

        return console_logger

    def take_snapshot(self, elements_to_track=None):
        """Take a snapshot of the page state."""
        try:
            page_source = self.driver.page_source if elements_to_track is None else None
            current_url = self.driver.current_url
            cookies = self.driver.get_cookies()
            element_snapshots = {}

            if elements_to_track:
                for element in elements_to_track:
                    if isinstance(element, WebElement):
                        try:
                            element_id = element.get_attribute("id") or element.get_attribute("name")
                            element_snapshots[element_id] = element.get_attribute("outerHTML")
                        except Exception as e:
                            self.logger.error(f"Error taking element snapshot: {e}")

            snapshot = {
                'page_source': page_source,
                'current_url': current_url,
                'cookies': cookies,
                'elements': element_snapshots
            }

            self.logger.debug(f"Snapshot taken for URL: {current_url}")
            self.console_logger.info("Snapshot taken of the current page state.")
            sys.stdout.flush()  # Flush to ensure immediate output
            return snapshot
        except Exception as e:
            self.logger.error(f"Error taking snapshot of the page state: {e}")
            return None

    def detect_inputs(self):
        """Detect all input fields on the page."""
        try:
            input_fields = self.driver.find_elements(By.TAG_NAME, "input")
            self.logger.info(f"Found {len(input_fields)} input elements.")
            self.console_logger.info(f"Found {len(input_fields)} input elements on the page.")
            sys.stdout.flush()  # Ensure output is flushed
            return input_fields
        except Exception as e:
            self.logger.error(f"Error detecting input fields: {e}")
            self.console_logger.error(f"Error detecting input fields: {e}")
            sys.stdout.flush()  # Ensure output is flushed
            return []

    def fuzz_field(self, input_element, payloads, delay=1):
        """Fuzz a given input field with a list of payloads."""
        MAX_RETRIES = 3

        before_snapshot = self.take_snapshot(elements_to_track=[input_element]) if self.track_state else None

        for payload in payloads:
            try:
                retry_count = 0
                success = False

                while retry_count < MAX_RETRIES and not success:
                    # Clear the input field using JavaScript to ensure it's empty
                    self.driver.execute_script("arguments[0].value = '';", input_element)

                    # Use explicit wait to ensure JavaScript clearing is complete
                    WebDriverWait(self.driver, delay).until(lambda d: self.driver.execute_script("return arguments[0].value;", input_element) == "")

                    # Set value using JavaScript to avoid front-end interference
                    self.driver.execute_script("arguments[0].value = arguments[1];", input_element, payload)

                    # Send TAB and ENTER to trigger potential events
                    input_element.send_keys(Keys.TAB)
                    input_element.send_keys(Keys.ENTER)

                    # Use explicit wait to verify value using JavaScript
                    WebDriverWait(self.driver, delay).until(lambda d: self.driver.execute_script("return arguments[0].value;", input_element) == payload)

                    entered_value = self.driver.execute_script("return arguments[0].value;", input_element)
                    if entered_value == payload:
                        success = True
                    else:
                        retry_count += 1

                if success:
                    self.logger.info(f"✅ Successfully entered payload '{payload}' into field '{input_element.get_attribute('name') or 'Unnamed'}'.")
                    self.console_logger.info(f"✅ Successfully entered payload '{payload}' into field '{input_element.get_attribute('name') or 'Unnamed'}'.")
                else:
                    self.logger.warning(f"⚠️ Failed to verify payload '{payload}' in field '{input_element.get_attribute('name') or 'Unnamed'}' after {MAX_RETRIES} retries.")
                    self.console_logger.warning(f"⚠️ Failed to verify payload '{payload}' in field '{input_element.get_attribute('name') or 'Unnamed'}' after {MAX_RETRIES} retries.")

                self.js_change_detector.check_for_js_changes(delay=delay)
                self.js_change_detector.capture_js_console_logs()  # Capture JS logs after fuzzing
                sys.stdout.flush()  # Ensure output is flushed

            except (NoSuchElementException, TimeoutException, WebDriverException) as e:
                self.logger.error(f"❌ Error inserting payload into field '{input_element.get_attribute('name') or 'Unnamed'}': {e}")
                self.console_logger.error(f"❌ Error inserting payload into field '{input_element.get_attribute('name') or 'Unnamed'}': {e}")
                sys.stdout.flush()  # Ensure output is flushed
            except Exception as e:
                self.logger.error(f"❌ Unexpected error inserting payload into field '{input_element.get_attribute('name') or 'Unnamed'}': {e}")
                self.console_logger.error(f"❌ Unexpected error inserting payload into field '{input_element.get_attribute('name') or 'Unnamed'}': {e}")
                sys.stdout.flush()  # Ensure output is flushed

        after_snapshot = self.take_snapshot(elements_to_track=[input_element]) if self.track_state else None
        if self.track_state:
            self.compare_snapshots(before_snapshot, after_snapshot)

    def detect_dropdowns(self, selector="select", delay=10):
        """Detect dropdown elements using the provided selector and interact with them."""
        try:
            dropdown_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            self.logger.info(f"Found {len(dropdown_elements)} dropdown elements using selector '{selector}'.")
            self.console_logger.info(f"Found {len(dropdown_elements)} dropdown elements using selector '{selector}'.")
            sys.stdout.flush()  # Ensure output is flushed

            if not dropdown_elements:
                self.logger.warning(f"No dropdown elements found using selector '{selector}'.")
                self.console_logger.warning(f"⚠️ No dropdown elements found using selector '{selector}'.")
                sys.stdout.flush()  # Ensure output is flushed
                return

            for idx, dropdown_element in enumerate(dropdown_elements):
                self.logger.info(f"👉 Interacting with dropdown {idx + 1} on the page.")
                self.console_logger.info(f"👉 Interacting with dropdown {idx + 1} on the page.")
                sys.stdout.flush()  # Ensure output is flushed
                self.fuzz_dropdown(dropdown_element, delay)

        except Exception as e:
            self.logger.error(f"❌ Error detecting dropdowns: {e}")
            self.console_logger.error(f"❌ Error detecting dropdowns: {e}")
            sys.stdout.flush()  # Ensure output is flushed

    def fuzz_dropdown(self, dropdown_element, delay=1):
        """Interact with a dropdown element by selecting each option."""
        try:
            select = Select(dropdown_element)
            options = select.options
            for index, option in enumerate(options):
                # Select each option by index
                select.select_by_index(index)
                self.logger.info(f"✅ Selected option '{option.text}' from dropdown.")
                self.console_logger.info(f"✅ Selected option '{option.text}' from dropdown.")

                # Use explicit wait to ensure JavaScript changes are applied
                WebDriverWait(self.driver, delay).until(lambda d: True)

                self.js_change_detector.check_for_js_changes(delay=delay)
                self.js_change_detector.capture_js_console_logs()  # Capture JS logs after each option is selected
                sys.stdout.flush()  # Ensure output is flushed

        except Exception as e:
            self.logger.error(f"❌ Error fuzzing dropdown: {e}")
            self.console_logger.error(f"❌ Error fuzzing dropdown: {e}")
            sys.stdout.flush()  # Ensure output is flushed

    def run_fuzz(self, delay=1):
        """Main method to run the fuzzing operation, including input fields, dropdowns, and clickable elements."""
        try:
            self.previous_state = self.take_snapshot() if self.track_state else None  # Initial snapshot
            self.detect_inputs()
            self.detect_dropdowns(delay=delay)
        finally:
            self.driver.quit()
