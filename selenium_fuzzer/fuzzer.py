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
        domain = parsed_url.netloc.replace(":", "_").replace(".", "_")
        log_filename = f"fuzzing_log_{domain}_{time.strftime('%Y%m%d_%H%M%S')}.log"

        logger = logging.getLogger(f"fuzzer_{domain}")
        logger.setLevel(logging.DEBUG)

        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)

        if not any(isinstance(handler, logging.FileHandler) and handler.baseFilename == file_handler.baseFilename for handler in logger.handlers):
            logger.addHandler(file_handler)

        return logger

    def setup_console_logger(self):
        console_logger = logging.getLogger('console_logger')
        console_logger.setLevel(logging.INFO)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)

        if not console_logger.hasHandlers():
            console_logger.addHandler(console_handler)

        return console_logger

    def detect_inputs(self):
        """
        Detect all input fields on the page.
        """
        try:
            input_fields = self.driver.find_elements(By.TAG_NAME, "input")
            self.logger.info(f"Found {len(input_fields)} input elements.")
            self.console_logger.info(f"Found {len(input_fields)} input elements on the page.")
            return input_fields
        except Exception as e:
            self.logger.error(f"Error detecting input fields: {e}")
            self.console_logger.error(f"Error detecting input fields: {e}")
            return []

    def fuzz_field(self, input_element, payloads, delay=1):
        """
        Fuzz a given input field with a list of payloads.
        """
        MAX_RETRIES = 3

        before_snapshot = self.take_snapshot(elements_to_track=[input_element]) if self.track_state else None

        for payload in payloads:
            try:
                retry_count = 0
                success = False

                while retry_count < MAX_RETRIES and not success:
                    self.driver.execute_script("arguments[0].value = '';", input_element)
                    WebDriverWait(self.driver, delay).until(lambda d: self.driver.execute_script("return arguments[0].value;", input_element) == "")

                    self.driver.execute_script("arguments[0].value = arguments[1];", input_element, payload)
                    input_element.send_keys(Keys.TAB)
                    input_element.send_keys(Keys.ENTER)

                    WebDriverWait(self.driver, delay).until(lambda d: self.driver.execute_script("return arguments[0].value;", input_element) == payload)

                    entered_value = self.driver.execute_script("return arguments[0].value;", input_element)

                    if entered_value == payload:
                        success = True
                    else:
                        retry_count += 1

                if success:
                    self.logger.info(f"Payload '{payload}' successfully entered into field '{input_element.get_attribute('name') or 'Unnamed'}'.")
                    self.console_logger.info(f"✅ Successfully entered payload '{payload}' into field '{input_element.get_attribute('name') or 'Unnamed'}'.")
                else:
                    self.logger.warning(f"Payload Verification Failed after {MAX_RETRIES} retries: '{payload}' in field '{input_element.get_attribute('name') or 'Unnamed'}'. Entered Value: '{entered_value}'")
                    self.console_logger.warning(f"⚠️ Failed to verify payload '{payload}' in field '{input_element.get_attribute('name') or 'Unnamed'}' after {MAX_RETRIES} retries.")

                self.js_change_detector.check_for_js_changes(delay=delay)
                self.js_change_detector.capture_js_console_logs()

            except (NoSuchElementException, TimeoutException, WebDriverException) as e:
                self.logger.error(f"Error Inserting Payload into Field '{input_element.get_attribute('name') or 'Unnamed'}': {e}")
                self.console_logger.error(f"❌ Error inserting payload into field '{input_element.get_attribute('name') or 'Unnamed'}': {e}")
            except Exception as e:
                self.logger.error(f"Unexpected Error Inserting Payload into Field '{input_element.get_attribute('name') or 'Unnamed'}': {e}")
                self.console_logger.error(f"❌ Unexpected error inserting payload into field '{input_element.get_attribute('name') or 'Unnamed'}': {e}")

        after_snapshot = self.take_snapshot(elements_to_track=[input_element]) if self.track_state else None
        if self.track_state:
            self.compare_snapshots(before_snapshot, after_snapshot)

    def detect_dropdowns(self, selector="select", delay=10):
        try:
            dropdown_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            self.logger.info(f"Found {len(dropdown_elements)} dropdown elements using selector '{selector}'.")
            self.console_logger.info(f"Found {len(dropdown_elements)} dropdown elements using selector '{selector}'.")

            if not dropdown_elements:
                self.logger.warning(f"No dropdown elements found using selector '{selector}'.")
                self.console_logger.warning(f"⚠️ No dropdown elements found using selector '{selector}'.")
                return

            for idx, dropdown_element in enumerate(dropdown_elements):
                self.logger.info(f"Interacting with dropdown {idx + 1} on the page.")
                self.console_logger.info(f"👉 Interacting with dropdown {idx + 1} on the page.")
                self.fuzz_dropdown(dropdown_element, delay)

        except Exception as e:
            self.logger.error(f"Error detecting dropdowns: {e}")
            self.console_logger.error(f"❌ Error detecting dropdowns: {e}")

    def fuzz_dropdown(self, dropdown_element, delay=1):
        try:
            select = Select(dropdown_element)
            options = select.options
            for index, option in enumerate(options):
                select.select_by_index(index)
                self.logger.info(f"Selected option '{option.text}' from dropdown.")
                self.console_logger.info(f"✅ Selected option '{option.text}' from dropdown.")
                WebDriverWait(self.driver, delay).until(lambda d: True)
                self.js_change_detector.check_for_js_changes(delay=delay)
                self.js_change_detector.capture_js_console_logs()

        except Exception as e:
            self.logger.error(f"Error fuzzing dropdown: {e}")
            self.console_logger.error(f"❌ Error fuzzing dropdown: {e}")

    def take_snapshot(self, elements_to_track=None):
        # Existing snapshot code
        pass

    def compare_snapshots(self, before_snapshot, after_snapshot):
        # Existing comparison code
        pass

    def run_fuzz_fields(self, delay=1):
        try:
            input_fields = self.detect_inputs()
            for input_element in input_fields:
                payloads = ["test@example.com", "123456", "' OR 1=1 --"]
                self.fuzz_field(input_element, payloads, delay)
        except Exception as e:
            self.logger.error(f"Unexpected error during input fuzzing: {e}")
            self.console_logger.error(f"❌ Unexpected error during input fuzzing: {e}")

    def run_fuzz(self, delay=1):
        try:
            self.run_fuzz_fields(delay)
            self.detect_dropdowns(delay=delay)
            self.run_click_elements(delay)
        finally:
            self.driver.quit()

