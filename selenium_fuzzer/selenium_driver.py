from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium_fuzzer.config import Config

def create_driver(headless: bool = False):
    """Create and configure a Selenium WebDriver instance with logging preferences."""
    options = Options()
    
    # Ensure headless is disabled when not requested
    if headless:
        options.add_argument("--headless=new")  # Use new headless mode for better performance in newer versions
    else:
        print("Running in non-headless mode. The Chrome browser window will be visible.")
    
    # Add necessary Chrome options
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Enable browser logging
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})

    # Use the ChromeDriver path from Config
    driver_path = Config.CHROMEDRIVER_PATH
    service = Service(executable_path=driver_path)

    # Create WebDriver instance without using deprecated `desired_capabilities`
    driver = webdriver.Chrome(service=service, options=options)

    return driver
