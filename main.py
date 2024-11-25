import logging
import argparse
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_fuzzer.fuzzer import Fuzzer
from selenium_fuzzer.utils import generate_safe_payloads
from selenium_fuzzer.config import Config
import time

def main():
    parser = argparse.ArgumentParser(description="Run Selenium Fuzzer on a target URL.")
    parser.add_argument("url", help="The URL to run the fuzzer against.")
    parser.add_argument("--headless", action="store_true", help="Run Chrome in headless mode.")
    parser.add_argument("--delay", type=int, default=1, help="Delay between fuzzing attempts in seconds.")
    parser.add_argument("--fuzz-fields", action="store_true", help="Fuzz input fields on the page.")
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

    try:
        driver.get(args.url)
        logger.info(f"Accessing URL: {args.url}")

        fuzzer = Fuzzer(driver)

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
                            logger.info(f"Inserted payload '{payload}' into field {idx}.")
                            time.sleep(args.delay)
                            # Validate that the payload was successfully entered
                            entered_value = field.get_attribute("value")
                            if entered_value == payload:
                                logger.info(f"Payload '{payload}' successfully entered into field {idx}.")
                            else:
                                logger.warning(f"Payload '{payload}' could not be verified in field {idx}. Entered value: '{entered_value}'")
                        except Exception as e:
                            logger.error(f"Error inserting payload into field {idx}: {e}")

            # Submit the form explicitly
            for form in driver.find_elements(By.TAG_NAME, "form"):
                try:
                    submit_button = form.find_element(By.XPATH, "//input[@type='submit'] | //button[@type='submit']")
                    submit_button.click()
                    logger.info("Clicked submit button to submit form.")
                except NoSuchElementException:
                    try:
                        # If no submit button, try sending ENTER key to any input field in the form
                        input_element = form.find_element(By.XPATH, ".//input")
                        input_element.send_keys(Keys.ENTER)
                        logger.info("Sent ENTER key to input element to submit form.")
                    except Exception as e:
                        logger.error(f"Error submitting form by sending ENTER key: {e}")
                except Exception as e:
                    logger.error(f"Error clicking submit button: {e}")

            # Look for updated JavaScript text to determine the result of form submission
            time.sleep(2)  # Wait for potential JavaScript updates
            page_source = driver.page_source
            success_message = "Form submitted! No validation errors."
            if success_message in page_source:
                logger.info("Form submitted successfully with no validation errors.")
            else:
                logger.warning("Form submission may have errors or unexpected behavior. Please review the page for error messages.")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        input("Press Enter to close the browser...")  # Keep the browser open until user input
        driver.quit()

if __name__ == "__main__":
    main()
