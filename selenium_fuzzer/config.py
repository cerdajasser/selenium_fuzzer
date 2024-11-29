import os
import time

class Config:
    """Configuration settings for the selenium fuzzer."""
    # Path to ChromeDriver
    CHROMEDRIVER_PATH = os.getenv('CHROMEDRIVER_PATH', '/usr/bin/chromedriver')

    # Headless mode for Selenium
    SELENIUM_HEADLESS = os.getenv('SELENIUM_HEADLESS', 'False') == 'True'

    # Logging configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')
    LOG_FILE = os.getenv('LOG_FILE', f"selenium_fuzzer_{time.strftime('%Y%m%d_%H%M%S')}.log")

    # DevTools Configuration (can be overridden by the command-line argument --devtools)
    ENABLE_DEVTOOLS = os.getenv('ENABLE_DEVTOOLS', 'False') == 'True'

    # State Tracking Configuration (can be overridden by the command-line argument --track-state)
    TRACK_STATE = os.getenv('TRACK_STATE', 'False') == 'True'

    # Timeout for explicit waits (in seconds)
    EXPLICIT_WAIT_TIMEOUT = int(os.getenv('EXPLICIT_WAIT_TIMEOUT', 10))  # Default is 10 seconds

    # Directory for log files
    LOG_FOLDER = os.getenv('LOG_FOLDER', 'log')
    if not os.path.exists(LOG_FOLDER):
        os.makedirs(LOG_FOLDER)

    @classmethod
    def get_log_file_path(cls):
        """Get the path for the log file, ensuring the folder is created."""
        return os.path.join(cls.LOG_FOLDER, cls.LOG_FILE)
