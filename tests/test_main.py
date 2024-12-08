# tests/test_main.py

import unittest
from unittest.mock import patch, MagicMock, mock_open, call
import os
import sys
from io import StringIO
from datetime import datetime
from urllib.parse import urlparse

# Import Config for access to ARTIFACTS_FOLDER
from selenium_fuzzer.config import Config

# Import the functions to be tested
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
    def test_setup_logger(self, mock_getLogger, mock_join, mock_urlparse):
        # Setup the mocks
        mock_urlparse.return_value = MagicMock(netloc='example.com')
        mock_join.return_value = '/path/to/logfile.log'
        mock_logger = MagicMock()
        mock_getLogger.return_value = mock_logger
        
        # Call setup_logger
        logger = setup_logger('http://example.com')
        
        # Assertions
        mock_urlparse.assert_called_with('http://example.com')
        mock_join.assert_called_with(Config.LOG_FOLDER, 'selenium_fuzzer_example_com_20241207_091726.log')  # The timestamp will vary
        mock_logger.setLevel.assert_called_with(logging.DEBUG)
        mock_logger.addHandler.assert_called()
        self.assertEqual(logger, mock_logger)
    
    @patch('main.os.makedirs')
    @patch('main.driver.save_screenshot')
    @patch('main.driver.get_log')
    @patch('builtins.open', new_callable=mock_open)
    def test_capture_artifacts_on_error_success(self, mock_file, mock_get_log, mock_save_screenshot, mock_makedirs):
        # Setup
        mock_driver = MagicMock()
        mock_driver.current_url = 'http://example.com'
        mock_get_log.return_value = [
            {'timestamp': '1234567890.123', 'level': 'SEVERE', 'message': 'JavaScript Error'}
        ]
        
        # Call the function
        capture_artifacts_on_error(mock_driver, 'run123', 'scenarioA', 'fuzzing', 'input_field_1')
        
        # Assertions
        mock_makedirs.assert_called_with(Config.ARTIFACTS_FOLDER, exist_ok=True)
        mock_driver.save_screenshot.assert_called_once_with('artifacts/error_screenshot_run123_20241207_091726.png')
        mock_driver.get_log.assert_called_once_with('browser')
        mock_file.assert_called_with('artifacts/console_logs_run123_20241207_091726.log', 'w', encoding='utf-8')
        handle = mock_file()
        handle.write.assert_any_call('Run ID: run123\nScenario: scenarioA\nLast Action: fuzzing\nLast Element: input_field_1\nCurrent URL: http://example.com\n\n')
        handle.write.assert_any_call('1234567890.123 SEVERE JavaScript Error\n')
        mock_file.assert_called_with('artifacts/dom_snapshot_run123_20241207_091726.html', 'w', encoding='utf-8')
        handle_dom = mock_file()
        handle_dom.write.assert_called()
    
    @patch('main.Fuzzer')
    @patch('main.JavaScriptChangeDetector')
    @patch('main.generate_safe_payloads')
    @patch('builtins.input', return_value='0,1')
    def test_initialize_fuzzer_fuzz_fields(self, mock_input, mock_generate_payloads, mock_js_detector, mock_fuzzer):
        # Setup
        mock_generate_payloads.return_value = ['payload1', 'payload2']
        mock_fuzzer_instance = MagicMock()
        mock_fuzzer.return_value = mock_fuzzer_instance
        mock_fuzzer_instance.detect_inputs.return_value = [
            (0, MagicMock(get_attribute=MagicMock(return_value='username'))),
            (1, MagicMock(get_attribute=MagicMock(return_value='password')))
        ]
        
        # Setup logger
        with patch('main.logging.getLogger') as mock_getLogger:
            mock_logger = MagicMock()
            mock_getLogger.return_value = mock_logger
            
            # Call the function
            driver = MagicMock()
            args = MagicMock()
            args.fuzz_fields = True
            args.check_dropdowns = False
            args.delay = 1
            args.run_id = 'run123'
            args.scenario = 'scenarioA'
            args.devtools = False
            args.track_state = False
            initialize_fuzzer(driver, args, mock_logger)
            
            # Assertions
            mock_fuzzer_instance.detect_inputs.assert_called_once_with()
            self.assertEqual(mock_fuzzer_instance.fuzz_field.call_count, 2)
            mock_logger.info.assert_any_call('Fuzzed field: username')
            mock_logger.info.assert_any_call('Fuzzed field: password')
    
    @patch('main.ReportGenerator')
    @patch('main.os.makedirs')
    def test_generate_final_report(self, mock_makedirs, mock_report_generator):
        # Setup
        mock_report = MagicMock()
        mock_report_generator.return_value = mock_report
        
        args = MagicMock()
        args.url = 'http://example.com'
        
        run_start_time = datetime.now()
        
        # Call the function
        generate_final_report(args, run_start_time, logger=MagicMock())
        
        # Assertions
        mock_makedirs.assert_called_with(Config.REPORTS_FOLDER, exist_ok=True)
        mock_report.parse_logs.assert_called_once()
        mock_report.find_artifacts.assert_called_once_with(Config.ARTIFACTS_FOLDER)
        mock_report.generate_report.assert_called_once()
        # Ensure report_path is correctly constructed
        parsed = urlparse('http://example.com')
        domain = parsed.netloc
        safe_domain = domain.replace(":", "_").replace(".", "_")
        # Since the timestamp varies, we check if the call was made with a path that starts correctly
        args, kwargs = mock_report.generate_report.call_args
        self.assertTrue(args[0].startswith(os.path.join(Config.REPORTS_FOLDER, f"fuzzer_report_{safe_domain}_")))
    
    @patch('main.Fuzzer')
    @patch('main.JavaScriptChangeDetector')
    @patch('main.generate_safe_payloads')
    @patch('builtins.input', return_value='invalid')  # Simulate invalid input
    def test_initialize_fuzzer_invalid_input(self, mock_input, mock_generate_payloads, mock_js_detector, mock_fuzzer):
        # Setup
        mock_generate_payloads.return_value = ['payload1']
        mock_fuzzer_instance = MagicMock()
        mock_fuzzer.return_value = mock_fuzzer_instance
        mock_fuzzer_instance.detect_inputs.return_value = [
            (0, MagicMock(get_attribute=MagicMock(return_value='email')))
        ]
        
        # Setup logger
        with patch('main.logging.getLogger') as mock_getLogger:
            mock_logger = MagicMock()
            mock_getLogger.return_value = mock_logger
            
            # Call the function
            driver = MagicMock()
            args = MagicMock()
            args.fuzz_fields = True
            args.check_dropdowns = False
            args.delay = 1
            args.run_id = 'run123'
            args.scenario = 'scenarioA'
            args.devtools = False
            args.track_state = False
            initialize_fuzzer(driver, args, mock_logger)
            
            # Assertions
            mock_fuzzer_instance.detect_inputs.assert_called_once_with()
            mock_fuzzer_instance.fuzz_field.assert_called_once()
            mock_logger.info.assert_any_call('Fuzzed field: email')
            # Since input is 'invalid', no indices are selected, so no additional fuzz_field calls
    
    @patch('main.create_driver')
    @patch('main.Fuzzer')
    @patch('main.JavaScriptChangeDetector')
    @patch('main.generate_safe_payloads')
    def test_initialize_webdriver_failure(self, mock_generate_payloads, mock_js_detector, mock_fuzzer, mock_create_driver):
        # Setup
        mock_create_driver.side_effect = WebDriverException("Failed to create driver")
        
        # Setup logger
        with patch('main.setup_logger') as mock_setup_logger:
            mock_logger = MagicMock()
            mock_setup_logger.return_value = mock_logger
            
            # Simulate args
            args = MagicMock()
            args.fuzz_fields = False
            args.check_dropdowns = False
            args.delay = 1
            args.run_id = 'run123'
            args.scenario = 'scenarioA'
            args.devtools = False
            args.track_state = False
            
            # Capture stdout
            with patch('sys.exit') as mock_sys_exit:
                initialize_fuzzer(None, args, mock_logger)
                
                # Assertions
                mock_logger.error.assert_called_with("\n!!! An Unexpected Error Occurred: Failed to create driver\n")
                mock_sys_exit.assert_not_called()  # Because exceptions are handled within initialize_fuzzer
    
    @patch('main.os.makedirs')
    @patch('main.driver.save_screenshot')
    @patch('main.driver.get_log')
    @patch('builtins.open', new_callable=mock_open)
    def test_capture_artifacts_on_error_no_console_logs(self, mock_file, mock_get_log, mock_save_screenshot, mock_makedirs):
        # Setup
        mock_driver = MagicMock()
        mock_driver.current_url = 'http://example.com'
        mock_driver.get_log.side_effect = Exception("No logs available")
        
        # Call the function
        capture_artifacts_on_error(mock_driver, 'run123', 'scenarioA', 'fuzzing', 'input_field_1')
        
        # Assertions
        mock_makedirs.assert_called_with(Config.ARTIFACTS_FOLDER, exist_ok=True)
        mock_driver.save_screenshot.assert_called_once_with('artifacts/error_screenshot_run123_20241207_091726.png')
        mock_driver.get_log.assert_called_once_with('browser')
        mock_file.assert_called_with('artifacts/console_logs_run123_20241207_091726.log', 'w', encoding='utf-8')
        handle = mock_file()
        handle.write.assert_called_with("No console logs available.\n")
        mock_file.assert_called_with('artifacts/dom_snapshot_run123_20241207_091726.html', 'w', encoding='utf-8')
        handle_dom = mock_file()
        handle_dom.write.assert_called()
    
    @patch('main.ReportGenerator')
    @patch('main.os.makedirs')
    def test_generate_final_report_no_artifacts(self, mock_makedirs, mock_report_generator):
        # Setup
        mock_report = MagicMock()
        mock_report_generator.return_value = mock_report
        
        args = MagicMock()
        args.url = 'http://example.com'
        
        run_start_time = datetime.now()
        
        # Call the function
        generate_final_report(args, run_start_time, logger=MagicMock())
        
        # Assertions
        mock_makedirs.assert_called_with(Config.REPORTS_FOLDER, exist_ok=True)
        mock_report.parse_logs.assert_called_once()
        mock_report.find_artifacts.assert_called_once_with(Config.ARTIFACTS_FOLDER)
        mock_report.generate_report.assert_called_once()
    
    def test_save_artifact_success(self):
        # Assuming save_artifact is a method in Fuzzer class
        # If it's a standalone function, adjust accordingly
        pass  # Implement if necessary
    
    def test_save_artifact_failure(self):
        # Similarly, implement tests for save_artifact failure scenarios
        pass  # Implement if necessary

    if __name__ == '__main__':
        unittest.main()
