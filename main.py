import logging
import argparse
import time
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium_fuzzer.utils import generate_safe_payloads
from selenium_fuzzer.config import Config
from selenium_fuzzer.js_change_detector import JavaScriptChangeDetector
from selenium_fuzzer.fuzzer import Fuzzer
from selenium_fuzzer.selenium_driver import create_driver

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

    # Set up logging with dynamic filename in the /log folder
    log_filename = Config.get_log_file_path()
    logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL.upper(), logging.DEBUG),
                        filename=log_filename,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    # Set up console logging
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)  # Set to DEBUG to capture more console messages
    console_formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)

    if not any(isinstance(handler, logging.StreamHandler) for handler in logger.handlers):
        logger.addHandler(console_handler)

    # Create the WebDriver using `create_driver` with logging enabled
    driver = None
    try:
        headless = args.headless or Config.SELENIUM_HEADLESS
        driver = create_driver(headless=headless)

        # Initialize JavaScriptChangeDetector with DevTools option
        js_change_detector = JavaScriptChangeDetector(driver, enable_devtools=args.devtools or Config.ENABLE_DEVTOOLS)

        logger.info("\n=== Starting the Selenium Fuzzer ===\n")
        driver.get(args.url)
        logger.info(f"\n>>> Accessing URL: {args.url}\n")

        fuzzer = Fuzzer(driver, js_change_detector, args.url, track_state=args.track_state or Config.TRACK_STATE)

        if args.fuzz_fields:
            logger.info("\n=== Fuzzing Input Fields on the Page ===\n")
            input_fields = fuzzer.detect_inputs()
            if input_fields:
                payloads = generate_safe_payloads()
                for idx, input_element in enumerate(input_fields):
                    fuzzer.fuzz_field(input_element, payloads, delay=args.delay)

        if args.check_dropdowns:
            logger.info("\n=== Checking Dropdown Menus on the Page ===\n")
            fuzzer.fuzz_dropdowns(delay=args.delay)

    except Exception as e:
        logger.error(f"\n!!! An Unexpected Error Occurred: {e}\n")
    finally:
        if driver:
            driver.quit()
            logger.info("\n>>> Closed the browser and exited gracefully.\n")

if __name__ == "__main__":
    main()
