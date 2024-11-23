import argparse
from selenium_fuzzer.fuzzer import Fuzzer
from selenium_fuzzer.config import Config


def main():
    # Set up argument parser for command-line options
    parser = argparse.ArgumentParser(description="Selenium-based fuzzer for input fields in Angular Material applications.")
    parser.add_argument("-url", required=True, help="The URL to fuzz")
    parser.add_argument("-attempts", type=int, default=1, help="Number of fuzz attempts per field")
    parser.add_argument("-delay", type=int, default=1, help="Delay between fuzzing attempts in seconds")
    parser.add_argument("-headless", action="store_true", help="Run Chrome in headless mode")

    args = parser.parse_args()

    # Update configuration based on arguments
    Config.SELENIUM_HEADLESS = args.headless
    url = args.url
    attempts = args.attempts
    delay = args.delay

    # Instantiate the fuzzer and run it
    fuzzer = Fuzzer(url)
    fuzzer.run(delay=delay)


if __name__ == "__main__":
    main()
