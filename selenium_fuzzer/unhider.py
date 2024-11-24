import logging
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
import time

logger = logging.getLogger(__name__)

class Unhider:
    def __init__(self, driver):
        self.driver = driver

    def unhide_field(self, input_element: WebElement) -> None:
        """Attempt to unhide the field if it's not displayed."""
        retries = 3
        for attempt in range(retries):
            try:
                # Look for the search icon or other clickable elements within the same parent container
                parent_element = input_element.find_element(By.XPATH, "./ancestor::*[contains(@class, 'mat-form-field') or contains(@class, 'form-group') or contains(@class, 'input-container') or contains(@class, 'input-item')]")
                search_icons = parent_element.find_elements(By.XPATH, ".//mat-icon[contains(@class, 'mat-search_icon-search') or contains(text(), 'search')] | .//button | .//a")
                
                # Try to click the search icon or other elements to unhide the input field
                for icon in search_icons:
                    if icon.is_displayed():
                        icon.click()
                        logger.info(f"Clicked icon to unhide the field: {icon.tag_name} with text: {icon.text}")
                        time.sleep(1)  # Give some time for the UI to update
                        return

                # As a fallback, try using JavaScript to make the field visible
                self.driver.execute_script(
                    "arguments[0].style.display = 'block'; arguments[0].style.visibility = 'visible'; arguments[0].style.opacity = '1'; arguments[0].removeAttribute('hidden');",
                    input_element
                )
                logger.info("Used JavaScript to unhide the field as a fallback.")
                return

            except StaleElementReferenceException:
                logger.warning(f"StaleElementReferenceException encountered while unhiding the field (attempt {attempt + 1}/{retries}). Retrying...")
                time.sleep(1)
            except NoSuchElementException:
                logger.warning("Unable to find an icon to unhide the element.")
                break
            except Exception as e:
                logger.error(f"Error unhiding the field: {e}")
                self.driver.save_screenshot('unhide_field_error.png')
                break
