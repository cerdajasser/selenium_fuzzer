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
    def __init__(self, driver, js_change_detector, url, track_state=True, run_id="default_run", scenario="default_scenario"):
        """
        Initialize the Fuzzer with a given driver, JS change detector, URL, state tracking option,
        run_id and scenario for better contextual logs.
        """
        self.driver = driver
        self.url = url
        self.js_change_detector = js_change_detector
        self.track_state = track_state
        self.run_id = run_id
        self.scenario = scenario

        # Add attributes to keep track of last action and element context
        self.last_action = "Initializing Fuzzer"
        self.last_element = "N/A"

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

        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter('[%(asctime)s] %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)

        if not any(isinstance(handler, logging.FileHandler) for handler in logger.handlers):
            logger.addHandler(file_handler)

        return logger

    def setup_console_logger(self):
        """
        Set up a console logger for more readable console output.
        """
        console_logger = logging.getLogger('console_logger')
        console_logger.setLevel(logging.INFO)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        console_formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)

        if not any(isinstance(handler, logging.StreamHandler) for handler in console_logger.handlers):
            console_logger.addHandler(console_handler)

        return console_logger

    def detect_inputs(self):
        """
        Detect all input fields on the page, including those deeper in the DOM and within iframes.
        Returns a list of tuples (iframe_index, element).
        """
        self.last_action = "Detecting Input Fields"
        self.last_element = "N/A"
        input_fields = []
        try:
            self.deep_traverse(self.driver.find_element(By.TAG_NAME, "body"), input_fields, iframe_index=None)

            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            for idx, iframe in enumerate(iframes):
                self.logger.info(f"Switching to iframe {idx + 1}")
                self.console_logger.info(f"🔄 Switching to iframe {idx + 1}")
                switch_to_iframe(self.driver, iframe)
                self.deep_traverse(self.driver.find_element(By.TAG_NAME, "body"), input_fields, iframe_index=idx + 1)
                self.driver.switch_to.default_content()

            suitable_fields = [
                (f['iframe'], f['element']) for f in input_fields
                if f['element'].is_displayed() and f['element'].is_enabled() and
                   f['element'].get_attribute("type") in ["text", "password", "email", "url", "number"]
            ]
            self.logger.info(f"Found {len(suitable_fields)} suitable input elements. RunID: {self.run_id}, Scenario: {self.scenario}")
            self.console_logger.info(f"Found {len(suitable_fields)} suitable input elements on the page.")
            return suitable_fields
        except Exception as e:
            error_message = str(e) if str(e) else "Unknown error occurred while detecting input fields."
            current_url = self.driver.current_url
            self.logger.error(
                f"Error detecting input fields: {error_message}. URL: {current_url}, RunID: {self.run_id}, Scenario: {self.scenario}, "
                f"LastAction: {self.last_action}, LastElement: {self.last_element}"
            )
            self.console_logger.error(f"Error detecting input fields: {error_message}")
            return []

    def deep_traverse(self, root_element, elements, iframe_index):
        """
        Recursively traverse the DOM to detect all relevant elements.
        Stores {'iframe': iframe_index, 'element': element} for each found element.
        """
        try:
            if root_element.tag_name in ["input", "button", "select", "textarea"]:
                elements.append({'iframe': iframe_index, 'element': root_element})

            child_elements = root_element.find_elements(By.XPATH, "./*")
            for child in child_elements:
                self.deep_traverse(child, elements, iframe_index)
        except StaleElementReferenceException as e:
            self.logger.warning(f"StaleElementReferenceException while traversing DOM: {e}")

    def make_element_visible(self, element):
        """
        Use JavaScript to make a hidden element visible.
        """
        self.driver.execute_script("arguments[0].style.display = 'block'; arguments[0].style.visibility = 'visible';", element)

    def fuzz_field(self, input_data, payloads, delay=1):
        """
        Fuzz a given input field with a list of payloads.
        input_data: (iframe_index, input_element)
        """
        iframe_index, input_element = input_data
        field_name = input_element.get_attribute('name') or 'Unnamed'
        current_url = self.driver.current_url
        self.last_action = "Fuzzing Input Field"
        self.last_element = field_name

        self.logger.info(
            f"Fuzzing field '{field_name}' in iframe {iframe_index if iframe_index else 'main page'} at URL: {current_url}, "
            f"RunID: {self.run_id}, Scenario: {self.scenario}"
        )
        self.console_logger.info(f"🔍 Fuzzing field '{field_name}' (iframe: {iframe_index if iframe_index else 'none'})")

        before_snapshot = self.take_snapshot(elements_to_track=[input_element]) if self.track_state else None

        if not input_element.is_displayed():
            self.logger.info(
                f"Making hidden input element '{field_name}' visible for fuzzing at URL: {current_url}, RunID: {self.run_id}, Scenario: {self.scenario}"
            )
            self.make_element_visible(input_element)

        MAX_RETRIES = 3

        for payload in payloads:
            try:
                retry_count = 0
                success = False
                payload_description = "empty" if payload == "" else "whitespace" if payload.isspace() else payload

                while retry_count < MAX_RETRIES and not success:
                    self.driver.execute_script("arguments[0].value = '';", input_element)
                    WebDriverWait(self.driver, delay).until(lambda d: self.driver.execute_script("return arguments[0].value;", input_element) == "")

                    self.driver.execute_script("arguments[0].value = arguments[1];", input_element, payload)
                    input_element.send_keys(Keys.TAB)
                    input_element.send_keys(Keys.ENTER)
                    WebDriverWait(self.driver, delay).until(lambda d: self.driver.execute_script("return arguments[0].value;", input_element) == payload)

                    entered_value = self.driver.execute_script("return arguments[0].value;", input_element)
                    success = (entered_value == payload)

                    if not success:
                        retry_count += 1

                if success:
                    self.logger.info(
                        f"Payload '{payload_description}' successfully entered into field '{field_name}'. URL: {current_url}, RunID: {self.run_id}, Scenario: {self.scenario}"
                    )
                    self.console_logger.info(f"✅ Successfully entered payload '{payload_description}' into field '{field_name}'.")
                else:
                    self.logger.warning(
                        f"Payload Verification Failed after {MAX_RETRIES} retries: '{payload_description}' in field '{field_name}', "
                        f"URL: {current_url}, RunID: {self.run_id}, Scenario: {self.scenario}. Entered Value: '{entered_value}'"
                    )
                    self.console_logger.warning(f"⚠️ Failed to verify payload '{payload_description}' in field '{field_name}' after {MAX_RETRIES} retries.")

                self.js_change_detector.capture_js_console_logs()

            except (NoSuchElementException, TimeoutException, WebDriverException, StaleElementReferenceException) as e:
                error_message = str(e) if str(e) else "Unknown error occurred."
                self.logger.error(
                    f"Error inserting payload '{payload_description}' into field '{field_name}' at URL: {current_url}, "
                    f"RunID: {self.run_id}, Scenario: {self.scenario}, LastAction: {self.last_action}, LastElement: {self.last_element}, Error: {error_message}"
                )
                self.console_logger.error(f"❌ Error inserting payload '{payload_description}' into field '{field_name}': {error_message}")
            except Exception as e:
                error_message = str(e) if str(e) else "Unexpected error occurred."
                self.logger.error(
                    f"Unexpected error inserting payload '{payload_description}' into field '{field_name}' at URL: {current_url}, "
                    f"RunID: {self.run_id}, Scenario: {self.scenario}, LastAction: {self.last_action}, LastElement: {self.last_element}, Error: {error_message}"
                )
                self.console_logger.error(f"❌ Unexpected error inserting payload '{payload_description}' into field '{field_name}': {error_message}")

        after_snapshot = self.take_snapshot(elements_to_track=[input_element]) if self.track_state else None
        if self.track_state:
            self.compare_snapshots(before_snapshot, after_snapshot)

    def fuzz_dropdowns(self, selector="select", delay=1):
        """
        Detect dropdown elements and allow user to select which ones to fuzz.
        """
        self.last_action = "Detecting Dropdowns"
        self.last_element = "N/A"
        try:
            dropdown_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            self.logger.info(f"Found {len(dropdown_elements)} dropdown elements using '{selector}' at URL: {self.driver.current_url}, RunID: {self.run_id}, Scenario: {self.scenario}")
            self.console_logger.info(f"Found {len(dropdown_elements)} dropdown elements on the page.\n")

            if not dropdown_elements:
                self.logger.warning(f"No dropdown elements found using selector '{selector}' at URL: {self.driver.current_url}, RunID: {self.run_id}, Scenario: {self.scenario}")
                self.console_logger.warning(f"⚠️ No dropdown elements found using selector '{selector}'.")
                return

            print(f"✅ Found {len(dropdown_elements)} dropdown element(s):")
            print("   ────────────────────────────────────────────────")
            for idx, dropdown_element in enumerate(dropdown_elements):
                dropdown_name = dropdown_element.get_attribute("name") or dropdown_element.get_attribute("id") or "Unnamed Dropdown"
                print(f"   [{idx}] 📂 Name: {dropdown_name}")

            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            selected_indices = input("\nPlease enter the indices of the dropdowns to fuzz (comma-separated): ")
            selected_indices = [int(idx.strip()) for idx in selected_indices.split(",") if idx.strip().isdigit()]

            if not selected_indices:
                self.console_logger.info("No dropdowns selected for fuzzing.")
                return

            for idx in selected_indices:
                if 0 <= idx < len(dropdown_elements):
                    dropdown_name = dropdown_elements[idx].get_attribute("name") or dropdown_elements[idx].get_attribute("id") or "Unnamed Dropdown"
                    self.last_action = f"Fuzzing Dropdown {dropdown_name}"
                    self.last_element = dropdown_name
                    self.logger.info(f"Fuzzing dropdown '{dropdown_name}' (index {idx}) at URL: {self.driver.current_url}, RunID: {self.run_id}, Scenario: {self.scenario}")
                    self.console_logger.info(f"👉 Fuzzing dropdown {idx + 1} on the page.")
                    self.fuzz_dropdown(dropdown_elements[idx], delay)
                else:
                    self.console_logger.warning(f"⚠️ Invalid index '{idx}' entered. Skipping.")
                    self.logger.warning(f"Invalid dropdown index '{idx}' entered at URL: {self.driver.current_url}, RunID: {self.run_id}, Scenario: {self.scenario}")

        except Exception as e:
            error_message = str(e) if str(e) else "Unknown error occurred while selecting dropdowns."
            self.logger.error(f"Error handling dropdown selection at URL: {self.driver.current_url}, RunID: {self.run_id}, Scenario: {self.scenario}: {error_message}")
            self.console_logger.error(f"❌ Error handling dropdown selection: {error_message}")

    def fuzz_dropdown(self, dropdown_element, delay=1):
        """
        Interact with a dropdown element by selecting each option.
        """
        dropdown_name = dropdown_element.get_attribute("name") or dropdown_element.get_attribute("id") or "Unnamed Dropdown"
        current_url = self.driver.current_url
        self.last_action = "Fuzzing Dropdown Options"
        self.last_element = dropdown_name
        self.logger.info(f"Fuzzing dropdown '{dropdown_name}' at URL: {current_url}, RunID: {self.run_id}, Scenario: {self.scenario}")
        self.console_logger.info(f"👉 Fuzzing dropdown '{dropdown_name}'")

        before_snapshot = self.take_snapshot(elements_to_track=[dropdown_element]) if self.track_state else None

        try:
            select = Select(dropdown_element)
            options = select.options
            for index, option in enumerate(options):
                self.last_action = f"Selecting option '{option.text}' in dropdown '{dropdown_name}'"
                select.select_by_index(index)
                self.logger.info(f"Selected option '{option.text}' from dropdown '{dropdown_name}' at URL: {current_url}, RunID: {self.run_id}, Scenario: {self.scenario}")
                self.console_logger.info(f"✅ Selected option '{option.text}' from dropdown.")
                WebDriverWait(self.driver, delay).until(lambda d: True)
                self.js_change_detector.capture_js_console_logs()

        except (StaleElementReferenceException, NoSuchElementException, WebDriverException, TimeoutException) as e:
            error_message = str(e) if str(e) else "Unknown error occurred."
            self.logger.error(
                f"Error fuzzing dropdown '{dropdown_name}' at URL: {current_url}, RunID: {self.run_id}, Scenario: {self.scenario}, "
                f"LastAction: {self.last_action}, LastElement: {self.last_element}, Error: {error_message}"
            )
            self.console_logger.error(f"❌ Error fuzzing dropdown '{dropdown_name}': {error_message}")

        after_snapshot = self.take_snapshot(elements_to_track=[dropdown_element]) if self.track_state else None
        if self.track_state:
            self.compare_snapshots(before_snapshot, after_snapshot)

    def take_snapshot(self, elements_to_track=None):
        """
        Take a snapshot of the page state.
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
                            self.logger.error(f"Error taking element snapshot for element '{element_id}': {error_message}, RunID: {self.run_id}, Scenario: {self.scenario}")

            snapshot = {
                'page_source': page_source,
                'current_url': current_url,
                'cookies': cookies,
                'elements': element_snapshots
            }

            self.logger.debug(f"Snapshot taken for URL: {current_url}, RunID: {self.run_id}, Scenario: {self.scenario}")
            self.console_logger.info("Snapshot taken of the current page state.")
            return snapshot
        except Exception as e:
            error_message = str(e) if str(e) else "Unknown error occurred while taking snapshot of the page state."
            self.logger.error(f"Error taking snapshot of the page state: {error_message}, RunID: {self.run_id}, Scenario: {self.scenario}")
            return None

    def compare_snapshots(self, before_snapshot, after_snapshot):
        """
        Compare two snapshots to detect any changes.
        """
        if not before_snapshot or not after_snapshot:
            self.logger.warning("Cannot compare snapshots; one or both snapshots are None.")
            return

        before_source = before_snapshot.get('page_source')
        after_source = after_snapshot.get('page_source')

        if before_source and after_source and before_source != after_source:
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

        for element_id in before_snapshot['elements']:
            before_element = before_snapshot['elements'].get(element_id)
            after_element = after_snapshot['elements'].get(element_id)
            if before_element != after_element:
                self.logger.info(f"Detected changes in element '{element_id}'. RunID: {self.run_id}, Scenario: {self.scenario}")
                self.console_logger.info(f"⚠️ Detected changes in element '{element_id}'.")
            else:
                self.logger.info(f"No changes detected in element '{element_id}'. RunID: {self.run_id}, Scenario: {self.scenario}")
                self.console_logger.info(f"No changes detected in element '{element_id}'.")

        if before_snapshot['current_url'] != after_snapshot['current_url']:
            self.logger.warning(
                f"URL changed from {before_snapshot['current_url']} to {after_snapshot['current_url']}. RunID: {self.run_id}, Scenario: {self.scenario}"
            )
            self.console_logger.warning(
                f"⚠️ URL changed from {before_snapshot['current_url']} to {after_snapshot['current_url']}."
            )

        if before_snapshot['cookies'] != after_snapshot['cookies']:
            self.logger.warning(f"Cookies have changed between snapshots. RunID: {self.run_id}, Scenario: {self.scenario}")
            self.console_logger.warning("⚠️ Cookies have changed between snapshots.")
