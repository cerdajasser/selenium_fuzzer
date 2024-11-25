import logging
import argparse
from selenium import webdriver
from selenium_fuzzer.fuzzer import Fuzzer
from selenium_fuzzer.utils import generate_safe_payloads
from selenium_fuzzer.config import Config

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
    driver = webdriver.Chrome(executable_path=Config.CHROMEDRIVER_PATH, options=chrome_options)

    try:
        driver.get(args.url)
        logger.info(f"Accessing URL: {args.url}")

        fuzzer = Fuzzer(driver)

        if args.fuzz_fields:
            payloads = generate_safe_payloads()
            fuzzer.run_fuzz_fields(payloads, delay=args.delay)

    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
