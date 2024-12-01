
# Selenium Fuzzer

The Selenium Fuzzer is a tool designed to perform automated testing on web pages using Selenium WebDriver. It identifies and interacts with form fields, dropdowns, iframes, and other page elements to test the robustness of web applications. The tool includes JavaScript error detection, tracking features, and state comparison.

## Features

- **Input Field Fuzzing**: Automatically detect and fuzz input fields using predefined payloads to identify vulnerabilities.
- **Dropdown Interaction**: Detect dropdowns and interact with all available options to test their resilience.
- **Iframe Handling**: Detect and interact with iframes to fuzz input fields within nested frames, extending coverage to iframe-based forms.
- **DOM Traversal**: Comprehensive ability to traverse and interact with elements deeper in the DOM hierarchy, including dynamically loaded elements or hidden elements that are made visible via JavaScript.
- **JavaScript Error Detection**: Capture JavaScript errors using both injected JavaScript and Chrome DevTools Protocol.
- **State Tracking**: Capture snapshots before and after interactions to compare changes, detect anomalies, and track JavaScript-triggered changes on the page.

## In Action 

Version 0.0.5

[Example Video/Screen of Fuzzer in Action](https://github.com/user-attachments/assets/25382382-0a73-4013-9779-aa244507dd6c)

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
- Console output provides an overview of current actions, JavaScript logs, DOM changes, iframe switches, and potential errors.

## Example Log Output

When running the fuzzer, you'll see outputs like this:

```plaintext



## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any feature requests, bug reports, or improvements.

## License━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 Starting Selenium Fuzzer...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🖥️  Starting ChromeDriver
   - Mode: GUI
Starting ChromeDriver. GUI Mode: Enabled
[2024-12-01 16:29:10,922] INFO: 🛠️ DevTools successfully initialized for JavaScript and network monitoring.
[2024-12-01 16:29:10,944] INFO: ℹ️ JavaScript for logging successfully injected.
[2024-12-01 16:29:10,953] INFO: ℹ️ JavaScript for DOM mutation monitoring successfully injected.
🛠️  DevTools successfully initialized for JavaScript and network monitoring.
ℹ️  JavaScript for console logging injected successfully.
🔍 JavaScript for DOM mutation monitoring injected successfully.

🌐 Accessing URL: http://localhost:8000/inputtypes.com/index.html...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨ Initializing Fuzzer...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 Detecting input fields on the page:
   - Including hidden elements, dynamically loaded elements, and elements inside iframes...

[2024-12-01 16:29:13,987] INFO: Found 1 suitable input elements on the page.
✅  Found 1 suitable input element(s):
   ────────────────────────────────────────────────
   [0] 📄 Name: Unnamed
      🏷️ Type: text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Please enter the indices of the fields to fuzz (comma-separated): 0

```


This project is licensed under the MIT License. See the `LICENSE` file for details.

## Contact

For more information or support, please reach out to the repository maintainer at cerdajasser@gmail.com