from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium_fuzzer.config import Config

def create_driver() -> webdriver.Chrome:
    """
    Create and return a configured Selenium WebDriver instance.
    """
    options = Options()
    
    # Set headless mode based on configuration
    if Config.SELENIUM_HEADLESS:
        options.add_argument('--headless')
    
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--ignore-certificate-errors')

    # Initialize ChromeDriver
    service = Service(executable_path=Config.CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(10)
    return driver
