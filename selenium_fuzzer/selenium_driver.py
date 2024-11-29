from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium_fuzzer.config import Config  # Import Config class

def create_driver(headless: bool = False):
    """Create and configure a Selenium WebDriver instance with logging preferences."""
    options = Options()
    
    if headless or Config.SELENIUM_HEADLESS:
        options.add_argument("--headless")
    
    # Common settings for ChromeDriver
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Enable browser logging through capabilities
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})

    # Use the ChromeDriver path from config.py
    driver_path = Config.CHROMEDRIVER_PATH
    service = Service(executable_path=driver_path)

    # Initialize the WebDriver with options and service
    driver = webdriver.Chrome(service=service, options=options)
    return driver
