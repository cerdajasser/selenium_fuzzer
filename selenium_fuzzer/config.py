import os
import time

class Config:
    """Configuration settings for the selenium fuzzer."""

    # Path to ChromeDriver
    CHROMEDRIVER_PATH = os.getenv('CHROMEDRIVER_PATH', '/usr/bin/chromedriver')

    # Selenium Chrome Options
    SELENIUM_HEADLESS = os.getenv('SELENIUM_HEADLESS', 'False') == 'True'  # Run with GUI by default

    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')  # Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FILE = os.getenv('LOG_FILE', f"selenium_fuzzer_{time.strftime('%Y%m%d_%H%M%S')}.log")  # Dynamic log file name

    # DevTools Configuration
    ENABLE_DEVTOOLS = os.getenv('ENABLE_DEVTOOLS', 'False') == 'True'  # Enable Chrome DevTools Protocol for monitoring

    # State Tracking Configuration
    TRACK_STATE = os.getenv('TRACK_STATE', 'False') == 'True'  # Enable state tracking before and after fuzzing

    # Timeout for Explicit Waits (in seconds)
    EXPLICIT_WAIT_TIMEOUT = int(os.getenv('EXPLICIT_WAIT_TIMEOUT', 10))  # Default wait time for Selenium explicit waits

    # Directory for log files
    LOG_FOLDER = os.getenv('LOG_FOLDER', 'log')
    if not os.path.exists(LOG_FOLDER):
        os.makedirs(LOG_FOLDER)

    @classmethod
    def get_log_file_path(cls):
        """Get the path for the log file, ensuring the folder is created."""
        return os.path.join(cls.LOG_FOLDER, cls.LOG_FILE)
