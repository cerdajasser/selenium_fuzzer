import logging
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException
import random
import string
from typing import List
import time

logger = logging.getLogger(__name__)


def scroll_into_view(driver, element: WebElement) -> None:
    """Scroll the element into view."""
    driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", element)


def generate_safe_payloads() -> List[str]:
    """Generate a list of safe payloads for fuzzing."""
    payloads = []

    # Short random strings
    for _ in range(5):
        payloads.append(''.join(random.choices(string.ascii_letters + string.digits, k=10)))

    # Long strings to test input limits
    payloads.append('A' * 256)
    payloads.append('B' * 1024)

    # Strings with special characters
    special_chars = "!@#$%^&*()_+-=[]{}|;:',.<>/?"
    payloads.append(special_chars)

    # Unicode characters
    payloads.append('测试中文字符')  # Chinese characters
    payloads.append('😃👍🏻🔥')      # Emojis

    # Numeric inputs
    payloads.append('1234567890')
    payloads.append('-999999999')

    # Empty string
    payloads.append('')

    # Whitespace characters
    payloads.append('   ')  # Spaces
    payloads.append('\t\n')  # Tab and newline

    # Emails
    payloads.append('test@example.com')
    payloads.append('user.name+tag+sorting@example.com')

    # SQL injection attempts (safe, not harmful)
    payloads.append("' OR '1'='1")
    payloads.append("'; DROP TABLE users; --")

    # HTML tags to test XSS and rendering issues
    payloads.append('<script>alert("XSS")</script>')
    payloads.append('<div><p>Test</p></div>')

    # Typical corporate inputs
    payloads.append('https://example.com')  # URL
    payloads.append('123 Main St., Springfield, USA')  # Address
    payloads.append('John Doe')  # Name
    payloads.append('"SELECT * FROM users WHERE id = 1"')  # SQL-like input

    return payloads


def retry_on_stale_element(func):
    """Decorator to retry a function if a StaleElementReferenceException is encountered."""
    def wrapper(*args, **kwargs):
        max_retries = 5  # Increased retries to handle dynamic elements better
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except StaleElementReferenceException as e:
                logger.warning(f"StaleElementReferenceException encountered. Attempt {attempt + 1} of {max_retries}. Error: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    logger.error(f"Max retries reached. StaleElementReferenceException could not be resolved: {e}")
                    raise
    return wrapper


def is_element_displayed(element: WebElement, driver) -> bool:
    """Check if an element is displayed, with retry logic for stale elements."""
    scroll_into_view(driver, element)  # Scroll into view before checking visibility
    return element.is_displayed()
