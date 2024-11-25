import logging
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException
import time
from selenium_fuzzer.utils import generate_safe_payloads, retry_on_stale_element, scroll_into_view
from typing import List

logger = logging.getLogger(__name__)

class Fuzzer:
    def __init__(self, driver):
        self.driver = driver

    def detect_inputs(self) -> List[WebElement]:
        """Detect all potential input fields and buttons on the page."""
        input_fields = []
        try:
            # Detect <input> elements
            input_elements = self.driver.find_elements(By.TAG_NAME, "input")
            textarea_elements = self.driver.find_elements(By.TAG_NAME, "textarea")
            button_elements = self.driver.find_elements(By.TAG_NAME, "button")

            input_fields.extend(input_elements)
            input_fields.extend(textarea_elements)
            input_fields.extend(button_elements)

            logger.info(f"Found {len(input_fields)} input fields, textareas, and buttons.")
        except Exception as e:
            logger.error(f"Error detecting input elements: {e}")
        return input_fields

    @retry_on_stale_element
    def interact_with_element(self, element: WebElement, payload: str) -> None:
        """Interact with a given element by sending a payload."""
        try:
            scroll_into_view(self.driver, element)
            if element.tag_name in ["input", "textarea"]:
                element.clear()
                element.send_keys(payload)
                logger.info(f"Successfully interacted with input/textarea using payload: {payload}")
            elif element.tag_name == "button":
                element.click()
                logger.info("Successfully clicked button.")
        except StaleElementReferenceException as e:
            logger.error(f"Error interacting with element: {e}")
        except Exception as e:
            logger.error(f"Unexpected error interacting with element: {e}")

    def run_fuzz_fields(self, payloads: List[str], delay: int = 1) -> None:
        """Run fuzzing on detected input fields with provided payloads."""
        input_fields = self.detect_inputs()
        if not input_fields:
            logger.warning("No input fields detected on the page.")
            return

        for element in input_fields:
            for payload in payloads:
                try:
                    self.interact_with_element(element, payload)
                    time.sleep(delay)
                except Exception as e:
                    logger.error(f"Error during fuzzing interaction: {e}")
                    continue
