import logging
import os
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from urllib.parse import urlparse
import time
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException

class Fuzzer:
    def __init__(self, driver, js_change_detector, url):
        """
        Initialize the Fuzzer with a given driver, JS change detector, and URL.
        """
        self.driver = driver
        self.url = url
        self.js_change_detector = js_change_detector
        self.logger = self.setup_logger()

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

        # Create a console handler for additional output (optional)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Set formatter for handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add handlers to the logger
        if not any(isinstance(handler, logging.FileHandler) and handler.baseFilename == file_handler.baseFilename for handler in logger.handlers):  # Avoid adding multiple handlers if the logger already has them
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)

        return logger

    def detect_inputs(self):
        """
        Detect all input fields on the page.
        """
        try:
            input_fields = self.driver.find_elements(By.TAG_NAME, "input")
            self.logger.info(f"Found {len(input_fields)} input elements.")
            return input_fields
        except Exception as e:
            self.logger.error(f"Error detecting input fields: {e}")
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
                    self.logger.info(f"\n>>> Payload '{payload}' successfully entered into field '{input_element.get_attribute('name') or 'Unnamed'}'.\n")
                else:
                    self.logger.warning(f"\n!!! Payload Verification Failed after {MAX_RETRIES} retries: '{payload}' in field '{input_element.get_attribute('name') or 'Unnamed'}'. Entered Value: '{entered_value}'\n")

                # Check for JavaScript changes after input
                self.js_change_detector.check_for_js_changes(delay=delay)

            except (NoSuchElementException, TimeoutException, WebDriverException) as e:
                self.logger.error(f"\n!!! Error Inserting Payload into Field '{input_element.get_attribute('name') or 'Unnamed'}': {e}\n")
            except Exception as e:
                self.logger.error(f"\n!!! Unexpected Error Inserting Payload into Field '{input_element.get_attribute('name') or 'Unnamed'}': {e}\n")

    def detect_dropdowns(self):
        """
        Detect dropdown elements in the specific div and interact with them.
        """
        try:
            # Locate the dropdown elements using the specific div ID
            container = self.driver.find_element(By.ID, "prductsize")
            dropdown_elements = container.find_elements(By.TAG_NAME, "select")
            self.logger.info(f"Found {len(dropdown_elements)} dropdown elements in 'prductsize'.")
            for dropdown_element in dropdown_elements:
                self.fuzz_dropdown(dropdown_element)
        except Exception as e:
            self.logger.error(f"Error detecting dropdowns: {e}")

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
                self.logger.info(f"Selected option: {option.text}")
                time.sleep(delay)  # Add a delay for each selection to observe any changes
                self.analyze_response()
        except Exception as e:
            self.logger.error(f"Error fuzzing dropdown: {e}")

    def analyze_response(self):
        """
        Analyze the response of the dropdown interaction.
        """
        # Placeholder method to analyze the response after selecting each option
        pass

    def run_fuzz_fields(self, delay=1):
        """
        Detect and fuzz all input fields on the page.
        """
        input_fields = self.detect_inputs()
        if not input_fields:
            self.logger.warning("No input fields detected on the page.")
            return

        payloads = ["test@example.com", "1234567890", "<script>alert('XSS')</script>", "' OR 1=1 --"]
        for input_element in input_fields:
            self.fuzz_field(input_element, payloads, delay)

    def run_click_elements(self, delay=1):
        """
        Detect and click all clickable elements on the page.
        """
        clickable_elements = self.driver.find_elements(By.XPATH, "//button | //a | //input[@type='button'] | //input[@type='submit']")
        self.logger.info(f"Found {len(clickable_elements)} clickable elements.")

        for element in clickable_elements:
            try:
                self.logger.info(f"Clicking on element: {element.text or element.get_attribute('name') or element.get_attribute('type')}")
                element.click()
                self.js_change_detector.check_for_js_changes(delay=delay)
            except Exception as e:
                self.logger.error(f"Error clicking element: {e}")

    def run_fuzz(self, delay=1):
        """
        Main method to run the fuzzing operation, including input fields, dropdowns, and clickable elements.
        """
        try:
            self.run_fuzz_fields(delay)
            self.detect_dropdowns()
            self.run_click_elements(delay)
        finally:
            self.driver.quit()

# Example usage
if __name__ == "__main__":
    from selenium import webdriver
    from selenium_fuzzer.js_change_detector import JSChangeDetector

    # Create a driver instance and JS change detector
    driver = webdriver.Chrome()
    js_change_detector = JSChangeDetector(driver)

    # Instantiate and run the fuzzer
    fuzzer = Fuzzer(driver, js_change_detector, "https://example.com")
    fuzzer.run_fuzz(delay=1)
