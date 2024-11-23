import argparse
from selenium_fuzzer.fuzzer import Fuzzer

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Selenium Fuzzer Script")
    parser.add_argument("url", help="URL to fuzz")
    parser.add_argument("--fuzz-fields", action="store_true", help="Fuzz input fields")
    parser.add_argument("--click-elements", action="store_true", help="Click through clickable elements")
    parser.add_argument("--delay", type=int, default=1, help="Delay between actions in seconds")
    parser.add_argument("--headless", action="store_true", help="Run the browser in headless mode")

    args = parser.parse_args()

    fuzzer = Fuzzer(args.url, headless=args.headless)

    if args.fuzz_fields:
        fuzzer.run_fuzz_fields(delay=args.delay)

    if args.click_elements:
        fuzzer.run_click_elements(delay=args.delay)
