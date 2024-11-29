import logging
import time
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException, ElementNotInteractableException
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
        Detect all suitable input fields on the page.
        """
        try:
            input_fields = self.driver.find_elements(By.TAG_NAME, "input")

            # Filter the fields to include only those suitable for text input
            suitable_fields = []
            for field in input_fields:
                field_type = field.get_attribute("type").lower() if field.get_attribute("type") else "text"
                if field_type in ["text", "email", "password", "search", "tel", "url"]:
                    suitable_fields.append(field)

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
        """
        MAX_RETRIES = 3

        before_snapshot = self.take_snapshot(elements_to_track=[input_element]) if self.track_state else None

        for payload in payloads:
            try:
                retry_count = 0
                success = False

                while retry_count < MAX_RETRIES and not success:
                    # Check if the element is interactable before fuzzing
                    if not input_element.is_displayed() or not input_element.is_enabled():
                        self.logger.warning(f"Field '{input_element.get_attribute('name') or 'Unnamed'}' is not interactable. Skipping.")
                        self.console_logger.warning(f"⚠️ Field '{input_element.get_attribute('name') or 'Unnamed'}' is not interactable. Skipping.")
                        return

                    # Clear the input field using JavaScript to ensure it's empty
                    self.driver.execute_script("arguments[0].value = '';", input_element)
                    WebDriverWait(self.driver, delay).until(lambda d: self.driver.execute_script("return arguments[0].value;", input_element) == "")

                    # Set value using JavaScript to avoid front-end interference
                    self.driver.execute_script("arguments[0].value = arguments[1];", input_element, payload)
                    input_element.send_keys(Keys.TAB)
                    input_element.send_keys(Keys.ENTER)

                    # Verify the value using JavaScript
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

                # Check for JavaScript changes after input
                self.js_change_detector.check_for_js_changes(delay=delay)
                self.js_change_detector.capture_js_console_logs()

            except (NoSuchElementException, TimeoutException, WebDriverException, ElementNotInteractableException) as e:
                self.logger.error(f"Error Inserting Payload into Field '{input_element.get_attribute('name') or 'Unnamed'}': {e}")
                self.console_logger.error(f"❌ Error inserting payload into field '{input_element.get_attribute('name') or 'Unnamed'}': {e}")
            except Exception as e:
                self.logger.error(f"Unexpected Error Inserting Payload into Field '{input_element.get_attribute('name') or 'Unnamed'}': {e}")
                self.console_logger.error(f"❌ Unexpected error inserting payload into field '{input_element.get_attribute('name') or 'Unnamed'}': {e}")

        after_snapshot = self.take_snapshot(elements_to_track=[input_element]) if self.track_state else None
        if self.track_state:
            self.compare_snapshots(before_snapshot, after_snapshot)

    def run_fuzz_fields(self, delay=1):
        try:
            input_fields = self.detect_inputs()
            if not input_fields:
                self.logger.warning("No suitable input fields detected for fuzzing.")
                self.console_logger.warning("⚠️ No suitable input fields detected for fuzzing.")
                return

            print("Detected input fields:")
            for idx, field in enumerate(input_fields):
                field_type = field.get_attribute("type") or "unknown"
                field_name = field.get_attribute("name") or "Unnamed"
                print(f"{idx}: {field_name} (type: {field_type})")

            selected_indices = input("Enter the indices of the fields to fuzz (comma-separated): ")
            selected_indices = [int(idx.strip()) for idx in selected_indices.split(",") if idx.strip().isdigit()]

            payloads = ["test@example.com", "123456", "' OR 1=1 --"]

            for idx in selected_indices:
                if 0 <= idx < len(input_fields):
                    self.fuzz_field(input_fields[idx], payloads, delay)
        except Exception as e:
            self.logger.error(f"Unexpected error during input fuzzing: {e}")
            self.console_logger.error(f"❌ Unexpected error during input fuzzing: {e}")

    def run_fuzz(self, delay=1):
        try:
            self.run_fuzz_fields(delay)
            self.detect_dropdowns(delay=delay)
        finally:
            self.driver.quit()
