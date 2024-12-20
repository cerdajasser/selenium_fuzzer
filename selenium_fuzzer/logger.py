import logging
import os
from urllib.parse import urlparse

def setup_logger(url, log_level=logging.DEBUG):
    """
    Set up a logger that creates a new log file for each website and outputs to the console.
    """
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.replace(":", "_").replace(".", "_")
    log_filename = f"fuzzing_log_{domain}.log"

    logger = logging.getLogger(f"selenium_fuzzer_{domain}")
    logger.setLevel(log_level)

    # Create a file handler for logging to a file
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(log_level)

    # Create a console handler for additional output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)  # Set to DEBUG for detailed console output

    # Set a formatter for handlers
    formatter = logging.Formatter('[%(asctime)s] %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to the logger if they have not been added yet
    if not logger.hasHandlers():
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    logger.propagate = False  # Prevent duplicate log entries

    return logger
