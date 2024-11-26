import logging
import argparse
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium_fuzzer.utils import generate_safe_payloads
from selenium_fuzzer.config import Config
import time

def main():
    # Import here to avoid circular import issues
    from selenium_fuzzer.js_change_detector import JavaScriptChangeDetector
    from selenium_fuzzer.fuzzer import Fuzzer

    parser = argparse.ArgumentParser(description="Run Selenium Fuzzer on a target URL.")
    parser.add_argument("url", help="The URL to run the fuzzer against.")
    parser.add_argument("--headless", action="store_true", help="Run Chrome in headless mode.")
    parser.add_argument("--delay", type=int, default=1, help="Delay between fuzzing attempts in seconds.")
    parser.add_argument("--fuzz-fields", action="store_true", help="Fuzz input fields on the page.")
    parser.add_argument("--check-dropdowns", action="store_true", help="Check dropdown menus on the page.")
    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(level=Config.LOG_LEVEL, filename=Config.LOG_FILE, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    # Set up Chrome options
    chrome_options = webdriver.ChromeOptions()
    if args.headless:
        chrome_options.add_argument("--headless")

    # Initialize the WebDriver
    driver = webdriver.Chrome(service=webdriver.chrome.service.Service(Config.CHROMEDRIVER_PATH), options=chrome_options)

    # Create JavaScriptChangeDetector instance
    js_change_detector = JavaScriptChangeDetector(driver)

    try:
        driver.get(args.url)
        logger.info(f"Accessing URL: {args.url}")

        # Pass JavaScriptChangeDetector instance to Fuzzer
        fuzzer = Fuzzer(driver, js_change_detector)

        if args.fuzz_fields:
            # Prompt the user to select fields to fuzz
            input_fields = fuzzer.detect_inputs()
            if not input_fields:
                logger.warning("No input fields detected on the page.")
                return

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
                    field = input_fields[idx]
                    for payload in payloads:
                        try:
                            field.clear()
                            field.send_keys(payload)
                            field.send_keys(Keys.TAB)  # Trigger potential JavaScript events after input
                            field.send_keys(Keys.ENTER)  # Explicitly hit enter after tabbing
                            logger.info(f"Inserted payload '{payload}' into field {idx}.")
                            time.sleep(args.delay)
                            # Validate that the payload was successfully entered
                            entered_value = field.get_attribute("value")
                            if entered_value == payload:
                                logger.info(f"Payload '{payload}' successfully entered into field {idx}.")
                            else:
                                logger.warning(f"Payload '{payload}' could not be verified in field {idx}. Entered value: '{entered_value}'")
                            # Check for JavaScript changes after input
                            js_change_detector.check_for_js_changes()
                        except Exception as e:
                            logger.error(f"Error inserting payload into field {idx}: {e}")

            # Submit the form explicitly
            for form in driver.find_elements(By.TAG_NAME, "form"):
                try:
                    submit_button = form.find_element(By.XPATH, "//input[@type='submit'] | //button[@type='submit']")
                    submit_button.click()
                    logger.info("Clicked submit button to submit form.")
                except Exception as e:
                    logger.error(f"Error clicking submit button: {e}")
                # Check for JavaScript changes after form submission
                js_change_detector.check_for_js_changes()

        if args.check_dropdowns:
            # Find all dropdown menus (select elements)
            dropdowns = driver.find_elements(By.TAG_NAME, "select")
            if not dropdowns:
                logger.warning("No dropdown menus detected on the page.")
            else:
                for idx, dropdown in enumerate(dropdowns):
                    try:
                        select = Select(dropdown)
                        options = select.options
                        for option in options:
                            select.select_by_visible_text(option.text)
                            logger.info(f"Selected option '{option.text}' from dropdown {idx}.")
                            time.sleep(args.delay)  # Wait for potential JavaScript updates
                            # Check for JavaScript changes or errors on the page
                            js_change_detector.check_for_js_changes()
                    except Exception as e:
                        logger.error(f"Error interacting with dropdown {idx}: {e}")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        input("Press Enter to close the browser...")  # Keep the browser open until user input
        driver.quit()

if __name__ == "__main__":
    main()
