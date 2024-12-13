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

    def parse_logs(self):
        print("Parsing logs...")
        if not os.path.exists(self.log_directory):
            print(f"Log directory '{self.log_directory}' not found.")
            return

        # Sort log files by modification time and pick the latest one
        log_files = sorted(
            [os.path.join(self.log_directory, f) for f in os.listdir(self.log_directory) if f.endswith(".log")],
            key=os.path.getmtime,
            reverse=True
        )

        if not log_files:
            print("No log files found.")
            return

        latest_log_file = log_files[0]
        print(f"Processing latest log file: {latest_log_file}")

        with open(latest_log_file, "r", encoding="utf-8") as file:
            for line in file:
                print(f"Log line: {line.strip()}")
                if "Payload" in line and "successfully entered into field" in line:
                    parts = line.split("'")
                    payload = html.escape(parts[1])
                    field_name = html.escape(parts[3])
                    url = html.escape(parts[-1].strip())
                    self.fuzzed_fields_details.append((field_name, payload, url))

    def generate_report(self, output_file: str = "report.html"):
        fields_count = len(self.fuzzed_fields_details)
        dropdowns_count = len(self.fuzzed_dropdowns_details)
        errors_count = len(self.errors)

        if fields_count == 0 and dropdowns_count == 0 and errors_count == 0:
            print("No data available to generate a report.")
            return

        html_content = [
            "<!DOCTYPE html>",
            "<html lang='en'>",
            "<head>",
            "<meta charset='UTF-8'>",
            "<meta name='viewport' content='width=device-width, initial-scale=1.0'>",
            "<title>Fuzzer Report</title>",
            "<script src='https://cdn.jsdelivr.net/npm/chart.js'></script>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin:0; padding:0; background: #f5f5f5; }",
            "header { background: #333; color: #fff; padding: 20px; }",
            "header h1 { margin: 0; font-size: 1.5em; }",
            ".container { max-width: 1200px; margin: 20px auto; background: #fff; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }",
            "canvas { max-width: 100%; height: auto; margin: 20px auto; }",
            "table { width: 100%; border-collapse: collapse; margin-top: 20px; }",
            "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; font-size: 14px; }",
            "th { background-color: #f2f2f2; font-weight: bold; }",
            "tr:nth-child(even) { background-color: #f9f9f9; }",
            "tr:hover { background-color: #f1f1f1; }",
            "</style>",
            "</head>",
            "<body>",
            "<header>",
            f"<h1>Fuzzer Report - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</h1>",
            "</header>",
            "<div class='container'>",
            "<h2>Summary</h2>",
            "<canvas id='summaryChart'></canvas>",
            "<script>",
            "const ctx = document.getElementById('summaryChart').getContext('2d');",
            "const summaryChart = new Chart(ctx, {",
            "    type: 'pie',",
            "    data: {",
            "        labels: ['Fuzzed Fields', 'Fuzzed Dropdowns', 'Errors'],",
            "        datasets: [{",
            f"            data: [{fields_count}, {dropdowns_count}, {errors_count}],",
            "            backgroundColor: ['#4CAF50', '#2196F3', '#F44336'],",
            "        }]",
            "    },",
            "    options: { responsive: true, plugins: { legend: { position: 'bottom' } } }",
            "});",
            "</script>",
            "<h2>Details</h2>",
            "<table>",
            "<thead>",
            "<tr>",
            "<th>Category</th>",
            "<th>Details</th>",
            "</tr>",
            "</thead>",
            "<tbody>",
        ]

        for field_name, payload, url in self.fuzzed_fields_details:
            html_content.append(f"<tr><td>Fuzzed Field</td><td>{field_name}: {payload} (<a href='{url}' target='_blank'>{url}</a>)</td></tr>")

        html_content.extend([
            "</tbody>",
            "</table>",
            "</div>",
            "</body>",
            "</html>",
        ])

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(html_content))

        print(f"Report generated: {output_file}")
