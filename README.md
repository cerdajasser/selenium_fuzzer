# Selenium Fuzzer

The Selenium Fuzzer is an advanced automated testing tool designed to rigorously assess the robustness of web applications. Leveraging Selenium WebDriver, it systematically identifies and interacts with form fields, dropdowns, iframes, and other critical page elements. The tool integrates JavaScript error detection, state tracking, and comprehensive reporting to provide insightful analysis and uncover potential vulnerabilities.

## Features

- **Input Field Fuzzing**: Automatically detect and fuzz input fields using predefined payloads to identify vulnerabilities, including hidden and dynamically loaded elements.
- **Dropdown Interaction**: Detect dropdown menus and interact with all available options to test their resilience against unexpected inputs.
- **Iframe Handling**: Identify and interact with iframes, enabling fuzzing of input fields within nested frames for extended coverage.
- **DOM Traversal**: Comprehensive traversal and interaction with elements deeper in the DOM hierarchy, ensuring coverage of dynamically loaded or hidden elements.
- **JavaScript Error Detection**: Capture JavaScript errors using both injected JavaScript and the Chrome DevTools Protocol for in-depth debugging.
- **State Tracking**: Capture snapshots of the webpage's state before and after interactions to compare changes, detect anomalies, and track JavaScript-triggered modifications.
- **Artifact Collection**: Automatically gather screenshots, console logs, and DOM snapshots upon encountering errors, facilitating detailed post-mortem analysis.
- **Comprehensive Reporting**: Generate detailed HTML reports aggregating fuzzing activities, errors, JavaScript logs, actions performed, visited URLs, and collected artifacts.

## In Action

### Version 0.0.6

