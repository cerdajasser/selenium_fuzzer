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
import platform

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

def capture_artifacts_on_error(driver, run_id, scenario, last_action, last_element):
    """Capture artifacts (screenshots, console logs, DOM snapshot) on error."""
    timestamp_str = time.strftime('%Y%m%d_%H%M%S')
    artifacts_dir = "artifacts"
    if not os.path.exists(artifacts_dir):
        os.makedirs(artifacts_dir)

    # Screenshot
    screenshot_path = os.path.join(artifacts_dir, f"error_screenshot_{run_id}_{timestamp_str}.png")
    driver.save_screenshot(screenshot_path)

    # Console logs (browser)
    console_logs_path = os.path.join(artifacts_dir, f"console_logs_{run_id}_{timestamp_str}.log")
    try:
        logs = driver.get_log('browser')
        with open(console_logs_path, 'w', encoding='utf-8') as f:
            f.write(f"Run ID: {run_id}\nScenario: {scenario}\nLast Action: {last_action}\nLast Element: {last_element}\nCurrent URL: {driver.current_url}\n\n")
            for entry in logs:
                f.write(f"{entry['timestamp']} {entry['level']} {entry['message']}\n")
    except Exception as e:
        # If we can't get console logs, log that fact
        with open(console_logs_path, 'w', encoding='utf-8') as f:
            f.write("No console logs available.\n")

    # DOM snapshot
    dom_path = os.path.join(artifacts_dir, f"dom_snapshot_{run_id}_{timestamp_str}.html")
    with open(dom_path, 'w', encoding='utf-8') as f:
        f.write(f"<!-- Run ID: {run_id}, Scenario: {scenario}, Last Action: {last_action}, Last Element: {last_element}, URL: {driver.current_url} -->\n")
        f.write(driver.page_source)

    print(f"📸 Saved error screenshot: {screenshot_path}")
    print(f"📜 Saved console logs: {console_logs_path}")
    print(f"📄 Saved DOM snapshot: {dom_path}")

    # Store references somewhere accessible; reporter.py can later scan this directory and link artifacts.
    # We could log these paths with the logger as well.
    logging.getLogger().info(f"Artifacts saved: screenshot={screenshot_path}, console={console_logs_path}, dom={dom_path}")

def main():
    parser = argparse.ArgumentParser(description="Run Selenium Fuzzer on a target URL.")
    parser.add_argument("url", help="The URL to run the fuzzer against.")
    parser.add_argument("--headless", action="store_true", help="Run Chrome in headless mode.")
    parser.add_argument("--delay", type=int, default=1, help="Delay between fuzzing attempts in seconds.")
    parser.add_argument("--fuzz-fields", action="store_true", help="Fuzz input fields on the page.")
    parser.add_argument("--check-dropdowns", action="store_true", help="Check dropdown menus on the page.")
    parser.add_argument("--devtools", action="store_true", help="Enable Chrome DevTools Protocol to capture JavaScript and network activity.")
    parser.add_argument("--track-state", action="store_true", help="Track the state of the webpage before and after fuzzing.")
    parser.add_argument("--aggregate-only", action="store_true", help="Generate an aggregated report from existing logs without running fuzzing.")
    parser.add_argument("--run-id", default="default_run", help="A unique run ID to correlate logs and artifacts.")
    parser.add_argument("--scenario", default="default_scenario", help="A scenario/test case name for additional context.")
    args = parser.parse_args()

    # Record the start time of the run
    run_start_time = datetime.now()

    # Basic environment info for logging
    system_info = f"OS: {platform.system()} {platform.release()}, Browser: Chrome/Unknown"
    # Browser version retrieval would require devtools or capabilities check
    # For demonstration, we just log headless mode and devtools:
    env_info = f"Headless: {args.headless}, DevTools: {args.devtools}, Scenario: {args.scenario}, Run ID: {args.run_id}, {system_info}"

    if not args.aggregate_only:
        logger = setup_logger(args.url)
        logger.info("Environment Info: " + env_info)
        driver = None
        last_action = "Initialization"
        last_element = "N/A"
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
            last_action = "Accessing URL"
            driver.get(args.url)

            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print("✨ Initializing Fuzzer...")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

            fuzzer = Fuzzer(driver, js_change_detector, args.url, track_state=args.track_state or Config.TRACK_STATE)
            last_action = "Initializing Fuzzer"

            # Fuzz input fields if requested
            if args.fuzz_fields:
                print("\n📋 Detecting input fields on the page:")
                print("   - Including hidden elements, dynamically loaded elements, and elements inside iframes...\n")
                logger.info("\n=== Detecting Input Fields on the Page ===\n")
                try:
                    last_action = "Detecting Input Fields"
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
                                last_action = f"Fuzzing field at index {idx}"
                                last_element = input_fields[idx][1].get_attribute('name') or 'Unnamed'
                                fuzzer.fuzz_field(input_fields[idx], payloads, delay=args.delay)

            # Check dropdown menus if requested
            if args.check_dropdowns:
                print("\n📋 Checking dropdown menus on the page...")
                logger.info("\n=== Checking Dropdown Menus on the Page ===\n")
                try:
                    last_action = "Fuzzing Dropdowns"
                    fuzzer.fuzz_dropdowns(delay=args.delay)
                except Exception as e:
                    logger.error(f"\n!!! Unexpected Error during dropdown interaction: {e}\n")
                    capture_artifacts_on_error(driver, args.run_id, args.scenario, last_action, last_element)

        except (WebDriverException, TimeoutException) as e:
            if 'logger' in locals():
                logger.error(f"\n!!! Critical WebDriver Error: {e}\n")
            capture_artifacts_on_error(driver, args.run_id, args.scenario, "N/A", "N/A")
        except Exception as e:
            if 'logger' in locals():
                logger.error(f"\n!!! An Unexpected Error Occurred: {e}\n")
            capture_artifacts_on_error(driver, args.run_id, args.scenario, "N/A", "N/A")
        finally:
            if driver:
                driver.quit()
                print("\nClosed the browser and exited gracefully.")
                if 'logger' in locals():
                    logger.info("\n>>> Closed the browser and exited gracefully.\n")

    # After fuzzing or if in aggregate-only mode, generate the report
    reports_dir = "reports"
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)

    parsed = urlparse(args.url)
    domain = parsed.netloc or "report"
    safe_domain = domain.replace(":", "_").replace(".", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"fuzzer_report_{safe_domain}_{timestamp}.html"
    report_path = os.path.join(reports_dir, report_filename)

    # Initialize ReportGenerator with updated artifact_directory
    reporter = ReportGenerator(log_directory="log", artifact_directory="artifacts", run_start_time=run_start_time)
    reporter.parse_logs()
    reporter.find_artifacts("artifacts")
    reporter.generate_report(report_path)

    print(f"\nReport generated at: {report_path}")
    if 'logger' in locals():
        logger.info(f"Report generated at: {report_path}")

if __name__ == "__main__":
    main()
