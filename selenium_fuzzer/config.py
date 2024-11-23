import os

class Config:
    """Configuration settings for the selenium fuzzer."""
    CHROMEDRIVER_PATH = os.getenv('CHROMEDRIVER_PATH', '/usr/bin/chromedriver')
    SELENIUM_HEADLESS = os.getenv('SELENIUM_HEADLESS', 'True') == 'True'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'selenium_fuzzer.log')
