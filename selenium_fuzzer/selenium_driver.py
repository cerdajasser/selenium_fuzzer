from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from selenium_fuzzer.config import Config
import logging

def create_driver(headless: bool = False):
    """Create and configure a Selenium WebDriver instance with logging preferences."""
    options = Options()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Enable browser logging
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})

    # Use the ChromeDriver path from Config
    driver_path = Config.CHROMEDRIVER_PATH
    service = Service(executable_path=driver_path)

    # Log whether headless mode is enabled
    logger = logging.getLogger(__name__)
    print(f"Starting ChromeDriver. GUI Mode: {'Enabled' if not headless else 'Headless Mode Enabled'}")
    logger.info(f"Creating ChromeDriver with GUI mode set to: {'Enabled' if not headless else 'Headless Mode Enabled'}")

    # Create driver with options and capabilities
    driver = webdriver.Chrome(service=service, options=options)

    return driver
