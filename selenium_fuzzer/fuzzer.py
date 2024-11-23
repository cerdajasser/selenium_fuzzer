import logging
import time
from typing import List, Dict
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_fuzzer.selenium_driver import create_driver
from selenium_fuzzer.utils import generate_safe_payloads, scroll_into_view
from selenium_fuzzer.logger import get_logger
from selenium_fuzzer.exceptions import ElementNotFoundError, ElementNotInteractableError
import argparse

logger = get_logger(__name__)

class Fuzzer:
    """Main class for the selenium fuzzer."""

    def __init__(self, url: str):
        self.url = url
        self.driver = create_driver()

    def detect_inputs(self) -> List[Dict]:
        """Detect input fields within mat-form-field components."""
        logger.info(f"Accessing URL: {self.url}")
        self.driver.get(self.url)

        try:
            WebDriverWait(self.driver, 40).until(
                EC.presence_of_element_located((By.TAG_NAME, 'mat-form-field'))
            )
            logger.info("Page loaded successfully, detecting mat-form-field components.")

            mat_form_fields = self.driver.find_elements(By.TAG_NAME, 'mat-form-field')
            logger.info(f"Found {len(mat_form_fields)} mat-form-field elements.")

            inputs = []
            for index, mat_field in enumerate(mat_form_fields):
                input_elements = mat_field.find_elements(By.CSS_SELECTOR, 'input')
                if input_elements:
                    inputs.append({
                        'form_index': index,
                        'inputs': input_elements,
                    })

            if not inputs:
                raise ElementNotFoundError("No input elements found within mat-form-field components.")

            return inputs

        except TimeoutException as e:
            logger.error(f"Timeout while detecting inputs: {e}")
            self.driver.save_screenshot('error_detecting_inputs.png')
            raise

    def detect_clickable_elements(self) -> List[WebElement]:
        """Detect clickable elements on the page."""
        try:
            clickable_elements = self.driver.find_elements(By.XPATH, "//a | //button | //*[@onclick]")
            logger.info(f"Detected {len(clickable_elements)} clickable elements.")
            return clickable_elements
        except Exception as e:
            logger.error(f"Error detecting clickable elements: {e}")
            return []

    def click_element(self, element: WebElement) -> None:
        """Click an element and analyze the page for errors."""
        try:
            # Scroll into view and click the element
            scroll_into_view(self.driver, element)
            WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable(element))
            element.click()
            logger.info(f"Clicked element: {element.tag_name} with text: {element.text}")

            # Analyze the page response after clicking
            self.analyze_response()

        except (ElementNotInteractableException, TimeoutException, NoSuchElementException) as e:
            logger.error(f"Error clicking element: {e}")
            self.driver.save_screenshot('click_element_error.png')

    def analyze_response(self) -> None:
        """Analyze the server response for errors."""
        response_content = self.driver.page_source
        response_url = self.driver.current_url
        logger.info(f"Current URL after interaction: {response_url}")

        error_indicators = [
            'error',
            'exception',
            'not found',
            '500 Internal Server Error',
            'JavaScript error',
        ]

        for indicator in error_indicators:
            if indicator.lower() in response_content.lower():
                logger.warning(f"Possible issue detected: {indicator}")
                self.driver.save_screenshot(f"issue_detected_{indicator}.png")
                break

    def unhide_field(self, input_element: WebElement) -> None:
        """Attempt to unhide the field if it's not displayed."""
        try:
            # Look for the search icon within the same parent container
            parent_element = input_element.find_element(By.XPATH, "./ancestor::*[contains(@class, 'mat-form-field')]")
            search_icons = parent_element.find_elements(By.XPATH, ".//mat-icon[contains(@class, 'mat-search_icon-search') or contains(text(), 'search')]")
            
            # Try to click the search icon to unhide the input field
            for icon in search_icons:
                if icon.is_displayed():
                    icon.click()
                    logger.info(f"Clicked search icon to unhide the field: {icon.tag_name} with text: {icon.text}")
                    time.sleep(1)  # Give some time for the UI to update
                    return

            logger.warning("No search icon found or could not unhide the element.")

        except NoSuchElementException:
            logger.warning("Unable to find a search icon to unhide the element.")
        except Exception as e:
            logger.error(f"Error unhiding the field: {e}")
            self.driver.save_screenshot('unhide_field_error.png')

    def fuzz_field(self, input_element: WebElement, input_name: str, delay: int) -> None:
        """Fuzz a single input field."""
        payloads = generate_safe_payloads()

        for payload in payloads:
            try:
                if not input_element.is_displayed():
                    logger.info(f"Field {input_name} is not displayed. Attempting to unhide it.")
                    self.unhide_field(input_element)
                    WebDriverWait(self.driver, 20).until(EC.visibility_of(input_element))

                scroll_into_view(self.driver, input_element)
                WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, self.get_xpath(input_element))))

                input_element.clear()
                input_element.send_keys(payload)
                logger.info(f"Fuzzing Field: {input_name}, Payload: {payload}")
                time.sleep(delay)

                # Trigger events
                input_element.send_keys(Keys.TAB)
                time.sleep(0.5)

                self.driver.execute_script(
                    "arguments[0].dispatchEvent(new Event('input', { bubbles: true }));",
                    input_element
                )
                self.driver.execute_script(
                    "arguments[0].dispatchEvent(new Event('change', { bubbles: true }));",
                    input_element
                )
                time.sleep(0.5)

                # Analyze response
                self.analyze_response()

            except Exception as e:
                logger.error(f"Error fuzzing with payload '{payload}': {e}")
                self.driver.save_screenshot(f"error_{input_name}.png")

    def run_fuzz_fields(self, delay: int = 1) -> None:
        """Run the fuzzer for input fields."""
        try:
            inputs = self.detect_inputs()
            if inputs:
                # List available input fields
                self.list_inputs(inputs)
                # Prompt user to select input
                selected_form, selected_field = self.select_input(inputs)
                form_info = inputs[selected_form]
                input_element = form_info['inputs'][selected_field]
                input_name = input_element.get_attribute('id') or input_element.get_attribute('name') or 'Unnamed'
                self.fuzz_field(input_element, input_name, delay)
        finally:
            self.driver.quit()

    def run_click_elements(self, delay: int = 1) -> None:
        """Run the fuzzer to click through clickable elements."""
        try:
            clickable_elements = self.detect_clickable_elements()
            for element in clickable_elements:
                self.click_element(element)
                time.sleep(delay)
        finally:
            self.driver.quit()

    def list_inputs(self, inputs: List[Dict]) -> None:
        """List available input fields."""
        print("\nAvailable input fields within mat-form-field components:")
        for form_info in inputs:
            form_index = form_info['form_index']
            print(f"mat-form-field {form_index}:")
            for input_index, input_element in enumerate(form_info['inputs']):
                input_name = input_element.get_attribute('id') or input_element.get_attribute('name') or 'Unnamed'
                input_type = input_element.get_attribute('type') or input_element.tag_name
                print(f"  [{input_index}] Field: {input_name}, Type: {input_type}")
        print("\nPlease enter only the number corresponding to your choice.")

    def select_input(self, inputs: List[Dict]) -> (int, int):
        """Prompt the user to select an input field."""
        selected_form = self.select_valid_index(
            f"Enter the mat-form-field number to select (0 to {len(inputs) - 1}): ",
            len(inputs) - 1
        )
        selected_field = self.select_valid_index(
            f"Enter the field number to select (0 to {len(inputs[selected_form]['inputs']) - 1}): ",
            len(inputs[selected_form]['inputs']) - 1
        )
        return selected_form, selected_field

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Selenium Fuzzer Script")
    parser.add_argument("url", help="URL to fuzz")
    parser.add_argument("--fuzz-fields", action="store_true", help="Fuzz input fields")
    parser.add_argument("--click-elements", action="store_true", help="Click through clickable elements")
    parser.add_argument("--delay", type=int, default=1, help="Delay between actions in seconds")

    args = parser.parse_args()

    fuzzer = Fuzzer(args.url)

    if args.fuzz_fields:
        fuzzer.run_fuzz_fields(delay=args.delay)

    if args.click_elements:
        fuzzer.run_click_elements(delay=args.delay)