[![Fuzzer in Action](https://github.com/user-attachments/assets/d57f73d6-c81f-44cd-a18e-4841128d0210)](https://github.com/user-attachments/assets/d57f73d6-c81f-44cd-a18e-4841128d0210)

*Click the image above to watch the Selenium Fuzzer in action.*

## Requirements

- **Python 3.8+**
- **Google Chrome** and **ChromeDriver**

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
   You can configure the following environment variables to customize the fuzzer's behavior:
   - `CHROMEDRIVER_PATH`: Path to ChromeDriver.
   - `SELENIUM_HEADLESS`: Set to `False` to run ChromeDriver in GUI mode (default: `True`).
   - `LOG_LEVEL`: Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`).
   - `ENABLE_DEVTOOLS`: Set to `True` to enable Chrome DevTools Protocol for capturing JavaScript and network logs.
   - `TRACK_STATE`: Set to `True` to enable state tracking before and after fuzzing.

   **Example (Unix-based systems):**
   ```bash
   export CHROMEDRIVER_PATH=/path/to/chromedriver
   export SELENIUM_HEADLESS=True
   export LOG_LEVEL=DEBUG
   export ENABLE_DEVTOOLS=True
   export TRACK_STATE=True
   ```

## Usage

Run the fuzzer on a target URL with desired options:

```bash
python main.py [URL] [OPTIONS]
```

### Arguments

- `url`: **(Required)** The target URL to run the fuzzer against.

### Options

- `--headless`: Run Chrome in headless mode.
- `--delay`: Delay between fuzzing attempts (in seconds). *(Default: 1)*
- `--fuzz-fields`: Fuzz input fields on the page.
- `--check-dropdowns`: Check and interact with dropdown menus on the page.
- `--devtools`: Enable Chrome DevTools Protocol to capture JavaScript and network activity.
- `--track-state`: Track the state of the webpage before and after fuzzing.
- `--aggregate-only`: Generate an aggregated report from existing logs without running fuzzing.
- `--run-id`: A unique run ID to correlate logs and artifacts. *(Default: `default_run`)*
- `--scenario`: A scenario/test case name for additional context. *(Default: `default_scenario`)*

### Examples

1. **Fuzz Input Fields with DevTools and State Tracking**:
   ```bash
   python main.py --fuzz-fields --devtools --track-state http://localhost:8000/inputtypes.com/index.html
   ```

2. **Fuzz Dropdowns Only**:
   ```bash
   python main.py --check-dropdowns http://localhost:8000/inputtypes.com/index.html
   ```

3. **Generate Aggregated Report Without Fuzzing**:
   ```bash
   python main.py --aggregate-only http://localhost:8000/inputtypes.com/index.html
   ```

## Configuration

You can modify default settings through the `config.py` file or by setting environment variables as described in the **Installation** section.

### Example `config.py`:

```python
import os

# Path to ChromeDriver
CHROMEDRIVER_PATH = os.getenv('CHROMEDRIVER_PATH', '/usr/bin/chromedriver')

# Selenium Chrome Options
SELENIUM_HEADLESS = os.getenv('SELENIUM_HEADLESS', 'True') == 'True'  # Run in headless mode by default

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')  # Default logging level
ENABLE_DEVTOOLS = os.getenv('ENABLE_DEVTOOLS', 'False') == 'True'  # Disable DevTools by default
TRACK_STATE = os.getenv('TRACK_STATE', 'False') == 'True'  # Disable state tracking by default

# Directories
LOG_FOLDER = "log"
ARTIFACTS_FOLDER = "artifacts"
REPORTS_FOLDER = "reports"
```

## Logging

The fuzzer provides both file-based and console-based logging to ensure comprehensive monitoring and debugging capabilities.

- **Log Files**:
  - Stored in the `log/` directory.
  - Each run generates a separate log file named in the format `selenium_fuzzer_<domain>_<timestamp>.log`.

- **Console Output**:
  - Provides real-time feedback on current actions, JavaScript logs, DOM changes, iframe switches, and potential errors.

## Report Generation

After completing a fuzzing session, the fuzzer generates a detailed HTML report summarizing all activities, errors, and collected artifacts.

- **Report Location**:
  - Saved in the `reports/` directory.
  - Named in the format `fuzzer_report_<domain>_<timestamp>.html`.

- **Report Contents**:
  - **Fuzzed Input Fields**: Lists all input fields that were fuzzed along with the payloads used and the URLs tested.
  - **Checked Dropdowns**: Details interactions with dropdown menus, including options selected and associated URLs.
  - **Major Errors**: Aggregates all critical errors encountered during fuzzing with timestamps, error levels, messages, and relevant URLs.
  - **JavaScript Errors & Warnings**: Captures and displays JavaScript errors and warnings from DevTools.
  - **Selenium Fuzzer Actions & Visited URLs**: Chronicles all actions performed by the fuzzer and the URLs it accessed.
  - **Screenshots**: Embeds screenshots taken during fuzzing, especially those captured upon encountering errors.
  - **Additional Artifacts**: Provides links to console logs and DOM snapshots for deeper analysis.

## Example Log Output

When running the fuzzer, you'll observe detailed log outputs similar to the following:

```plaintext
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 Starting Selenium Fuzzer...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🖥️  Starting ChromeDriver
   - Mode: GUI
🛠️  DevTools successfully initialized for JavaScript and network monitoring.
ℹ️  JavaScript for console logging injected successfully.
🔍 JavaScript for DOM mutation monitoring injected successfully.

🌐 Accessing URL: http://localhost:8000/inputtypes.com/index.html...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨ Initializing Fuzzer...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 Detecting input fields on the page:
   - Including hidden elements, dynamically loaded elements, and elements inside iframes...

✅  Found 1 suitable input element(s):
   ────────────────────────────────────────────────
   [0] 📄 Name: Unnamed
      🏷️ Type: text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Please enter the indices of the fields to fuzz (comma-separated): 0

📄 Fuzzing field 'Unnamed' with payload 'oCAW42oXaD' at URL: http://localhost:8000/inputtypes.com/index.html
📜 Saved console logs: artifacts/console_logs_default_run_20241207_091726.log
📄 Saved DOM snapshot: artifacts/dom_snapshot_default_run_20241207_091726.html

📷 Screenshots:
- artifacts/error_screenshot_default_run_20241207_091726.png

Report generated at: reports/fuzzer_report_localhost_8000_20241207_091726.html
```

## License

This project is licensed under the MIT License. See the [`LICENSE`](LICENSE) file for details.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any feature requests, bug reports, or improvements.

## Contact

For more information or support, please reach out to the repository maintainer at [cerdaj@example.com](mailto:cerdaj@example.com).