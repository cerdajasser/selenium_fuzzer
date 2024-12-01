
# Selenium Fuzzer

The Selenium Fuzzer is a tool designed to perform automated testing on web pages using the Selenium WebDriver. It identifies and interacts with form fields, dropdowns, and other page elements to test the robustness of web applications. The tool includes JavaScript error detection and tracking features.

## Features

- Fuzzing of input fields using pre-defined payloads.
- Dropdown interaction and validation.
- JavaScript error detection using both injected JavaScript and Chrome DevTools.
- State tracking and snapshot comparison before and after interactions.

## In action 

https://github.com/user-attachments/assets/51089107-1098-438c-bd3e-9472e2edb1ae

## Requirements

- Python 3.8+
- Google Chrome and ChromeDriver

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/selenium_fuzzer.git
   cd selenium_fuzzer
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Environment Variables** (optional):
   You can configure the following environment variables:
   - `CHROMEDRIVER_PATH`: Path to ChromeDriver.
   - `SELENIUM_HEADLESS`: Set to `False` to run ChromeDriver in GUI mode (default: `True`).
   - `LOG_LEVEL`: Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`).
   - `ENABLE_DEVTOOLS`: Set to `True` to enable Chrome DevTools Protocol for capturing JavaScript and network logs.
   - `TRACK_STATE`: Set to `True` to enable state tracking before and after fuzzing.

## Usage

Run the fuzzer on a target URL:

```bash
python main.py [URL] [OPTIONS]
```




### Arguments

- `url`: The target URL to run the fuzzer against.

### Options

- `--headless`: Run Chrome in headless mode.
- `--delay`: Delay between fuzzing attempts (in seconds).
- `--fuzz-fields`: Fuzz input fields on the page.
- `--check-dropdowns`: Check dropdown menus on the page.
- `--devtools`: Enable Chrome DevTools Protocol to capture JavaScript and network activity.
- `--track-state`: Track the state of the webpage before and after fuzzing.

### Example

```bash
python main.py --fuzz-fields --check-dropdowns --devtools http://localhost:8000/index.html
```

## Configuration

You can modify default settings through the `config.py` file:

```python
# Path to ChromeDriver
CHROMEDRIVER_PATH = os.getenv('CHROMEDRIVER_PATH', '/usr/bin/chromedriver')

# Selenium Chrome Options
SELENIUM_HEADLESS = os.getenv('SELENIUM_HEADLESS', 'False') == 'True'  # Run in GUI mode by default
```

## Logging

The fuzzer provides both file-based and console-based logging:

- Logs are saved in the `log/` directory.
- Console output provides an overview of current actions, JavaScript logs, and potential errors.

## Example Log Output

When running the fuzzer, you'll see outputs like this:

```plaintext
Starting ChromeDriver. GUI Mode: Enabled
[2024-11-30 14:31:07,417] ℹ️ JavaScript for logging successfully injected.
=== Starting the Selenium Fuzzer ===
>>> Accessing URL: http://localhost:8000/inputtypes.com/index.html
=== Fuzzing Input Fields on the Page ===
Found 1 suitable input elements on the page.
Detected input fields:
0: Unnamed (type: text)
```

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any feature requests, bug reports, or improvements.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Contact

For more information or support, please reach out to the repository maintainer at cerdajasser@gmail.com
