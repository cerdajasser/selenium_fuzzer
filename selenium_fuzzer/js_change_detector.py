import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

class JavaScriptChangeDetector:
    def __init__(self, driver):
        self.driver = driver
        self.logger = logging.getLogger(__name__)
        self.previous_page_source = ""

    def check_for_js_changes(self, success_message=None, error_keywords=None, delay=2):
        """Check for JavaScript changes or error messages on the page.

        Args:
            success_message (str): The expected success message after changes are applied.
            error_keywords (list of str): List of keywords indicating errors.
            delay (int): Time in seconds to wait for changes to appear.
        """
        if error_keywords is None:
            error_keywords = ["error", "failed", "invalid"]

        # Wait for potential changes on the page
        time.sleep(delay)

        # Capture the current state of the page source
        page_source = self.driver.page_source.lower()

        # Log the lengths of previous and current page sources for debugging purposes
        self.logger.debug(f"Previous page source length: {len(self.previous_page_source)}")
        self.logger.debug(f"Current page source length: {len(page_source)}")

        # Compare the current page source with the previous one to detect any changes
        if self.previous_page_source and self.previous_page_source != page_source:
            self.logger.info("Detected changes in the page source.")
        else:
            self.logger.info("No changes detected in the page source.")
        self.previous_page_source = page_source

        # Check for success messages
        if success_message and success_message.lower() in page_source:
            self.logger.info(f"Success message detected: '{success_message}'")

        # Check for error keywords in the page source
        for keyword in error_keywords:
            if keyword in page_source:
                self.logger.warning(f"Error detected: keyword '{keyword}' found on the page.")

    def observe_element_changes(self, element_locator, timeout=10):
        """Observe specific elements for changes using Selenium's explicit waits.

        Args:
            element_locator (tuple): Locator tuple to find the element (e.g., (By.ID, 'element_id')).
            timeout (int): Time in seconds to wait for the element to change.
        """
        try:
            WebDriverWait(self.driver, timeout).until(EC.staleness_of(self.driver.find_element(*element_locator)))
            self.logger.info("Detected a change in the targeted element.")
        except TimeoutException:
            self.logger.info("No change detected in the targeted element within the timeout period.")

    def add_mutation_observer(self, target_selector):
        """Inject JavaScript to add a MutationObserver to the target element.

        Args:
            target_selector (str): CSS selector for the target element to observe.
        """
        script = f"""
        var targetNode = document.querySelector('{target_selector}');
        if (targetNode) {{
            var config = {{ attributes: true, childList: true, subtree: true }};
            var callback = function(mutationsList, observer) {{
                mutationsList.forEach(function(mutation) {{
                    console.log('Mutation detected:', mutation);
                }});
            }};
            var observer = new MutationObserver(callback);
            observer.observe(targetNode, config);
            console.log('MutationObserver added to target node: {target_selector}');
        }} else {{
            console.log('Target node not found: {target_selector}');
        }}
        """
        self.driver.execute_script(script)
        self.logger.info(f"MutationObserver added to target element: {target_selector}")
