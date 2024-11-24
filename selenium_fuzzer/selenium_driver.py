from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def create_driver(headless: bool = False):
    """Create and configure a Selenium WebDriver instance."""
    options = Options()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    return driver
