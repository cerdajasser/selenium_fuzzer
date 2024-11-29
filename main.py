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

    # Set up logging with dynamic filename in the /log folder
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
        # Initialize the WebDriver
        driver = webdriver.Chrome(service=webdriver.chrome.service.Service(Config.CHROMEDRIVER_PATH), options=chrome_options)

        # Initialize JavaScriptChangeDetector with devtools option
        js_change_detector = JavaScriptChangeDetector(driver, enable_devtools=args.devtools)

        logger.info("\n=== Starting the Selenium Fuzzer ===\n")
        driver.get(args.url)
        logger.info(f"\n>>> Accessing URL: {args.url}\n")

        # Instantiate the Fuzzer with the provided URL
        fuzzer = Fuzzer(driver, js_change_detector, args.url, track_state=args.track_state)

        if args.fuzz_fields:
            logger.info("\n=== Fuzzing Input Fields on the Page ===\n")
            try:
                input_fields = fuzzer.detect_inputs()
                if not input_fields:
                    logger.warning("\n!!! No input fields detected on the page.\n")
                else:
                    print("Detected input fields:")
                    for idx, field in enumerate(input_fields):
                        field_type = field.get_attribute("type") or "unknown"
                        field_name = field.get_attribute("name") or "Unnamed"
                        print(f"{idx}: {field_name} (type: {field_type})")

                    selected_indices = input("Enter the indices of the fields to fuzz (comma-separated): ")
                    selected_indices = [int(idx.strip()) for idx in selected_indices.split(",") if idx.strip().isdigit()]

                    payloads = generate_safe_payloads()
                    for idx in selected_indices:
                        if 0 <= idx < len(input_fields):
                            fuzzer.fuzz_field(input_fields[idx], payloads, delay=args.delay)

            except (NoSuchElementException, TimeoutException) as e:
                logger.error(f"\n!!! Error during input fuzzing: {e}\n")
            except Exception as e:
                logger.error(f"\n!!! Unexpected Error during input fuzzing: {e}\n")

        if args.check_dropdowns:
            logger.info("\n=== Checking Dropdown Menus on the Page ===\n")
            try:
                fuzzer.detect_dropdowns(delay=args.delay)
            except (NoSuchElementException, TimeoutException) as e:
                logger.error(f"\n!!! Error during dropdown interaction: {e}\n")
            except Exception as e:
                logger.error(f"\n!!! Unexpected Error during dropdown interaction: {e}\n")

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
