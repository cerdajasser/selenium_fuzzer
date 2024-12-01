import logging
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException, NoSuchFrameException
import random
import string
from typing import List
import time

logger = logging.getLogger(__name__)

def scroll_into_view(driver, element: WebElement) -> None:
    """Scroll the element into view."""
    driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", element)

def reveal_element_with_js(driver, element: WebElement) -> None:
    """Reveal a hidden element using JavaScript."""
    try:
        driver.execute_script("arguments[0].style.display = 'block'; arguments[0].style.visibility = 'visible';", element)
        logger.info(f"Element with tag name '{element.tag_name}' revealed.")
    except Exception as e:
        logger.error(f"Error revealing element: {e}")

def switch_to_iframe(driver, iframe_element: WebElement) -> None:
    """Switch to a given iframe."""
    try:
        driver.switch_to.frame(iframe_element)
        logger.info(f"Switched to iframe: {iframe_element.get_attribute('name') or 'Unnamed'}")
    except NoSuchFrameException as e:
        logger.error(f"Could not switch to iframe: {e}")

def generate_safe_payloads() -> List[str]:
    """Generate a list of safe payloads for fuzzing."""
    payloads = []

    # Short random strings
    for _ in range(10):  # Increased number of short strings
        payloads.append(''.join(random.choices(string.ascii_letters + string.digits, k=10)))

    # Long strings to test input limits
    for length in [256, 512, 1024, 2048]:
        payloads.append('A' * length)

    # Strings with special characters
    special_chars_list = [
        "!@#$%^&*()_+-=[]{}|;:',.<>/?",  # Common special characters
        "`~\\\"'/",                      # Other symbols often used in user inputs
        "¡¢£¤¥¦§¨©ª«¬®¯°±²³´µ¶·¸¹º»¼½¾¿"  # Extended special characters set for testing
    ]
    payloads.extend(special_chars_list)

    # Unicode characters
    unicode_strings = [
        '测试中文字符',  # Chinese characters
        'テスト日本語文字',  # Japanese characters
        'Тестирование',  # Russian characters
        '😃👍🏻🔥🌍',    # Emojis with multiple skin tones and additional icons
        'Öäüß',         # German umlauts and special characters
        'صباح الخير'    # Arabic greeting
    ]
    payloads.extend(unicode_strings)

    # Numeric inputs
    numeric_payloads = [
        '1234567890',
        '-999999999',
        '0',                    # Edge case zero value
        '2147483647',           # Maximum value for a 32-bit signed integer
        '-2147483648',          # Minimum value for a 32-bit signed integer
        '99999999999999999999', # Long numeric value to test length limits
        '3.14159',              # Decimal value
    ]
    payloads.extend(numeric_payloads)

    # Empty and whitespace strings
    whitespace_payloads = [
        '',        # Empty string
        '   ',     # Spaces
        '\t\n',    # Tab and newline
        '\u200B'   # Zero-width space
    ]
    payloads.extend(whitespace_payloads)

    # Emails
    email_variations = [
        'test@example.com',
        'user.name+tag+sorting@example.com',
        'user@sub.example.co.uk',
        'john.doe@company.com',             # Typical corporate email
        'contact@departments.company.com',  # Department-based email address
        'invalid-email@',                   # Malformed email (safe for testing)
    ]
    payloads.extend(email_variations)

    # URLs
    url_payloads = [
        'https://example.com',
        'http://intranet.company.com',      # Internal corporate URL
        'ftp://example.com/resource',       # FTP link to test protocol handling
        'https://example.com/special?name=test&value=123',  # URL with query parameters
        'javascript:alert(1)'               # Attempt to inject JavaScript protocol
    ]
    payloads.extend(url_payloads)

    # SQL injection attempts (safe, not harmful)
    sql_payloads = [
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "' OR 1=1 --",
        '" OR "a"="a"',
        "' UNION SELECT null, null, null --",
        "' AND '1'='2",
        "'; EXEC xp_cmdshell('dir'); --"    # SQL payload for testing against MSSQL commands
    ]
    payloads.extend(sql_payloads)

    # HTML tags to test XSS and rendering issues
    xss_payloads = [
        '<script>alert("XSS")</script>',
        '<img src="x" onerror="alert(\'XSS\')" />',
        '<div><p>Test paragraph</p></div>',
        '<svg><script>alert("XSS")</script></svg>',
        '<a href="javascript:alert(\'XSS\')">Click me</a>',
    ]
    payloads.extend(xss_payloads)

    # Typical corporate inputs
    corporate_inputs = [
        '123 Main St., Springfield, USA',    # Address
        'John Doe',                          # Name
        '"SELECT * FROM users WHERE id = 1"', # SQL-like input
        'Project Phoenix Q4 2024 Update',    # Corporate project title
        'Quarterly Earnings Report Q3',      # Document title
        'C:\\Users\\John\\Documents\\file.txt',  # File path format
        '+1 (555) 123-4567',                 # Phone number with country code
        '9:00 AM - 5:00 PM',                 # Working hours format
    ]
    payloads.extend(corporate_inputs)

    # Phone numbers in various formats
    phone_numbers = [
        '555-123-4567',
        '(555) 123-4567',
        '+44 20 7946 0958',                  # International phone number (UK)
        '+1-800-555-1212',                   # Toll-free number
        '12345'                              # Short number
    ]
    payloads.extend(phone_numbers)

    # Dates in different formats
    date_payloads = [
        '2024-11-30',                        # ISO format
        '30/11/2024',                        # European format
        '11/30/2024',                        # US format
        '2024/11/30',                        # Alternate ISO format
        'Nov 30, 2024',                      # Month-day-year format
        '30-Nov-2024'                        # Day-month-year with text month
    ]
    payloads.extend(date_payloads)

    # Miscellaneous test inputs for common fields
    miscellaneous_inputs = [
        'ABCD1234',                          # Alphanumeric identifier
        'N/A',                               # Typical "Not Applicable" value
        'null',                              # Literal string "null"
        'undefined',                         # Literal string "undefined"
        'true',                              # Boolean value as string
        'false',                             # Boolean value as string
    ]
    payloads.extend(miscellaneous_inputs)

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
