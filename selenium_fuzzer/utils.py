import random
import string
from typing import List
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

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

    return payloads

def scroll_into_view(driver: WebDriver, element: WebElement) -> None:
    """Scroll the element into view."""
    driver.execute_script(
        "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
        element
    )
