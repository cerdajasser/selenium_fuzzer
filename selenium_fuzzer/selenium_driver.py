from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from selenium_fuzzer.config import Config  # Import Config class

def create_driver(headless: bool = False):
    """Create and configure a Selenium WebDriver instance with logging preferences."""
    options = Options()

    if headless or Config.SELENIUM_HEADLESS:
        options.add_argument("--headless")

    # Set ChromeDriver options
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Set capabilities for logging console messages
    options.set_capability("goog:loggingPrefs", {"browser": "ALL", "performance": "ALL"})

    # Use the ChromeDriver path from config.py
    driver_path = Config.CHROMEDRIVER_PATH
    service = Service(executable_path=driver_path)

    # Create WebDriver with options
    driver = webdriver.Chrome(service=service, options=options)
    return driver
