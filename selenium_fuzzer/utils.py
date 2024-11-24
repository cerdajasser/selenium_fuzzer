from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

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

            child = parent
        except (NoSuchElementException, Exception) as e:
            # If we encounter an error getting the parent, break the loop
            break

    components.reverse()
    return '/' + '/'.join(components)