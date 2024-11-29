import logging
import time
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from urllib.parse import urlparse

class Fuzzer:
    def __init__(self, driver, js_change_detector, url):
        """
        Initialize the Fuzzer with a given driver, JS change detector, and URL.
        """
        self.driver = driver
        self.url = url
        self.js_change_detector = js_change_detector
        self.logger = self.setup_logger()
        self.console_logger = self.setup_console_logger()

    def setup_logger(self):
        """
        Set up a logger that creates a new log file for each website.
        """
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

        # Add handlers to the logger
        if not any(isinstance(handler, logging.FileHandler) and handler.baseFilename == file_handler.baseFilename for handler in logger.handlers):  # Avoid adding multiple handlers if the logger already has them
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
        console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)

        # Avoid adding multiple handlers if the logger already has one
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
        
        Args:
            input_element (WebElement): The input field to fuzz.
            payloads (list): The payloads to input into the field.
            delay (int): Time in seconds to wait between fuzzing attempts.
        """
        MAX_RETRIES = 3

        for payload in payloads:
            try:
                retry_count = 0
                success = False

                while retry_count < MAX_RETRIES and not success:
                    # Clear the input field using JavaScript to ensure it's empty
                    self.driver.execute_script("arguments[0].value = '';", input_element)
                    
                    # Wait a moment to ensure JavaScript clearing is complete
                    time.sleep(0.5)

                    # Set value using JavaScript to avoid front-end interference
                    self.driver.execute_script("arguments[0].value = arguments[1];", input_element, payload)
                    
                    # Send TAB and ENTER to trigger potential events
                    input_element.send_keys(Keys.TAB)
                    input_element.send_keys(Keys.ENTER)

                    # Wait to allow JavaScript to process changes
                    time.sleep(delay)

                    # Verify the value using JavaScript
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
                self.js_change_detector.capture_js_console_logs()  # Capture JS logs after fuzzing

            except (NoSuchElementException, TimeoutException, WebDriverException) as e:
                self.logger.error(f"Error Inserting Payload into Field '{input_element.get_attribute('name') or 'Unnamed'}': {e}")
                self.console_logger.error(f"❌ Error inserting payload into field '{input_element.get_attribute('name') or 'Unnamed'}': {e}")
            except Exception as e:
                self.logger.error(f"Unexpected Error Inserting Payload into Field '{input_element.get_attribute('name') or 'Unnamed'}': {e}")
                self.console_logger.error(f"❌ Unexpected error inserting payload into field '{input_element.get_attribute('name') or 'Unnamed'}': {e}")

    def detect_dropdowns(self, selector="select", delay=10):
        """
        Detect dropdown elements using the provided selector and interact with them.
        
        Args:
            selector (str): CSS selector to locate dropdowns.
            delay (int): Time in seconds to wait between dropdown interactions.
        """
        try:
            # Locate dropdown elements using the provided CSS selector
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
        """
        Interact with a dropdown element by selecting each option.
        
        Args:
            dropdown_element (WebElement): The dropdown element to fuzz.
            delay (int): Time in seconds to wait between selections.
        """
        try:
            select = Select(dropdown_element)
            options = select.options
            for index, option in enumerate(options):
                # Select each option by index
                select.select_by_index(index)
                self.logger.info(f"Selected option '{option.text}' from dropdown.")
                self.console_logger.info(f"✅ Selected option '{option.text}' from dropdown.")
                time.sleep(delay)  # Add a delay for each selection to observe any changes
                self.js_change_detector.check_for_js_changes(delay=delay)
                self.js_change_detector.capture_js_console_logs()  # Capture JS logs after each option is selected
        except Exception as e:
            self.logger.error(f"Error fuzzing dropdown: {e}")
            self.console_logger.error(f"❌ Error fuzzing dropdown: {e}")

    def analyze_response(self):
        """
        Analyze the response of the dropdown interaction.
        """
        # Placeholder method to analyze the response after selecting each option
        pass

    def run_fuzz(self, delay=1):
        """
        Main method to run the fuzzing operation, including input fields, dropdowns, and clickable elements.
        """
        try:
            self.run_fuzz_fields(delay)
            self.detect_dropdowns(delay=delay)
            self.run_click_elements(delay)
        finally:
            self.driver.quit()

# Example usage
if __name__ == "__main__":
    from selenium import webdriver
    from selenium_fuzzer.js_change_detector import JavaScriptChangeDetector

    # Create a driver instance and JS change detector
    chrome_options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(options=chrome_options)
    js_change_detector = JavaScriptChangeDetector(driver)

    # Instantiate and run the fuzzer
    fuzzer = Fuzzer(driver, js_change_detector, "https://example.com")
    fuzzer.run_fuzz(delay=1)
