import unittest
from src.analyzer.iflow_parser import IFlowParser

class TestIFlowParser(unittest.TestCase):

    def setUp(self):
        self.parser = IFlowParser()

    def test_parse_iflw_file(self):
        # Test parsing a sample .iflw file
        result = self.parser.parse('tests/fixtures/sample.iflw')
        self.assertIsNotNone(result)
        self.assertIn('participants', result)
        self.assertIn('processes', result)

    def test_invalid_iflw_file(self):
        # Test parsing an invalid .iflw file
        with self.assertRaises(ValueError):
            self.parser.parse('tests/fixtures/invalid.iflw')

    def test_extract_participants(self):
        # Test extracting participants from a parsed iFlow
        parsed_data = self.parser.parse('tests/fixtures/sample.iflw')
        participants = self.parser.extract_participants(parsed_data)
        self.assertGreater(len(participants), 0)

    def test_extract_processes(self):
        # Test extracting processes from a parsed iFlow
        parsed_data = self.parser.parse('tests/fixtures/sample.iflw')
        processes = self.parser.extract_processes(parsed_data)
        self.assertGreater(len(processes), 0)

if __name__ == '__main__':
    unittest.main()