import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

class Fuzzer:
    def __init__(self, driver, js_change_detector):
        self.driver = driver
        self.logger = logging.getLogger(__name__)
        self.js_change_detector = js_change_detector

    def detect_inputs(self):
        """Detect all input fields on the page."""
        try:
            input_fields = self.driver.find_elements(By.TAG_NAME, "input")
            self.logger.info(f"Found {len(input_fields)} input elements.")
            return input_fields
        except Exception as e:
            self.logger.error(f"Error detecting input fields: {e}")
            return []

    def fuzz_field(self, input_element, payloads, delay=1):
        """Fuzz a given input field with a list of payloads.
        
        Args:
            input_element (WebElement): The input field to fuzz.
            payloads (list): The payloads to input into the field.
            delay (int): Time in seconds to wait between fuzzing attempts.
        """
        for payload in payloads:
            try:
                input_element.clear()
                input_element.send_keys(payload)
                input_element.send_keys(Keys.TAB)  # Trigger potential JavaScript events after input
                input_element.send_keys(Keys.ENTER)  # Explicitly hit enter after tabbing
                self.logger.info(f"Inserted payload '{payload}' into field {input_element.get_attribute('name') or 'Unnamed'}.")
                self.js_change_detector.check_for_js_changes(delay=delay)
            except Exception as e:
                self.logger.error(f"Error fuzzing with payload '{payload}': {e}")

    def run_fuzz_fields(self, delay=1):
        """Detect and fuzz all input fields on the page."""
        input_fields = self.detect_inputs()
        if not input_fields:
            self.logger.warning("No input fields detected on the page.")
            return

        payloads = ["test@example.com", "1234567890", "<script>alert('XSS')</script>", "\' OR 1=1 --"]
        for input_element in input_fields:
            self.fuzz_field(input_element, payloads, delay)

    def run_click_elements(self, delay=1):
        """Detect and click all clickable elements on the page."""
        clickable_elements = self.driver.find_elements(By.XPATH, "//button | //a | //input[@type='button'] | //input[@type='submit']")
        self.logger.info(f"Found {len(clickable_elements)} clickable elements.")

        for element in clickable_elements:
            try:
                self.logger.info(f"Clicking on element: {element.text or element.get_attribute('name') or element.get_attribute('type')}")
                element.click()
                self.js_change_detector.check_for_js_changes(delay=delay)
            except Exception as e:
                self.logger.error(f"Error clicking element: {e}")
