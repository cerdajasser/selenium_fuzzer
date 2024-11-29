import os

class Config:
    """Configuration settings for the selenium fuzzer."""
    # Path to ChromeDriver
    CHROMEDRIVER_PATH = os.getenv('CHROMEDRIVER_PATH', '/usr/bin/chromedriver')

    # Headless mode for Selenium
    SELENIUM_HEADLESS = os.getenv('SELENIUM_HEADLESS', 'True') == 'True'

    # Logging configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')
    LOG_FILE = os.getenv('LOG_FILE', 'selenium_fuzzer.log')

    # DevTools Configuration (can be overridden by the command-line argument --devtools)
    ENABLE_DEVTOOLS = os.getenv('ENABLE_DEVTOOLS', 'False') == 'True'  # Default is False

    # State Tracking Configuration (can be overridden by the command-line argument --track-state)
    TRACK_STATE = os.getenv('TRACK_STATE', 'False') == 'True'  # Default is False

    # Timeout for explicit waits (in seconds)
    EXPLICIT_WAIT_TIMEOUT = int(os.getenv('EXPLICIT_WAIT_TIMEOUT', 10))  # Default is 10 seconds
