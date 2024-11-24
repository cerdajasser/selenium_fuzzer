import logging
import time
from typing import List, Dict
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_fuzzer.selenium_driver import create_driver
from selenium_fuzzer.utils import generate_safe_payloads, scroll_into_view, get_xpath
from selenium_fuzzer.logger import get_logger
from selenium_fuzzer.exceptions import ElementNotFoundError, ElementNotInteractableError
from selenium_fuzzer.unhider import Unhider
from selenium_fuzzer.input_detector import InputDetector
from selenium_fuzzer.click_analyzer import ClickAnalyzer
import argparse

logger = get_logger(__name__)

class Fuzzer:
    """Main class for the selenium fuzzer."""

    def __init__(self, url: str, headless: bool = False):
        self.url = url
        self.driver = create_driver(headless=headless)
        self.unhider = Unhider(self.driver)
        self.input_detector = InputDetector(self.driver)
        self.click_analyzer = ClickAnalyzer(self.driver)

    def fuzz_field(self, input_element: WebElement, input_name: str, delay: int) -> None:
        """Fuzz a single input field."""
        payloads = generate_safe_payloads()

        for payload in payloads:
            try:
                if not input_element.is_displayed():
                    logger.info(f"Field {input_name} is not displayed. Attempting to unhide it.")
                    self.unhider.unhide_field(input_element)
                    WebDriverWait(self.driver, 20).until(EC.visibility_of(input_element))

                scroll_into_view(self.driver, input_element)
                xpath = get_xpath(input_element)
                WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, xpath)))

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
                self.click_analyzer.analyze_response()

            except Exception as e:
                logger.error(f"Error fuzzing with payload '{payload}': {e}")
                self.driver.save_screenshot(f"error_{input_name}.png")

    def run_fuzz_fields(self, delay: int = 1) -> None:
        """Run the fuzzer for input fields."""
        try:
            inputs = self.input_detector.detect_inputs(self.url)
            if inputs:
                # List available input fields
                self.input_detector.list_inputs(inputs)
                # Prompt user to select input
                selected_form, selected_field = self.input_detector.select_input(inputs)
                form_info = inputs[selected_form]
                input_element = form_info['inputs'][selected_field]
                input_name = input_element.get_attribute('id') or input_element.get_attribute('name') or 'Unnamed'
                self.fuzz_field(input_element, input_name, delay)
        finally:
            self.driver.quit()

    def run_click_elements(self, delay: int = 1) -> None:
        """Run the fuzzer to click through clickable elements."""
        try:
            clickable_elements = self.input_detector.detect_clickable_elements()
            for element in clickable_elements:
                self.click_analyzer.click_element(element)
                time.sleep(delay)
        finally:
            self.driver.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Selenium Fuzzer Script")
    parser.add_argument("url", help="URL to fuzz")
    parser.add_argument("--fuzz-fields", action="store_true", help="Fuzz input fields")
    parser.add_argument("--click-elements", action="store_true", help="Click through clickable elements")
    parser.add_argument("--delay", type=int, default=1, help="Delay between actions in seconds")

    args = parser.parse_args()

    fuzzer = Fuzzer(args.url, headless=Config.SELENIUM_HEADLESS)

    if args.fuzz_fields:
        fuzzer.run_fuzz_fields(delay=args.delay)

    if args.click_elements:
        fuzzer.run_click_elements(delay=args.delay)
