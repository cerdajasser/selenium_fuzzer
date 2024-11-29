import logging
import argparse
import os
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium_fuzzer.utils import generate_safe_payloads
from selenium_fuzzer.config import Config
from selenium_fuzzer.js_change_detector import JavaScriptChangeDetector
from selenium_fuzzer.fuzzer import Fuzzer
import time

def main():
    parser = argparse.ArgumentParser(description="Run Selenium Fuzzer on a target URL.")
    parser.add_argument("url", help="The URL to run the fuzzer against.")
    parser.add_argument("--headless", action="store_true", help="Run Chrome in headless mode.")
    parser.add_argument("--delay", type=int, default=1, help="Delay between fuzzing attempts in seconds.")
    parser.add_argument("--fuzz-fields", action="store_true", help="Fuzz input fields on the page.")
    parser.add_argument("--check-dropdowns", action="store_true", help="Check dropdown menus on the page.")
    parser.add_argument("--devtools", action="store_true", help="Enable Chrome DevTools Protocol to capture JavaScript and network activity.")
    parser.add_argument("--track-state", action="store_true", help="Track the state of the webpage before and after fuzzing.")
    args = parser.parse_args()

    # Set up logging
    log_folder = "log"
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)

    log_filename = os.path.join(log_folder, f"selenium_fuzzer_{time.strftime('%Y%m%d_%H%M%S')}.log")
    logging.basicConfig(level=Config.LOG_LEVEL, filename=log_filename, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)

    # Set up Chrome options
    chrome_options = webdriver.ChromeOptions()
    if args.headless:
        chrome_options.add_argument("--headless")

    if args.devtools:
        chrome_options.add_argument("--auto-open-devtools-for-tabs")

    driver = None
    try:
        # Initialize WebDriver
        driver = webdriver.Chrome(service=webdriver.chrome.service.Service(Config.CHROMEDRIVER_PATH), options=chrome_options)

        # Initialize JavaScriptChangeDetector
        js_change_detector = JavaScriptChangeDetector(driver, enable_devtools=args.devtools)

        logger.info("\n=== Starting the Selenium Fuzzer ===\n")
        driver.get(args.url)
        logger.info(f"\n>>> Accessing URL: {args.url}\n")

        # Instantiate the Fuzzer
        fuzzer = Fuzzer(driver, js_change_detector, args.url, track_state=args.track_state)

        if args.fuzz_fields:
            logger.info("\n=== Fuzzing Input Fields on the Page ===\n")
            fuzzer.run_fuzz_fields(delay=args.delay)

        if args.check_dropdowns:
            logger.info("\n=== Checking Dropdown Menus on the Page ===\n")
            fuzzer.detect_dropdowns(delay=args.delay)

    except (WebDriverException, TimeoutException) as e:
        logger.error(f"\n!!! Critical WebDriver Error: {e}\n")
    except Exception as e:
        logger.error(f"\n!!! An Unexpected Error Occurred: {e}\n")
    finally:
        if driver:
            driver.quit()
            logger.info("\n>>> Closed the browser and exited gracefully.\n")

if __name__ == "__main__":
    main()
