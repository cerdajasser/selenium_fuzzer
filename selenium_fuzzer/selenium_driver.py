from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium_fuzzer.config import Config

def create_driver(headless: bool = False):
    """Create and configure a Selenium WebDriver instance."""
    options = Options()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Use the ChromeDriver path from config.py
    driver_path = Config.CHROMEDRIVER_PATH
    service = Service(executable_path=driver_path)

    driver = webdriver.Chrome(service=service, options=options)
    return driver
