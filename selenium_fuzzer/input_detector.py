import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_fuzzer.exceptions import ElementNotFoundError
import time
from typing import List, Dict

logger = logging.getLogger(__name__)

class InputDetector:
    def __init__(self, driver):
        self.driver = driver

    def detect_inputs(self, url: str) -> List[Dict]:
        """Detect input fields within the page, retrying to account for dynamic loading and stale elements."""
        logger.info(f"Accessing URL: {url}")
        self.driver.get(url)

        retries = 5
        delay_between_retries = 5
        inputs = []
        for attempt in range(retries):
            try:
                WebDriverWait(self.driver, 40).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//input[@type='text' or @type='email' or @type='password' or @type='number' or contains(@class, 'input-item') or @placeholder] | //textarea | //*[@contenteditable='true']"))
                )
                logger.info("Page loaded successfully, detecting input components.")

                input_elements = self.driver.find_elements(By.XPATH, "//input[@type='text' or @type='email' or @type='password' or @type='number' or contains(@class, 'input-item') or @placeholder] | //textarea | //*[@contenteditable='true']")
                logger.info(f"Found {len(input_elements)} input elements.")

                for index, input_element in enumerate(input_elements):
                    if input_element.is_displayed():
                        inputs.append({
                            'form_index': index,
                            'inputs': [input_element],
                        })

                if inputs:
                    break

            except TimeoutException as e:
                logger.error(f"Timeout while detecting inputs (attempt {attempt + 1}/{retries}): {e}")
                self.driver.save_screenshot(f'error_detecting_inputs_attempt_{attempt + 1}.png')

            time.sleep(delay_between_retries)  # Wait a bit before retrying

        if not inputs:
            raise ElementNotFoundError("No visible input elements found on the page after multiple attempts.")

        return inputs

    def list_inputs(self, inputs: List[Dict]) -> None:
        """List available input fields."""
        print("\nAvailable input fields:")
        for form_info in inputs:
            form_index = form_info['form_index']
            for input_index, input_element in enumerate(form_info['inputs']):
                input_name = input_element.get_attribute('id') or input_element.get_attribute('name') or 'Unnamed'
                input_type = input_element.get_attribute('type') or input_element.tag_name
                print(f"  [{form_index}-{input_index}] Field: {input_name}, Type: {input_type}")
        print("\nPlease enter only the number corresponding to your choice.")

    def select_input(self, inputs: List[Dict]) -> (int, int):
        """Prompt the user to select an input field."""
        selected_form = self.select_valid_index(
            f"Enter the input number to select (0 to {len(inputs) - 1}): ",
            len(inputs) - 1
        )
        return selected_form, 0

    @staticmethod
    def select_valid_index(prompt: str, max_index: int) -> int:
        """Validate input selection."""
        while True:
            try:
                user_input = input(prompt).strip()
                selected_index = int(user_input)
                if 0 <= selected_index <= max_index:
                    return selected_index
                else:
                    print(f"Invalid input: please select a number between 0 and {max_index}.")
            except ValueError:
                print("Invalid input: please enter a valid number.")
