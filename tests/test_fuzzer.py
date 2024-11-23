import unittest
from selenium_fuzzer.fuzzer import Fuzzer

class TestFuzzer(unittest.TestCase):
    def setUp(self):
        self.fuzzer = Fuzzer('http://example.com')  # Use a test URL or mock

    def test_detect_inputs(self):
        # This test would require a mock or a test page with mat-form-field elements
        inputs = self.fuzzer.detect_inputs()
        self.assertIsInstance(inputs, list)

    def tearDown(self):
        self.fuzzer.driver.quit()
