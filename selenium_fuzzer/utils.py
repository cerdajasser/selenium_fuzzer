from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
import random
import string
from typing import List

def scroll_into_view(driver, element: WebElement) -> None:
    """Scroll the element into view."""
    driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", element)

def get_xpath(element: WebElement) -> str:
    """Get the XPath of a WebElement by traversing the DOM."""
    components = []
    child = element
    while child is not None:
        try:
            # Get the parent element of the current node
            parent = child.find_element(By.XPATH, "..")

            # Ensure the parent is not the document root or an invalid element
            if not isinstance(parent, WebElement):
                break

            # Find siblings with the same tag name to determine the index
            siblings = parent.find_elements(By.XPATH, child.tag_name)

            if len(siblings) > 1:
                index = 1
                for i in range(len(siblings)):
                    if siblings[i] == child:
                        index = i + 1
                        break
                components.append(f'{child.tag_name}[{index}]')
            else:
                components.append(child.tag_name)

            # Move up to the parent for the next iteration
            child = parent

        except (NoSuchElementException, StaleElementReferenceException) as e:
            # If we encounter an error getting the parent, break the loop
            break

    components.reverse()
    return '/' + '/'.join(components)

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
