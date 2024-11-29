import logging
import time
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException, StaleElementReferenceException
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
            self.console_logger.error(f"❌ Error detecting input fields: {e}")
            return []

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
                try:
                    # Explicitly wait until the option is interactable
                    WebDriverWait(self.driver, delay).until(EC.element_to_be_clickable((By.XPATH, f"//select/option[{index+1}]")))
                    
                    # Select each option by index
                    select.select_by_index(index)
                    self.logger.info(f"Selected option '{option.text}' from dropdown.")
                    self.console_logger.info(f"✅ Selected option '{option.text}' from dropdown.")

                    # Explicitly wait for JavaScript changes and stability
                    self.js_change_detector.check_for_js_changes(delay=delay)
                    self.js_change_detector.capture_js_console_logs()  # Capture JS logs after each option is selected
                except (TimeoutException, StaleElementReferenceException) as e:
                    self.logger.error(f"Error while selecting option '{option.text}': {e}")
                    self.console_logger.error(f"❌ Error while selecting option '{option.text}': {e}")

        except (StaleElementReferenceException, NoSuchElementException, TimeoutException) as e:
            self.logger.error(f"Error fuzzing dropdown: {e}")
            self.console_logger.error(f"❌ Error fuzzing dropdown: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error fuzzing dropdown: {e}")
            self.console_logger.error(f"❌ Unexpected error fuzzing dropdown: {e}")

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
