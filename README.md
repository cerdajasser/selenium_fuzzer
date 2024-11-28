
# Selenium Fuzzer

Selenium Fuzzer is a web fuzzing tool that uses Selenium to interact with and test dynamic websites. It automates the process of inputting test data into forms, selecting dropdown values, and monitoring JavaScript-based changes on webpages to detect errors or unexpected behaviors.

## Features
- **Fuzz Input Fields**: Automatically fuzz input fields on a target webpage with various payloads to test for vulnerabilities or unexpected behaviors.
- **Check Dropdown Menus**: Iteratively select each option in dropdown menus using a configurable selector and observe page responses for JavaScript updates or errors.
- **JavaScript Change Detection**: Monitor and detect changes in the page's JavaScript after interacting with input fields or dropdown menus.
- **Flexible Logging**: Create new log files for each target webpage, including both file and console outputs for detailed monitoring.

## Installation
### Prerequisites
- **Python 3.8 or higher**
- **Google Chrome** (latest version recommended)
- **ChromeDriver**: Make sure to install ChromeDriver and update the path in the configuration if necessary.

### Install Required Dependencies
1. Clone the repository:
   ```sh
   git clone https://github.com/cerdajasser/selenium_fuzzer.git
   cd selenium_fuzzer
   ```

2. Set up a virtual environment (optional but recommended):
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required dependencies:
   ```sh
   pip install -r requirements.txt
   ```

## Configuration
The configuration file (`selenium_fuzzer/config.py`) includes important settings such as:
- **CHROMEDRIVER_PATH**: The path to your ChromeDriver executable (default is `/usr/bin/chromedriver`).
- **SELENIUM_HEADLESS**: A boolean flag to run Chrome in headless mode.
- **LOG_LEVEL** and **LOG_FILE**: Logging configuration for both console and file outputs.

Make sure to update `CHROMEDRIVER_PATH` to the correct location of ChromeDriver on your system.

## Usage
To run Selenium Fuzzer, use the `main.py` script with the following command-line arguments:

```sh
python main.py [URL] [OPTIONS]
```

### Options
- **URL**: The URL of the target webpage to fuzz.
- `--headless`: Run Chrome in headless mode.
- `--delay DELAY`: Set delay between fuzzing attempts (in seconds). Default is 1 second.
- `--fuzz-fields`: Fuzz all input fields on the page.
- `--check-dropdowns`: Check dropdown menus on the page.
- `--dropdown-selector SELECTOR`: Set the CSS selector for the dropdown menus to be fuzzed. Default is `"select"`.

### Example Usage
1. To fuzz input fields on a webpage:
   ```sh
   python main.py http://example.com --fuzz-fields --delay 2
   ```
2. To fuzz input fields and check dropdown menus:
   ```sh
   python main.py http://example.com --fuzz-fields --check-dropdowns --headless
   ```
3. To use a custom selector for dropdown menus:
   ```sh
   python main.py http://example.com --check-dropdowns --dropdown-selector "#specific-dropdown" --headless
   ```

### Logs
Selenium Fuzzer logs its activities to both a log file (located in the `/log` directory) and the console. The log file name includes the timestamp for easy identification. Console and file logs provide:
- HTTP status of requests
- Changes detected in the webpage after each fuzzing attempt
- Selected dropdown values and their impact on the page
- Detailed information for input field interactions and JavaScript changes
- Improved readability for console output, making it easier to follow the fuzzing process

## New Improvements
- **Configurable Dropdown Selectors**: You can now specify the CSS selector to locate dropdown elements, making the tool more flexible for different page structures.
- **Graceful Exit**: Improved handling of exceptions to ensure the script quits gracefully and provides helpful debug information.
- **Detailed Logging**: Added more detailed logging, including logging JavaScript changes and the status of dropdown interactions, making debugging easier.
- **Consistent Console Output**: Both dropdown and input field interactions now provide consistent and human-readable console output to match logging standards.

## Troubleshooting
- **ChromeDriver Path**: Ensure `CHROMEDRIVER_PATH` in `config.py` points to the correct path of ChromeDriver on your system.
- **Permissions**: If you encounter permission errors, try running the script with elevated privileges or update the permissions on `chromedriver`.
- **Dynamic JavaScript Changes**: If dynamic JavaScript changes aren't being detected, make sure that the elements to be monitored are correctly specified in the `JavaScriptChangeDetector` module.
- **Dropdown Element Not Found**: If you encounter errors related to dropdown elements, try updating the `--dropdown-selector` argument to match the specific structure of the page you're testing.

## Contributing
Feel free to submit issues or pull requests to improve the Selenium Fuzzer. Contributions are always welcome.

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.
