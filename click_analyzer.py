import logging
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException, NoSuchElementException
from selenium_fuzzer.utils import scroll_into_view
import time

logger = logging.getLogger(__name__)

class ClickAnalyzer:
    def __init__(self, driver):
        self.driver = driver

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
