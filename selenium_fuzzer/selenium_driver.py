from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium_fuzzer.config import Config
import logging

def create_driver(headless: bool = False):
    """Create and configure a Selenium WebDriver instance with logging preferences."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    options = Options()
    if headless:
        options.add_argument("--headless")

    # Common Chrome options for consistency and reliability
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Enable browser logging at the browser console
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})

    driver_path = Config.CHROMEDRIVER_PATH
    service = Service(executable_path=driver_path)

    # Log contextual information about the WebDriver setup
    logger.info(f"Creating ChromeDriver with GUI mode set to: {'Enabled' if not headless else 'Headless'}")
    logger.info(f"ChromeDriver path: {driver_path}")
    logger.info(f"SELENIUM_HEADLESS from config: {Config.SELENIUM_HEADLESS}")
    logger.info(f"ENABLE_DEVTOOLS from config: {Config.ENABLE_DEVTOOLS}")

    print(f"Starting ChromeDriver. GUI Mode: {'Enabled' if not headless else 'Headless Mode Enabled'}")

    # Create the WebDriver instance
    driver = webdriver.Chrome(service=service, options=options)

    # Optionally, if you want to set timeouts or other properties, do so here:
    # driver.set_page_load_timeout(Config.EXPLICIT_WAIT_TIMEOUT)

    logger.info("ChromeDriver created successfully.")
    return driver
