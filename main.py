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
            payloads = generate_safe_payloads()
            fuzzer.run_fuzz_fields(payloads, delay=args.delay)

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
        driver.quit()

if __name__ == "__main__":
    main()
