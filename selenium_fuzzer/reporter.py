import os
import re
import datetime
from typing import List, Dict
import html

class ReportGenerator:
    def __init__(self, log_directory: str = "log", screenshot_directory: str = "screenshots"):
        self.log_directory = log_directory
        self.screenshot_directory = screenshot_directory
        self.fuzzed_fields_details = []    # (field_name, payload, iframe, url)
        self.fuzzed_dropdowns_details = [] # (dropdown_name, option, url)
        self.errors = []                   # (timestamp, error_level, error_message, url)
        self.screenshots = []

    def parse_logs(self):
        if not os.path.exists(self.log_directory):
            print(f"Log directory {self.log_directory} not found.")
            return

        # Only consider files that start with "fuzzing_log_" and end with ".log"
        log_files = [f for f in os.listdir(self.log_directory) if f.startswith("fuzzing_log_") and f.endswith(".log")]
        if not log_files:
            print("No matching log files found in the log directory.")
            return

        # Sort by modification time (newest first)
        log_files = sorted(log_files, key=lambda x: os.path.getmtime(os.path.join(self.log_directory, x)), reverse=True)
        latest_log_file = log_files[0]
        print(f"Parsing latest log file: {latest_log_file}")

        # Regex patterns based on the logs you provided:
        field_fuzz_pattern = re.compile(
            r".*Payload '(.*?)' successfully entered into field '(.*?)' in iframe (.*?)\. URL: (.*?)$"
        )
        dropdown_option_pattern = re.compile(
            r".*Selected option '(.*?)' from dropdown '(.*?)' at URL: (.*?)$"
        )
        error_pattern = re.compile(r"(.*)(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),.*(ERROR|CRITICAL).*?: (.*?) at URL: (.*?)$")

        with open(os.path.join(self.log_directory, latest_log_file), 'r', encoding='utf-8') as lf:
            for line in lf:
                # Fields
                ff_match = field_fuzz_pattern.search(line)
                if ff_match:
                    payload = ff_match.group(1)
                    field_name = ff_match.group(2)
                    iframe_info = ff_match.group(3)
                    url = ff_match.group(4)
                    # Escape values to prevent XSS
                    self.fuzzed_fields_details.append((
                        html.escape(field_name),
                        html.escape(payload),
                        html.escape(iframe_info),
                        html.escape(url)
                    ))

                # Dropdowns
                do_match = dropdown_option_pattern.search(line)
                if do_match:
                    option = do_match.group(1)
                    dropdown_name = do_match.group(2)
                    url = do_match.group(3)
                    # Escape to prevent XSS
                    self.fuzzed_dropdowns_details.append((
                        html.escape(dropdown_name),
                        html.escape(option),
                        html.escape(url)
                    ))

                # Errors
                e_match = error_pattern.search(line)
                if e_match:
                    timestamp = e_match.group(2)
                    error_level = e_match.group(3)
                    error_message = e_match.group(4)
                    url = e_match.group(5)
                    # Escape these values as well
                    self.errors.append((
                        html.escape(timestamp),
                        html.escape(error_level),
                        html.escape(error_message),
                        html.escape(url)
                    ))

    def find_screenshots(self):
        if os.path.exists(self.screenshot_directory):
            self.screenshots = [f for f in os.listdir(self.screenshot_directory) if f.lower().endswith((".png", ".jpg", ".jpeg"))]

    def generate_report(self, output_file: str = "report.html"):
        html_content = [
            "<!DOCTYPE html>",
            "<html lang='en'>",
            "<head>",
            "<meta charset='UTF-8'>",
            "<meta name='viewport' content='width=device-width, initial-scale=1.0'>",
            "<title>Fuzzer Report</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin:0; padding:0; background: #f5f5f5; }",
            "header { background: #333; color: #fff; padding: 20px; }",
            "header h1 { margin: 0; font-size: 1.5em; }",
            "nav { background: #444; color: #fff; padding: 10px; }",
            "nav a { color: #fff; margin-right: 15px; text-decoration: none; font-weight: bold; }",
            "nav a:hover { text-decoration: underline; }",
            ".container { max-width: 1200px; margin: 20px auto; background: #fff; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }",
            "h2, h3 { color: #333; border-bottom: 1px solid #ddd; padding-bottom: 5px; }",
            "p, li { line-height: 1.6; }",
            "table { border-collapse: collapse; width: 100%; margin-bottom: 20px; table-layout: fixed; }",
            "th, td { border: 1px solid #ccc; padding: 10px; text-align: left; font-size: 0.95em; word-wrap: break-word; white-space: pre-wrap; }",
            "th { background: #f0f0f0; font-weight: bold; }",
            "/* Ensure long payloads wrap gracefully */",
            ".error { color: red; font-weight: bold; }",
            ".screenshot { margin: 10px 0; max-width: 600px; border: 1px solid #ccc; padding: 5px; background: #fafafa; }",
            ".section { margin-bottom: 40px; }",
            ".no-data { color: #777; font-style: italic; }",
            ".icon { margin-right: 5px; }",
            "</style>",
            "</head>",
            "<body>",
            "<header>",
            f"<h1>Fuzzer Report - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</h1>",
            "</header>",
            "<nav>",
            "<a href='#fields'>💻 Fields</a>",
            "<a href='#dropdowns'>🔽 Dropdowns</a>",
            "<a href='#errors'>❌ Errors</a>",
            "<a href='#screenshots'>📷 Screenshots</a>",
            "</nav>",
            "<div class='container'>"
        ]

        # Fields Fuzzed
        html_content.append("<div class='section' id='fields'>")
        html_content.append("<h2>💻 Fuzzed Input Fields</h2>")
        if self.fuzzed_fields_details:
            html_content.append("<table>")
            html_content.append("<tr><th>Field Name</th><th>Payload</th><th>Iframe</th><th>URL</th></tr>")
            for field_name, payload, iframe, url in self.fuzzed_fields_details:
                html_content.append(f"<tr><td>{field_name}</td><td>{payload}</td><td>{iframe}</td><td><a href='{url}' target='_blank'>{url}</a></td></tr>")
            html_content.append("</table>")
        else:
            html_content.append("<p class='no-data'>No input fields were fuzzed.</p>")
        html_content.append("</div>")

        # Dropdowns Checked
        html_content.append("<div class='section' id='dropdowns'>")
        html_content.append("<h2>🔽 Checked Dropdowns</h2>")
        if self.fuzzed_dropdowns_details:
            html_content.append("<table>")
            html_content.append("<tr><th>Dropdown Name</th><th>Option Selected</th><th>URL</th></tr>")
            for dropdown_name, option, url in self.fuzzed_dropdowns_details:
                html_content.append(f"<tr><td>{dropdown_name}</td><td>{option}</td><td><a href='{url}' target='_blank'>{url}</a></td></tr>")
            html_content.append("</table>")
        else:
            html_content.append("<p class='no-data'>No dropdown interactions were recorded.</p>")
        html_content.append("</div>")

        # Major Errors
        html_content.append("<div class='section' id='errors'>")
        html_content.append("<h2>❌ Major Errors</h2>")
        if self.errors:
            html_content.append("<table>")
            html_content.append("<tr><th>Timestamp</th><th>Level</th><th>Message</th><th>URL</th></tr>")
            for timestamp, level, message, url in self.errors:
                html_content.append(f"<tr><td>{timestamp}</td><td class='error'>{level}</td><td>{message}</td><td><a href='{url}' target='_blank'>{url}</a></td></tr>")
            html_content.append("</table>")
        else:
            html_content.append("<p class='no-data'>No major errors recorded.</p>")
        html_content.append("</div>")

        # Screenshots
        html_content.append("<div class='section' id='screenshots'>")
        html_content.append("<h2>📷 Screenshots</h2>")
        if self.screenshots:
            for screenshot in self.screenshots:
                screenshot_path = os.path.join(self.screenshot_directory, screenshot)
                html_content.append(f"<div class='screenshot'><img src='{html.escape(screenshot_path)}' alt='{html.escape(screenshot)}' style='max-width:100%;'/><br><small>{html.escape(screenshot)}</small></div>")
        else:
            html_content.append("<p class='no-data'>No screenshots found.</p>")
        html_content.append("</div>")

        html_content.append("</div>")  # .container
        html_content.append("</body></html>")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(html_content))

        print(f"Report generated: {output_file}")
