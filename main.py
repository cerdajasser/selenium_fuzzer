import logging
import argparse
import time
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium_fuzzer.utils import generate_safe_payloads
from selenium_fuzzer.config import Config
from selenium_fuzzer.js_change_detector import JavaScriptChangeDetector
from selenium_fuzzer.fuzzer import Fuzzer
from selenium_fuzzer.selenium_driver import create_driver
from selenium_fuzzer.logger import setup_logger

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
    log_file_path = Config.get_log_file_path()
    logger = setup_logger(url=args.url, log_file=log_file_path)

    # Create the WebDriver using `create_driver` with logging enabled
    driver = None
    try:
        # Determine headless mode based on arguments or configuration
        headless = args.headless or Config.SELENIUM_HEADLESS
        print("Starting the Selenium Fuzzer...\n")
        logger.info("\n=== Starting the Selenium Fuzzer ===\n")

        driver = create_driver(headless=headless)

        # Initialize JavaScriptChangeDetector with DevTools option
        js_change_detector = JavaScriptChangeDetector(driver, enable_devtools=args.devtools or Config.ENABLE_DEVTOOLS)

        print(f"Accessing URL: {args.url}...\n")
        logger.info(f"\n>>> Accessing the target URL: {args.url}\n")
        driver.get(args.url)

        # Instantiate the Fuzzer with the provided URL and state tracking option
        print("Initializing the Fuzzer...\n")
        fuzzer = Fuzzer(driver, js_change_detector, args.url, track_state=args.track_state or Config.TRACK_STATE)

        # Fuzz input fields if requested
        if args.fuzz_fields:
            print("Detecting input fields on the page...\n")
            logger.info("\n=== Detecting Input Fields on the Page ===\n")
            try:
                input_fields = fuzzer.detect_inputs()
                if not input_fields:
                    logger.warning("\n!!! No input fields detected on the page.\n")
                    return

                print(f"Detected {len(input_fields)} input field(s):")
                for idx, field in enumerate(input_fields):
                    field_type = field.get_attribute("type") or "unknown"
                    field_name = field.get_attribute("name") or "Unnamed"
                    print(f"  [{idx}] - Name: {field_name}, Type: {field_type}")

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

        # Check dropdown menus if requested
        if args.check_dropdowns:
            print("Checking dropdown menus on the page...\n")
            logger.info("\n=== Checking Dropdown Menus on the Page ===\n")
            try:
                fuzzer.fuzz_dropdowns(delay=args.delay)
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
            print("Closed the browser and exited gracefully.\n")
            logger.info("\n>>> Closed the browser and exited gracefully.\n")

if __name__ == "__main__":
    main()
