import logging
import argparse
import os
import time
from urllib.parse import urlparse
from datetime import datetime

from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium_fuzzer.utils import generate_safe_payloads
from selenium_fuzzer.config import Config
from selenium_fuzzer.js_change_detector import JavaScriptChangeDetector
from selenium_fuzzer.fuzzer import Fuzzer
from selenium_fuzzer.selenium_driver import create_driver
from selenium_fuzzer.reporter import ReportGenerator

def setup_logger(url):
    parsed_url = os.path.basename(url)
    domain = parsed_url.replace(":", "_").replace(".", "_")
    log_filename = os.path.join(Config.LOG_FOLDER, f"selenium_fuzzer_{domain}_{time.strftime('%Y%m%d_%H%M%S')}.log")

    logger = logging.getLogger(f"selenium_fuzzer_{domain}")
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[%(asctime)s] %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    if not any(isinstance(handler, logging.FileHandler) for handler in logger.handlers):
        logger.addHandler(file_handler)

    return logger

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

    logger = setup_logger(args.url)

    driver = None
    try:
        headless = args.headless or Config.SELENIUM_HEADLESS
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("🚀 Starting Selenium Fuzzer...")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        logger.info("\n=== Starting the Selenium Fuzzer ===\n")

        print("\n🖥️  Starting ChromeDriver")
        print(f"   - Mode: {'Headless' if headless else 'GUI'}")

        driver = create_driver(headless=headless)

        js_change_detector = JavaScriptChangeDetector(driver, enable_devtools=args.devtools or Config.ENABLE_DEVTOOLS)

        print("🛠️  DevTools successfully initialized for JavaScript and network monitoring.")
        print("ℹ️  JavaScript for console logging injected successfully.")
        print("🔍 JavaScript for DOM mutation monitoring injected successfully.\n")

        logger.info(f"\n>>> Accessing the target URL: {args.url}\n")
        print(f"🌐 Accessing URL: {args.url}...\n")
        driver.get(args.url)

        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("✨ Initializing Fuzzer...")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        fuzzer = Fuzzer(driver, js_change_detector, args.url, track_state=args.track_state or Config.TRACK_STATE)

        # Fuzz input fields if requested
        if args.fuzz_fields:
            print("\n📋 Detecting input fields on the page:")
            print("   - Including hidden elements, dynamically loaded elements, and elements inside iframes...\n")
            logger.info("\n=== Detecting Input Fields on the Page ===\n")
            try:
                input_fields = fuzzer.detect_inputs()
                if not input_fields:
                    logger.warning("\n!!! No input fields detected on the page.\n")
                else:
                    print(f"✅  Found {len(input_fields)} suitable input element(s):")
                    print("   ────────────────────────────────────────────────")
                    for idx, (iframe_idx, field) in enumerate(input_fields):
                        field_type = field.get_attribute("type") or "unknown"
                        field_name = field.get_attribute("name") or "Unnamed"
                        print(f"   [{idx}] 📄 Name: {field_name}")
                        print(f"      🏷️ Type: {field_type}")

                    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                    selected_indices = input("\nPlease enter the indices of the fields to fuzz (comma-separated): ")
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
            print("\n📋 Checking dropdown menus on the page...")
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
            print("\nClosed the browser and exited gracefully.")
            logger.info("\n>>> Closed the browser and exited gracefully.\n")

        # After fuzzing is completed, generate the report
        reports_dir = "reports"
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)

        # Generate a run-specific filename
        # Extract a human-readable part of the domain if possible
        parsed = urlparse(args.url)
        domain = parsed.netloc or "report"
        # Clean the domain for filename use
        safe_domain = domain.replace(":", "_").replace(".", "_")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"fuzzer_report_{safe_domain}_{timestamp}.html"
        report_path = os.path.join(reports_dir, report_filename)

        reporter = ReportGenerator(log_directory="log", screenshot_directory="screenshots")
        reporter.parse_logs()
        reporter.find_screenshots()
        reporter.generate_report(report_path)

        print(f"\nReport generated at: {report_path}")
        logger.info(f"Report generated at: {report_path}")

if __name__ == "__main__":
    main()
