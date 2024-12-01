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

    # Directory for log files
    LOG_FOLDER = os.getenv('LOG_FOLDER', 'log')
    if not os.path.exists(LOG_FOLDER):
        os.makedirs(LOG_FOLDER)

    # Dynamic log file name in the specified log folder
    LOG_FILE_NAME = f"selenium_fuzzer_{time.strftime('%Y%m%d_%H%M%S')}.log"
    LOG_FILE = os.path.join(LOG_FOLDER, LOG_FILE_NAME)

    # DevTools Configuration
    ENABLE_DEVTOOLS = os.getenv('ENABLE_DEVTOOLS', 'False') == 'True'  # Enable Chrome DevTools Protocol for monitoring

    # State Tracking Configuration
    TRACK_STATE = os.getenv('TRACK_STATE', 'False') == 'True'  # Enable state tracking before and after fuzzing

    # Timeout for Explicit Waits (in seconds)
    EXPLICIT_WAIT_TIMEOUT = int(os.getenv('EXPLICIT_WAIT_TIMEOUT', 10))  # Default wait time for Selenium explicit waits

    @classmethod
    def get_log_file_path(cls):
        """Get the path for the log file, ensuring the folder is created."""
        return cls.LOG_FILE
