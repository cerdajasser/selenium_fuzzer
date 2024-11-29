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

        # Create a file handler for the logger
        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(logging.DEBUG)

        # Set formatter for handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)

        if not any(isinstance(handler, logging.FileHandler) and handler.baseFilename == file_handler.baseFilename for handler in logger.handlers):
            logger.addHandler(file_handler)

        return logger

    def setup_console_logger(self):
        console_logger = logging.getLogger('console_logger')
        console_logger.setLevel(logging.INFO)

        # Create a console handler for additional output
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)

        if not console_logger.hasHandlers():
            console_logger.addHandler(console_handler)

        return console_logger

    def take_snapshot(self, elements_to_track=None):
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
            return snapshot
        except Exception as e:
            self.logger.error(f"Error taking snapshot of the page state: {e}")
            return None

    def compare_snapshots(self, before_snapshot, after_snapshot):
        if not before_snapshot or not after_snapshot:
            self.logger.warning("Cannot compare snapshots; one or both snapshots are None.")
            return

        if before_snapshot.get('page_source') and after_snapshot.get('page_source'):
            before_source = before_snapshot['page_source']
            after_source = after_snapshot['page_source']

            if before_source != after_source:
                self.logger.info("Detected changes in the full page source.")
                self.console_logger.info("Detected changes in the full page source.")

                diff = difflib.unified_diff(
                    before_source.splitlines(),
                    after_source.splitlines(),
                    fromfile='Before Fuzzing',
                    tofile='After Fuzzing',
                    lineterm=''
                )
                diff_text = '\n'.join(diff)
                self.logger.debug(f"Page source differences:\n{diff_text}")
                self.console_logger.info("Changes detected in the page source:\n" + diff_text)
            else:
                self.logger.info("No changes detected in the full page source.")
                self.console_logger.info("No changes detected in the full page source.")

        for element_id in before_snapshot['elements']:
            before_element = before_snapshot['elements'].get(element_id)
            after_element = after_snapshot['elements'].get(element_id)
            if before_element != after_element:
                self.logger.info(f"Detected changes in element '{element_id}'.")
                self.console_logger.info(f"⚠️ Detected changes in element '{element_id}'.")
            else:
                self.logger.info(f"No changes detected in element '{element_id}'.")
                self.console_logger.info(f"No changes detected in element '{element_id}'.")

        if before_snapshot['current_url'] != after_snapshot['current_url']:
            self.logger.warning(f"URL changed from {before_snapshot['current_url']} to {after_snapshot['current_url']}.")
            self.console_logger.warning(f"⚠️ URL changed from {before_snapshot['current_url']} to {after_snapshot['current_url']}.")

        if before_snapshot['cookies'] != after_snapshot['cookies']:
            self.logger.warning("Cookies have changed between snapshots.")
            self.console_logger.warning("⚠️ Cookies have changed between snapshots.")

    def detect_inputs(self):
        try:
            input_fields = [field for field in self.driver.find_elements(By.TAG_NAME, "input") if field.is_displayed() and field.is_enabled() and field.get_attribute("type") not in ['hidden']]
            self.logger.info(f"Found {len(input_fields)} suitable input elements on the page.")
            self.console_logger.info(f"Found {len(input_fields)} suitable input elements on the page.")
            return input_fields
        except Exception as e:
            self.logger.error(f"Error detecting input fields: {e}")
            self.console_logger.error(f"Error detecting input fields: {e}")
            return []

    def fuzz_field(self, input_element, payloads, delay=1):
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
                self.logger.error(f"Error inserting payload into field '{input_element.get_attribute('name') or 'Unnamed'}': {e}")
                self.console_logger.error(f"❌ Error inserting payload into field '{input_element.get_attribute('name') or 'Unnamed'}': {e}")
                continue
            except Exception as e:
                self.logger.error(f"Unexpected error inserting payload into field '{input_element.get_attribute('name') or 'Unnamed'}': {e}")
                self.console_logger.error(f"❌ Unexpected error inserting payload into field '{input_element.get_attribute('name') or 'Unnamed'}': {e}")
                continue

        after_snapshot = self.take_snapshot(elements_to_track=[input_element]) if self.track_state else None
        if self.track_state:
            self.compare_snapshots(before_snapshot, after_snapshot)

    def detect_dropdowns(self, delay=1):
        try:
            dropdown_elements = [el for el in self.driver.find_elements(By.TAG_NAME, "select") if el.is_displayed() and el.is_enabled()]
            self.logger.info(f"Found {len(dropdown_elements)} dropdown elements on the page.")
            self.console_logger.info(f"Found {len(dropdown_elements)} dropdown elements on the page.")

            if not dropdown_elements:
                self.logger.warning(f"No dropdown elements found on the page.")
                self.console_logger.warning(f"⚠️ No dropdown elements found on the page.")
                return

            for idx, dropdown_element in enumerate(dropdown_elements):
                self.logger.info(f"Interacting with dropdown {idx + 1} on the page.")
                self.console_logger.info(f"👉 Interacting with dropdown {idx + 1} on the page.")
                self.fuzz_dropdown(dropdown_element, delay)

        except Exception as e:
            self.logger.error(f"Error detecting dropdowns: {e}")
            self.console_logger.error(f"❌ Error detecting dropdowns: {e}")

    def fuzz_dropdown(self, dropdown_element, delay=1):
        before_snapshot = self.take_snapshot(elements_to_track=[dropdown_element]) if self.track_state else None
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

        after_snapshot = self.take_snapshot(elements_to_track=[dropdown_element]) if self.track_state else None
        if self.track_state:
            self.compare_snapshots(before_snapshot, after_snapshot)

    def run_fuzz(self, delay=1):
        try:
            self.previous_state = self.take_snapshot() if self.track_state else None
            self.run_fuzz_fields(delay)
            self.detect_dropdowns(delay=delay)
            self.run_click_elements(delay)
        finally:
            self.driver.quit()
