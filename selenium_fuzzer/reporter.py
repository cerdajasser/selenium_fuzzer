import os
import re
import datetime
from typing import List, Dict

class ReportGenerator:
    def __init__(self, log_directory: str = "log", screenshot_directory: str = "screenshots"):
        self.log_directory = log_directory
        self.screenshot_directory = screenshot_directory
        self.fuzzed_fields_details = []  # [(field_name, payload, iframe_index, url), ...]
        self.fuzzed_dropdowns_details = []  # [(dropdown_name, option, url), ...]
        self.errors = []  # [(timestamp, error_level, error_message, url)]
        self.screenshots = []

    def parse_logs(self):
        if not os.path.exists(self.log_directory):
            print(f"Log directory {self.log_directory} not found.")
            return

        log_files = [f for f in os.listdir(self.log_directory) if f.endswith(".log")]

        # Regex to match enhanced logs
        field_fuzz_pattern = re.compile(r"Successfully entered payload '(.*?)' into field '(.*?)'\.")
        field_context_pattern = re.compile(r"Fuzzing field '(.*?)' in iframe (.*?) at URL: (.*?)$")
        dropdown_fuzz_pattern = re.compile(r"Fuzzing dropdown '(.*?)' at URL: (.*?)$")
        dropdown_option_pattern = re.compile(r"Selected option '(.*?)' from dropdown.")
        error_pattern = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),.*(ERROR|CRITICAL).*?: (.*?) at URL: (.*?)$")

        current_field_context = {}    # Keep track of last known context for fields
        current_dropdown_context = {} # Keep track of last known context for dropdowns

        for log_file in log_files:
            log_path = os.path.join(self.log_directory, log_file)
            with open(log_path, 'r', encoding='utf-8') as lf:
                for line in lf:
                    # Capture field context
                    fc_match = field_context_pattern.search(line)
                    if fc_match:
                        field_name = fc_match.group(1)
                        iframe_info = fc_match.group(2)
                        url = fc_match.group(3)
                        current_field_context = {
                            'field_name': field_name,
                            'iframe': iframe_info,
                            'url': url
                        }

                    # When a payload is inserted successfully
                    ff_match = field_fuzz_pattern.search(line)
                    if ff_match and current_field_context:
                        payload = ff_match.group(1)
                        # field is already known from current_field_context
                        self.fuzzed_fields_details.append((
                            current_field_context['field_name'],
                            payload,
                            current_field_context['iframe'],
                            current_field_context['url']
                        ))

                    # Capture dropdown context
                    dcf_match = dropdown_fuzz_pattern.search(line)
                    if dcf_match:
                        dropdown_name = dcf_match.group(1)
                        url = dcf_match.group(2)
                        current_dropdown_context = {
                            'dropdown_name': dropdown_name,
                            'url': url
                        }

                    do_match = dropdown_option_pattern.search(line)
                    if do_match and current_dropdown_context:
                        option = do_match.group(1)
                        self.fuzzed_dropdowns_details.append((
                            current_dropdown_context['dropdown_name'],
                            option,
                            current_dropdown_context['url']
                        ))

                    # Capture errors with URL
                    e_match = error_pattern.search(line)
                    if e_match:
                        timestamp = e_match.group(1)
                        error_level = e_match.group(2)
                        error_message = e_match.group(3)
                        url = e_match.group(4)
                        self.errors.append((timestamp, error_level, error_message, url))

    def find_screenshots(self):
        if os.path.exists(self.screenshot_directory):
            self.screenshots = [f for f in os.listdir(self.screenshot_directory) if f.lower().endswith((".png", ".jpg", ".jpeg"))]

    def generate_report(self, output_file: str = "report.html"):
        html = [
            "<!DOCTYPE html>",
            "<html lang='en'>",
            "<head><meta charset='UTF-8'><title>Fuzzer Report</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 20px; }",
            "h1, h2, h3 { color: #333; }",
            "table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }",
            "th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }",
            "th { background: #f9f9f9; }",
            ".error { color: red; font-weight: bold; }",
            ".screenshot { margin: 10px 0; max-width: 600px; border: 1px solid #ccc; padding: 5px; }",
            "</style>",
            "</head>",
            "<body>",
            f"<h1>Fuzzer Report - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</h1>"
        ]

        # Fields Fuzzed
        html.append("<h2>Fuzzed Input Fields</h2>")
        if self.fuzzed_fields_details:
            html.append("<table>")
            html.append("<tr><th>Field Name</th><th>Payload</th><th>Iframe</th><th>URL</th></tr>")
            for field_name, payload, iframe, url in self.fuzzed_fields_details:
                html.append(f"<tr><td>{field_name}</td><td>{payload}</td><td>{iframe}</td><td>{url}</td></tr>")
            html.append("</table>")
        else:
            html.append("<p>No input fields were fuzzed.</p>")

        # Dropdowns Checked
        html.append("<h2>Checked Dropdowns</h2>")
        if self.fuzzed_dropdowns_details:
            html.append("<table>")
            html.append("<tr><th>Dropdown Name</th><th>Option Selected</th><th>URL</th></tr>")
            for dropdown_name, option, url in self.fuzzed_dropdowns_details:
                html.append(f"<tr><td>{dropdown_name}</td><td>{option}</td><td>{url}</td></tr>")
            html.append("</table>")
        else:
            html.append("<p>No dropdown interactions were recorded.</p>")

        # Major Errors
        html.append("<h2>Major Errors</h2>")
        if self.errors:
            html.append("<table>")
            html.append("<tr><th>Timestamp</th><th>Level</th><th>Message</th><th>URL</th></tr>")
            for timestamp, level, message, url in self.errors:
                html.append(f"<tr><td>{timestamp}</td><td class='error'>{level}</td><td>{message}</td><td>{url}</td></tr>")
            html.append("</table>")
        else:
            html.append("<p>No major errors recorded.</p>")

        # Screenshots
        html.append("<h2>Screenshots</h2>")
        if self.screenshots:
            for screenshot in self.screenshots:
                screenshot_path = os.path.join(self.screenshot_directory, screenshot)
                html.append(f"<div class='screenshot'><img src='{screenshot_path}' alt='{screenshot}' style='max-width:100%;'/><br>{screenshot}</div>")
        else:
            html.append("<p>No screenshots found.</p>")

        html.append("</body></html>")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(html))

        print(f"Report generated: {output_file}")
