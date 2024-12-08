# tests/test_main.py

import unittest
from unittest.mock import patch, MagicMock, mock_open, call
from selenium.common.exceptions import WebDriverException
from datetime import datetime
from urllib.parse import urlparse
import os

from selenium_fuzzer.config import Config
from main import (
    setup_logger,
    capture_artifacts_on_error,
    initialize_fuzzer,
    generate_final_report
)


class TestSeleniumFuzzer(unittest.TestCase):

    @patch('main.urlparse')
    @patch('main.os.path.join')
    @patch('main.logging.getLogger')
    def test_setup_logger(self, mock_get_logger, mock_path_join, mock_urlparse):
        # Mock environment
        mock_urlparse.return_value = MagicMock(netloc="example.com")
        mock_path_join.return_value = "/path/to/logfile.log"
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        # Call setup_logger
        logger = setup_logger("http://example.com")

        # Validate calls
        mock_urlparse.assert_called_with("http://example.com")
        mock_path_join.assert_called()
        mock_logger.setLevel.assert_called_with(logging.DEBUG)
        mock_logger.addHandler.assert_called()
        self.assertEqual(logger, mock_logger)

    @patch("main.os.makedirs")
    @patch("main.logging.getLogger")
    @patch("main.capture_artifacts_on_error")
    def test_initialize_webdriver_failure(self, mock_capture_artifacts, mock_get_logger, mock_makedirs):
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        # Simulate WebDriverException
        with patch("main.create_driver") as mock_create_driver:
            mock_create_driver.side_effect = WebDriverException("Driver initialization failed")

            with self.assertRaises(WebDriverException):
                initialize_fuzzer(None, MagicMock(), mock_logger)

            mock_capture_artifacts.assert_called_once()
            mock_logger.error.assert_called()

    @patch("main.create_driver")
    @patch("main.capture_artifacts_on_error")
    def test_capture_artifacts_on_error(self, mock_capture_artifacts, mock_create_driver):
        mock_driver = MagicMock()
        mock_create_driver.return_value = mock_driver

        mock_driver.current_url = "http://example.com"
        mock_driver.get_log.return_value = [{"timestamp": 123, "level": "SEVERE", "message": "Error"}]

        capture_artifacts_on_error(mock_driver, "run1", "scenario1", "test_action", "test_element")

        mock_driver.save_screenshot.assert_called_once()
        mock_driver.get_log.assert_called_once_with("browser")

    @patch("main.Fuzzer")
    @patch("main.JavaScriptChangeDetector")
    @patch("main.generate_safe_payloads")
    @patch("builtins.input", return_value="0")
    def test_initialize_fuzzer_fuzz_fields(self, mock_input, mock_generate_payloads, mock_js_change_detector, mock_fuzzer_class):
        mock_driver = MagicMock()
        mock_logger = MagicMock()
        args = MagicMock()
        args.fuzz_fields = True
        args.check_dropdowns = False
        args.delay = 1

        mock_fuzzer_instance = MagicMock()
        mock_fuzzer_class.return_value = mock_fuzzer_instance
        mock_fuzzer_instance.detect_inputs.return_value = [
            (0, MagicMock(get_attribute=MagicMock(return_value="input1"))),
        ]

        initialize_fuzzer(mock_driver, args, mock_logger)

        mock_fuzzer_instance.detect_inputs.assert_called_once()
        mock_fuzzer_instance.fuzz_field.assert_called_once()

    @patch("main.ReportGenerator")
    @patch("main.os.makedirs")
    def test_generate_final_report(self, mock_makedirs, mock_report_generator):
        mock_report = MagicMock()
        mock_report_generator.return_value = mock_report

        args = MagicMock()
        args.url = "http://example.com"

        run_start_time = datetime.now()

        generate_final_report(args, run_start_time, logger=MagicMock())

        mock_makedirs.assert_called_once_with(Config.REPORTS_FOLDER, exist_ok=True)
        mock_report.parse_logs.assert_called_once()
        mock_report.find_artifacts.assert_called_once_with(Config.ARTIFACTS_FOLDER)
        mock_report.generate_report.assert_called_once()

    @patch("main.ReportGenerator")
    @patch("main.os.makedirs")
    def test_generate_final_report_no_logs(self, mock_makedirs, mock_report_generator):
        mock_report = MagicMock()
        mock_report_generator.return_value = mock_report

        args = MagicMock()
        args.url = "http://example.com"

        run_start_time = datetime.now()

        generate_final_report(args, run_start_time, logger=MagicMock())

        mock_makedirs.assert_called_once_with(Config.REPORTS_FOLDER, exist_ok=True)
        mock_report.parse_logs.assert_called_once()
        mock_report.find_artifacts.assert_called_once_with(Config.ARTIFACTS_FOLDER)
        mock_report.generate_report.assert_called_once()


if __name__ == "__main__":
    unittest.main()
