from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from selenium_fuzzer.config import Config  # Import the Config class

def create_driver(headless: bool = False):
    """Create and configure a Selenium WebDriver instance with logging preferences."""
    options = Options()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Enable browser logging to capture all logs (removing the problematic 'desired_capabilities' issue)
    capabilities = DesiredCapabilities.CHROME.copy()
    capabilities["goog:loggingPrefs"] = {
        "browser": "ALL",
        "performance": "ALL",
        "driver": "ALL"
    }

    # Use the ChromeDriver path from Config
    driver_path = Config.CHROMEDRIVER_PATH
    service = Service(executable_path=driver_path)

    # Combine options with the service and capabilities to create the WebDriver
    driver = webdriver.Chrome(service=service, options=options, desired_capabilities=capabilities)
    
    return driver
