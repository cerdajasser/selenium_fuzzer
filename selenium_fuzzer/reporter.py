import os
import re
import datetime
from typing import List, Dict

class ReportGenerator:
    """
    The ReportGenerator parses logs and compiles a summary of what was fuzzed, what dropdowns were checked,
    and what errors occurred. It can also include screenshots taken during the fuzzing process.
    """

    def __init__(self, log_directory: str = "log", screenshot_directory: str = "screenshots"):
        self.log_directory = log_directory
        self.screenshot_directory = screenshot_directory
        self.fuzzed_fields_details = []    # List of tuples: (field_name, payload, iframe, url)
        self.fuzzed_dropdowns_details = [] # List of tuples: (dropdown_name, option, url)
        self.errors = []                   # List of tuples: (timestamp, error_level, error_message, url)
        self.screenshots = []

    def parse_logs(self):
        """
        Parse all log files in the log directory to extract information.
        Looks for patterns related to fields fuzzed, dropdowns interacted with, and errors encountered.
        """
        if not os.path.exists(self.log_directory):
            print(f"Log directory {self.log_directory} not found.")
            return

        log_files = [f for f in os.listdir(self.log_directory) if f.endswith(".log")]

        # Regex patterns to identify relevant lines
        # Field contexts and payload insertions
        field_context_pattern = re.compile(r"Fuzzing field '(.*?)' in iframe (.*?) at URL: (.*?)$")
        field_fuzz_pattern = re.compile(r"Successfully entered payload '(.*?)' into field '(.*?)'\.")
        
        # Dropdown contexts and selections
        dropdown_fuzz_pattern = re.compile(r"Fuzzing dropdown '(.*?)' at URL: (.*?)$")
        dropdown_option_pattern = re.compile(r"Selected option '(.*?)' from dropdown '(.*?)'")

        # Errors with timestamps and URL context
        error_pattern = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),.*(ERROR|CRITICAL).*?: (.*?) at URL: (.*?)$")

        current_field_context = {}
        current_dropdown_context = {}

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

                    # When a payload is inserted successfully into a field
                    ff_match = field_fuzz_pattern.search(line)
                    if ff_match and current_field_context:
                        payload = ff_match.group(1)
                        field_logged_name = ff_match.group(2)
                        # Use the current_field_context for iframe and url
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
                        dropdown_logged_name = do_match.group(2)
                        # Use current dropdown context for url
                        self.fuzzed_dropdowns_details.append((
                            current_dropdown_context['dropdown_name'],
                            option,
                            current_dropdown_context['url']
                        ))

                    # Capture errors
                    e_match = error_pattern.search(line)
                    if e_match:
                        timestamp = e_match.group(1)
                        error_level = e_match.group(2)
                        error_message = e_match.group(3)
                        url = e_match.group(4)
                        self.errors.append((timestamp, error_level, error_message, url))

    def find_screenshots(self):
        """
        Identify screenshot files in the screenshot directory.
        """
        if os.path.exists(self.screenshot_directory):
            self.screenshots = [f for f in os.listdir(self.screenshot_directory) if f.lower().endswith((".png", ".jpg", ".jpeg"))]

    def generate_report(self, output_file: str = "report.html"):
        """
        Generate an HTML report summarizing the fuzzing session with improved styling and easier navigation.
        """
        html = [
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
            "table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }",
            "th, td { border: 1px solid #ccc; padding: 10px; text-align: left; font-size: 0.95em; }",
            "th { background: #f0f0f0; font-weight: bold; }",
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
        html.append("<div class='section' id='fields'>")
        html.append("<h2>💻 Fuzzed Input Fields</h2>")
        if self.fuzzed_fields_details:
            html.append("<table>")
            html.append("<tr><th>Field Name</th><th>Payload</th><th>Iframe</th><th>URL</th></tr>")
            for field_name, payload, iframe, url in self.fuzzed_fields_details:
                html.append(f"<tr><td>{field_name}</td><td>{payload}</td><td>{iframe}</td><td><a href='{url}' target='_blank'>{url}</a></td></tr>")
            html.append("</table>")
        else:
            html.append("<p class='no-data'>No input fields were fuzzed.</p>")
        html.append("</div>")

        # Dropdowns Checked
        html.append("<div class='section' id='dropdowns'>")
        html.append("<h2>🔽 Checked Dropdowns</h2>")
        if self.fuzzed_dropdowns_details:
            html.append("<table>")
            html.append("<tr><th>Dropdown Name</th><th>Option Selected</th><th>URL</th></tr>")
            for dropdown_name, option, url in self.fuzzed_dropdowns_details:
                html.append(f"<tr><td>{dropdown_name}</td><td>{option}</td><td><a href='{url}' target='_blank'>{url}</a></td></tr>")
            html.append("</table>")
        else:
            html.append("<p class='no-data'>No dropdown interactions were recorded.</p>")
        html.append("</div>")

        # Major Errors
        html.append("<div class='section' id='errors'>")
        html.append("<h2>❌ Major Errors</h2>")
        if self.errors:
            html.append("<table>")
            html.append("<tr><th>Timestamp</th><th>Level</th><th>Message</th><th>URL</th></tr>")
            for timestamp, level, message, url in self.errors:
                html.append(f"<tr><td>{timestamp}</td><td class='error'>{level}</td><td>{message}</td><td><a href='{url}' target='_blank'>{url}</a></td></tr>")
            html.append("</table>")
        else:
            html.append("<p class='no-data'>No major errors recorded.</p>")
        html.append("</div>")

        # Screenshots
        html.append("<div class='section' id='screenshots'>")
        html.append("<h2>📷 Screenshots</h2>")
        if self.screenshots:
            for screenshot in self.screenshots:
                screenshot_path = os.path.join(self.screenshot_directory, screenshot)
                html.append(f"<div class='screenshot'><img src='{screenshot_path}' alt='{screenshot}' style='max-width:100%;'/><br><small>{screenshot}</small></div>")
        else:
            html.append("<p class='no-data'>No screenshots found.</p>")
        html.append("</div>")

        html.append("</div>")  # .container
        html.append("</body></html>")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(html))

        print(f"Report generated: {output_file}")
