import logging
import os
import time
import difflib
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException, StaleElementReferenceException
from urllib.parse import urlparse
from selenium.webdriver.remote.webelement import WebElement
from selenium_fuzzer.config import Config
from selenium_fuzzer.utils import switch_to_iframe

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

    def setup_logger(self):
        """
        Set up a logger that creates a new log file for each website.
        """
        parsed_url = urlparse(self.url)
        domain = parsed_url.netloc.replace(":", "_").replace(".", "_")
        log_filename = os.path.join(Config.LOG_FOLDER, f"fuzzing_log_{domain}_{time.strftime('%Y%m%d_%H%M%S')}.log")

        logger = logging.getLogger(f"fuzzer_{domain}")
        logger.setLevel(logging.DEBUG)

        # Create a file handler for the logger
        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(logging.DEBUG)

        # Set formatter for handlers
        formatter = logging.Formatter('[%(asctime)s] %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)

        # Ensure the logger does not already have a file handler, to avoid duplicate log files
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

        # Ensure the logger does not already have a console handler, to avoid duplicate console logs
        if not any(isinstance(handler, logging.StreamHandler) for handler in console_logger.handlers):
            console_logger.addHandler(console_handler)

        return console_logger

    def detect_inputs(self):
        """
        Detect all input fields on the page, including those deeper in the DOM and within iframes.
        """
        input_fields = []
        try:
            # Traverse the main page
            self.deep_traverse(self.driver.find_element(By.TAG_NAME, "body"), input_fields)

            # Traverse each iframe
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            for idx, iframe in enumerate(iframes):
                self.logger.info(f"Switching to iframe {idx + 1}")
                self.console_logger.info(f"🔄 Switching to iframe {idx + 1}")
                switch_to_iframe(self.driver, iframe)
                self.deep_traverse(self.driver.find_element(By.TAG_NAME, "body"), input_fields)
                self.driver.switch_to.default_content()

            suitable_fields = [field for field in input_fields if field.is_displayed() and field.is_enabled() and field.get_attribute("type") in ["text", "password", "email", "url", "number"]]
            self.logger.info(f"Found {len(suitable_fields)} suitable input elements.")
            self.console_logger.info(f"Found {len(suitable_fields)} suitable input elements on the page.")
            return suitable_fields
        except Exception as e:
            error_message = str(e) if str(e) else "Unknown error occurred while detecting input fields."
            self.logger.error(f"Error detecting input fields: {error_message}")
            self.console_logger.error(f"Error detecting input fields: {error_message}")
            return []

    def deep_traverse(self, root_element, elements):
        """
        Recursively traverse the DOM to detect all relevant elements.

        Args:
            root_element (WebElement): The root element to start the traversal.
            elements (list): The list to store found elements.
        """
        try:
            if root_element.tag_name in ["input", "button", "select", "textarea"]:
                elements.append(root_element)

            child_elements = root_element.find_elements(By.XPATH, "./*")
            for child in child_elements:
                self.deep_traverse(child, elements)
        except StaleElementReferenceException as e:
            self.logger.warning(f"StaleElementReferenceException while traversing DOM: {e}")

    def make_element_visible(self, element):
        """
        Use JavaScript to make a hidden element visible.
        """
        self.driver.execute_script("arguments[0].style.display = 'block'; arguments[0].style.visibility = 'visible';", element)

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

        # Make sure the element is visible
        if not input_element.is_displayed():
            self.logger.info(f"Making hidden input element '{input_element.get_attribute('name') or 'Unnamed'}' visible for fuzzing.")
            self.make_element_visible(input_element)

        for payload in payloads:
            try:
                retry_count = 0
                success = False

                # Log payload type (e.g., whitespace, empty, etc.) for better context
                payload_description = "empty" if payload == "" else "whitespace" if payload.isspace() else payload

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
                    self.logger.info(f"Payload '{payload_description}' successfully entered into field '{input_element.get_attribute('name') or 'Unnamed'}'.")
                    self.console_logger.info(f"✅ Successfully entered payload '{payload_description}' into field '{input_element.get_attribute('name') or 'Unnamed'}'.")
                else:
                    self.logger.warning(f"Payload Verification Failed after {MAX_RETRIES} retries: '{payload_description}' in field '{input_element.get_attribute('name') or 'Unnamed'}'. Entered Value: '{entered_value}'")
                    self.console_logger.warning(f"⚠️ Failed to verify payload '{payload_description}' in field '{input_element.get_attribute('name') or 'Unnamed'}' after {MAX_RETRIES} retries.")

                # Check for JavaScript changes after input
                self.js_change_detector.capture_js_console_logs()

            except (NoSuchElementException, TimeoutException, WebDriverException, StaleElementReferenceException) as e:
                # Handle empty or malformed error messages
                error_message = str(e) if str(e) else "Unknown error occurred. The error message was empty. This often occurs with input that the page is unable to process."
                self.logger.error(f"Error inserting payload '{payload_description}' into field '{input_element.get_attribute('name') or 'Unnamed'}': {error_message}")
                self.console_logger.error(f"❌ Error inserting payload '{payload_description}' into field '{input_element.get_attribute('name') or 'Unnamed'}': {error_message}")
            except Exception as e:
                # General unexpected error
                error_message = str(e) if str(e) else "Unexpected error occurred, but no details were available."
                self.logger.error(f"Unexpected error inserting payload '{payload_description}' into field '{input_element.get_attribute('name') or 'Unnamed'}': {error_message}")
                self.console_logger.error(f"❌ Unexpected error inserting payload '{payload_description}' into field '{input_element.get_attribute('name') or 'Unnamed'}': {error_message}")

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

            if not dropdown_elements:
                self.logger.warning(f"No dropdown elements found using selector '{selector}'.")
                self.console_logger.warning(f"⚠️ No dropdown elements found using selector '{selector}'.")
                return

            for idx, dropdown_element in enumerate(dropdown_elements):
                self.logger.info(f"Interacting with dropdown {idx + 1} on the page.")
                self.console_logger.info(f"👉 Interacting with dropdown {idx + 1} on the page.")
                self.fuzz_dropdown(dropdown_element, delay)

        except Exception as e:
            error_message = str(e) if str(e) else "Unknown error occurred while detecting dropdowns."
            self.logger.error(f"Error detecting dropdowns: {error_message}")
            self.console_logger.error(f"❌ Error detecting dropdowns: {error_message}")

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
                self.js_change_detector.capture_js_console_logs()

        except (StaleElementReferenceException, NoSuchElementException, WebDriverException, TimeoutException) as e:
            error_message = str(e) if str(e) else "Unknown error occurred while interacting with the dropdown."
            self.logger.error(f"Error fuzzing dropdown: {error_message}")
            self.console_logger.error(f"❌ Error fuzzing dropdown: {error_message}")

        after_snapshot = self.take_snapshot(elements_to_track=[dropdown_element]) if self.track_state else None
        if self.track_state:
            self.compare_snapshots(before_snapshot, after_snapshot)

    def take_snapshot(self, elements_to_track=None):
        """
        Take a snapshot of the page state.

        Args:
            elements_to_track (list): List of WebElement to track.

        Returns:
            dict: A dictionary containing page state information.
        """
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
                            error_message = str(e) if str(e) else "Unknown error occurred while taking element snapshot."
                            self.logger.error(f"Error taking element snapshot for element '{element_id}': {error_message}")

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
            error_message = str(e) if str(e) else "Unknown error occurred while taking snapshot of the page state."
            self.logger.error(f"Error taking snapshot of the page state: {error_message}")
            return None

    def compare_snapshots(self, before_snapshot, after_snapshot):
        """
        Compare two snapshots to detect any changes.

        Args:
            before_snapshot (dict): The initial state of the page.
            after_snapshot (dict): The state after performing some action.
        """
        if not before_snapshot or not after_snapshot:
            self.logger.warning("Cannot compare snapshots; one or both snapshots are None.")
            return

        # Compare page sources
        if before_snapshot.get('page_source') and after_snapshot.get('page_source'):
            before_source = before_snapshot['page_source']
            after_source = after_snapshot['page_source']

            if before_source != after_source:
                self.logger.info("Detected changes in the full page source.")
                self.console_logger.info("✅ [Detected Changes]: The page source has changed. Please review the latest content.")
                
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
                self.console_logger.info("ℹ️ [No Changes]: The page content appears to be stable, with no detected changes.")

        # Compare specific elements if they were tracked
        for element_id in before_snapshot['elements']:
            before_element = before_snapshot['elements'].get(element_id)
            after_element = after_snapshot['elements'].get(element_id)
            if before_element != after_element:
                self.logger.info(f"Detected changes in element '{element_id}'.")
                self.console_logger.info(f"⚠️ Detected changes in element '{element_id}'.")
            else:
                self.logger.info(f"No changes detected in element '{element_id}'.")
                self.console_logger.info(f"No changes detected in element '{element_id}'.")

        # Compare URLs
        if before_snapshot['current_url'] != after_snapshot['current_url']:
            self.logger.warning(f"URL changed from {before_snapshot['current_url']} to {after_snapshot['current_url']}.")
            self.console_logger.warning(f"⚠️ URL changed from {before_snapshot['current_url']} to {after_snapshot['current_url']}.")

        # Compare cookies
        if before_snapshot['cookies'] != after_snapshot['cookies']:
            self.logger.warning("Cookies have changed between snapshots.")
            self.console_logger.warning("⚠️ Cookies have changed between snapshots.")
