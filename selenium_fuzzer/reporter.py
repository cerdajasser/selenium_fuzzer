import os
import re
import datetime
from typing import List, Tuple
import html

class ReportGenerator:
    def __init__(self, log_directory: str = "log", artifact_directory: str = "artifacts", run_start_time: datetime.datetime = None):
        self.log_directory = log_directory
        self.artifact_directory = artifact_directory
        self.run_start_time = run_start_time

        # Data structures for aggregated results
        self.fuzzed_fields_details: List[Tuple[str, str, str]] = []    # (field_name, payload, url)
        self.fuzzed_dropdowns_details: List[Tuple[str, str, str]] = [] # (dropdown_name, option, url)
        self.errors: List[Tuple[str, str, str, str]] = []             # (timestamp, level, message, url)

        self.js_errors: List[Tuple[str, str, str]] = []    # (timestamp, message, url)
        self.js_warnings: List[Tuple[str, str, str]] = []  # (timestamp, message, url)
        self.visited_urls: List[str] = []                  # URLs accessed by Selenium
        self.fuzzer_actions: List[str] = []                # Actions performed by Selenium fuzzer

        # Artifact collections
        self.screenshots: List[str] = []
        self.console_logs: List[str] = []    # List of console log files
        self.dom_snapshots: List[str] = []   # List of DOM snapshot files
        self.artifact_screenshots: List[str] = [] # Additional screenshots stored in artifacts directory

    def parse_logs(self):
        if not os.path.exists(self.log_directory):
            print(f"Log directory '{self.log_directory}' not found.")
            return

        # Match logs starting with js_change_detector_, fuzzing_log_, or selenium_fuzzer_ and ending in .log
        log_files = [
            f for f in os.listdir(self.log_directory)
            if f.endswith(".log") and (
                f.startswith("fuzzing_log_") or
                f.startswith("js_change_detector_") or
                f.startswith("selenium_fuzzer_")
            )
        ]

        if not log_files:
            print("No matching log files found in the log directory.")
            return

        # Sort logs by modification time (oldest first)
        log_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.log_directory, x)))

        # If run_start_time is provided, filter logs modified after run_start_time
        if self.run_start_time:
            run_start_timestamp = self.run_start_time.timestamp()
            log_files = [
                f for f in log_files
                if os.path.getmtime(os.path.join(self.log_directory, f)) >= run_start_timestamp
            ]

        if not log_files:
            print("No new log files found for this run (no logs modified after run_start_time).")
            return

        # Updated Regex patterns for fuzzing logs
        field_fuzz_pattern = re.compile(
            r".*Payload '(.*?)' successfully entered into field '(.*?)'\. URL: (.*?)$"
        )
        dropdown_option_pattern = re.compile(
            r".*Selected option '(.*?)' from dropdown '(.*?)' at URL: (.*?)$"
        )
        fuzz_error_pattern = re.compile(
            r"\[(.*?)\] .* - (ERROR|CRITICAL) - (.*?)(?:\. URL: (.*))?$"
        )

        # JS logs patterns
        js_error_pattern = re.compile(
            r".*\[(.*?)\] .* - ERROR - JavaScript Error from DevTools: (.*?) - (.*)"
        )
        js_warning_pattern = re.compile(
            r".*\[(.*?)\] .* - WARNING - JavaScript Warning from DevTools: (.*?) (.*)"
        )

        # Selenium fuzzer logs patterns
        accessed_url_pattern = re.compile(r".*Accessing the target URL:\s*(.*?)$")
        action_pattern = re.compile(r".*=== (.*?) ===")

        # Parse each selected log file
        for log_file in log_files:
            log_path = os.path.join(self.log_directory, log_file)
            print(f"Parsing log file: {log_file}")
            with open(log_path, 'r', encoding='utf-8') as lf:
                for line in lf:
                    if log_file.startswith("fuzzing_log_"):
                        # Fields
                        ff_match = field_fuzz_pattern.search(line)
                        if ff_match:
                            payload = ff_match.group(1)
                            field_name = ff_match.group(2)
                            url = ff_match.group(3)
                            self.fuzzed_fields_details.append((
                                html.escape(field_name),
                                html.escape(payload),
                                html.escape(url)
                            ))

                        # Dropdowns
                        do_match = dropdown_option_pattern.search(line)
                        if do_match:
                            option = do_match.group(1)
                            dropdown_name = do_match.group(2)
                            url = do_match.group(3)
                            self.fuzzed_dropdowns_details.append((
                                html.escape(dropdown_name),
                                html.escape(option),
                                html.escape(url)
                            ))

                        # Errors
                        fe_match = fuzz_error_pattern.search(line)
                        if fe_match:
                            timestamp = fe_match.group(1)
                            error_level = fe_match.group(2)
                            error_message = fe_match.group(3)
                            url = fe_match.group(4) if fe_match.group(4) else "N/A"
                            self.errors.append((
                                html.escape(timestamp),
                                html.escape(error_level),
                                html.escape(error_message),
                                html.escape(url)
                            ))

                    elif log_file.startswith("js_change_detector_"):
                        # JS Errors
                        je_match = js_error_pattern.search(line)
                        if je_match:
                            timestamp = je_match.group(1)
                            url = je_match.group(2)
                            message = je_match.group(3)
                            self.js_errors.append((
                                html.escape(timestamp),
                                html.escape(message),
                                html.escape(url)
                            ))

                        # JS Warnings
                        jw_match = js_warning_pattern.search(line)
                        if jw_match:
                            timestamp = jw_match.group(1)
                            url = jw_match.group(2)
                            message = jw_match.group(3)
                            self.js_warnings.append((
                                html.escape(timestamp),
                                html.escape(message),
                                html.escape(url)
                            ))

                    elif log_file.startswith("selenium_fuzzer_"):
                        # Accessed URLs
                        au_match = accessed_url_pattern.search(line)
                        if au_match:
                            accessed_url = au_match.group(1)
                            self.visited_urls.append(html.escape(accessed_url))

                        # Actions
                        act_match = action_pattern.search(line)
                        if act_match:
                            action_desc = act_match.group(1)
                            self.fuzzer_actions.append(html.escape(action_desc))

    def find_artifacts(self, artifact_directory: str):
        # Screenshots
        if os.path.exists(artifact_directory):
            for f in os.listdir(artifact_directory):
                fp = os.path.join(artifact_directory, f)
                if os.path.isfile(fp):
                    if f.lower().endswith((".png", ".jpg", ".jpeg")):
                        self.screenshots.append(f)
                    elif f.lower().endswith(".log"):
                        self.console_logs.append(f)
                    elif f.lower().endswith(".html"):
                        self.dom_snapshots.append(f)
                    elif f.lower().endswith((".png", ".jpg", ".jpeg")):
                        self.artifact_screenshots.append(f)

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
            "<a href='#jserrors'>🛠️ JS Errors</a>",
            "<a href='#jswarnings'>⚠️ JS Warnings</a>",
            "<a href='#fuzzeractions'>🎬 Fuzzer Actions</a>",
            "<a href='#screenshots'>📷 Screenshots</a>",
            "<a href='#artifacts'>🗂️ Artifacts</a>",
            "</nav>",
            "<div class='container'>"
        ]

        # Fields Fuzzed
        html_content.append("<div class='section' id='fields'>")
        html_content.append("<h2>💻 Fuzzed Input Fields (Aggregated)</h2>")
        if self.fuzzed_fields_details:
            html_content.append("<table>")
            html_content.append("<tr><th>Field Name</th><th>Payload</th><th>URL</th></tr>")
            for field_name, payload, url in self.fuzzed_fields_details:
                html_content.append(f"<tr><td>{field_name}</td><td>{payload}</td><td><a href='{url}' target='_blank'>{url}</a></td></tr>")
            html_content.append("</table>")
        else:
            html_content.append("<p class='no-data'>No input fields were fuzzed across all logs.</p>")
        html_content.append("</div>")

        # Dropdowns Checked
        html_content.append("<div class='section' id='dropdowns'>")
        html_content.append("<h2>🔽 Checked Dropdowns (Aggregated)</h2>")
        if self.fuzzed_dropdowns_details:
            html_content.append("<table>")
            html_content.append("<tr><th>Dropdown Name</th><th>Option Selected</th><th>URL</th></tr>")
            for dropdown_name, option, url in self.fuzzed_dropdowns_details:
                html_content.append(f"<tr><td>{dropdown_name}</td><td>{option}</td><td><a href='{url}' target='_blank'>{url}</a></td></tr>")
            html_content.append("</table>")
        else:
            html_content.append("<p class='no-data'>No dropdown interactions recorded across all logs.</p>")
        html_content.append("</div>")

        # Major Errors
        html_content.append("<div class='section' id='errors'>")
        html_content.append("<h2>❌ Major Errors (Aggregated)</h2>")
        if self.errors:
            html_content.append("<table>")
            html_content.append("<tr><th>Timestamp</th><th>Level</th><th>Message</th><th>URL</th></tr>")
            for timestamp, level, message, url in self.errors:
                html_content.append(f"<tr><td>{timestamp}</td><td class='error'>{level}</td><td>{message}</td><td><a href='{url}' target='_blank'>{url}</a></td></tr>")
            html_content.append("</table>")
        else:
            html_content.append("<p class='no-data'>No major errors recorded across all logs.</p>")
        html_content.append("</div>")

        # JS Errors
        html_content.append("<div class='section' id='jserrors'>")
        html_content.append("<h2>🛠️ JS Errors from DevTools</h2>")
        if self.js_errors:
            html_content.append("<table>")
            html_content.append("<tr><th>Timestamp</th><th>URL</th><th>Message</th></tr>")
            for timestamp, message, url in self.js_errors:
                html_content.append(f"<tr><td>{timestamp}</td><td><a href='{url}' target='_blank'>{url}</a></td><td>{message}</td></tr>")
            html_content.append("</table>")
        else:
            html_content.append("<p class='no-data'>No JS errors found.</p>")
        html_content.append("</div>")

        # JS Warnings
        html_content.append("<div class='section' id='jswarnings'>")
        html_content.append("<h2>⚠️ JS Warnings from DevTools</h2>")
        if self.js_warnings:
            html_content.append("<table>")
            html_content.append("<tr><th>Timestamp</th><th>URL</th><th>Message</th></tr>")
            for timestamp, message, url in self.js_warnings:
                html_content.append(f"<tr><td>{timestamp}</td><td><a href='{url}' target='_blank'>{url}</a></td><td>{message}</td></tr>")
            html_content.append("</table>")
        else:
            html_content.append("<p class='no-data'>No JS warnings found.</p>")
        html_content.append("</div>")

        # Selenium Fuzzer Actions & Visited URLs
        html_content.append("<div class='section' id='fuzzeractions'>")
        html_content.append("<h2>🎬 Selenium Fuzzer Actions & Visited URLs</h2>")

        # Actions
        html_content.append("<h3>Actions</h3>")
        if self.fuzzer_actions:
            html_content.append("<ul>")
            for action in self.fuzzer_actions:
                html_content.append(f"<li>{action}</li>")
            html_content.append("</ul>")
        else:
            html_content.append("<p class='no-data'>No recorded actions from Selenium Fuzzer logs.</p>")

        # Visited URLs
        html_content.append("<h3>Visited URLs</h3>")
        if self.visited_urls:
            html_content.append("<ul>")
            for vurl in self.visited_urls:
                html_content.append(f"<li><a href='{vurl}' target='_blank'>{vurl}</a></li>")
            html_content.append("</ul>")
        else:
            html_content.append("<p class='no-data'>No visited URLs recorded.</p>")
        html_content.append("</div>")

        # Screenshots
        html_content.append("<div class='section' id='screenshots'>")
        html_content.append("<h2>📷 Screenshots</h2>")
        if self.screenshots:
            for screenshot in self.screenshots:
                screenshot_path = os.path.join(self.artifact_directory, screenshot)
                html_content.append(f"<div class='screenshot'><img src='{html.escape(screenshot_path)}' alt='{html.escape(screenshot)}' style='max-width:100%;'/><br><small>{html.escape(screenshot)}</small></div>")
        else:
            html_content.append("<p class='no-data'>No screenshots found.</p>")
        html_content.append("</div>")

        # Artifacts Section
        html_content.append("<div class='section' id='artifacts'>")
        html_content.append("<h2>🗂️ Additional Artifacts</h2>")

        if not (self.console_logs or self.dom_snapshots or self.artifact_screenshots):
            html_content.append("<p class='no-data'>No additional artifacts found.</p>")
        else:
            # Console logs
            if self.console_logs:
                html_content.append("<h3>Console Logs</h3>")
                html_content.append("<ul>")
                for c_log in self.console_logs:
                    artifact_path = os.path.join(self.artifact_directory, c_log)
                    html_content.append(f"<li><a href='{artifact_path}' target='_blank'>{c_log}</a></li>")
                html_content.append("</ul>")

            # DOM Snapshots
            if self.dom_snapshots:
                html_content.append("<h3>DOM Snapshots</h3>")
                html_content.append("<ul>")
                for dom_file in self.dom_snapshots:
                    artifact_path = os.path.join(self.artifact_directory, dom_file)
                    html_content.append(f"<li><a href='{artifact_path}' target='_blank'>{dom_file}</a></li>")
                html_content.append("</ul>")

            # Additional Screenshots
            if self.artifact_screenshots:
                html_content.append("<h3>Artifact Screenshots</h3>")
                for ss in self.artifact_screenshots:
                    artifact_path = os.path.join(self.artifact_directory, ss)
                    html_content.append(f"<div class='screenshot'><img src='{html.escape(artifact_path)}' alt='{html.escape(ss)}' style='max-width:100%;'/><br><small>{html.escape(ss)}</small></div>")

        html_content.append("</div>")  # artifacts section

        html_content.append("</div>")  # .container
        html_content.append("</body></html>")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(html_content))

        print(f"Report generated: {output_file}")
