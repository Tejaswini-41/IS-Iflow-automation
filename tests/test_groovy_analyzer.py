import unittest
from src.analyzer.groovy_analyzer import GroovyAnalyzer

class TestGroovyAnalyzer(unittest.TestCase):

    def setUp(self):
        self.analyzer = GroovyAnalyzer()

    def test_analyze_json_parsing(self):
        script_content = """
        import groovy.json.JsonSlurper
        def json = new JsonSlurper().parseText('{"key": "value"}')
        """
        result = self.analyzer.analyze(script_content)
        self.assertIn('has_json', result)
        self.assertTrue(result['has_json'])

    def test_analyze_property_setting(self):
        script_content = """
        setProperty('key', 'value')
        """
        result = self.analyzer.analyze(script_content)
        self.assertIn('operations', result)
        self.assertIn('setProperty', result['operations'])

    def test_analyze_header_setting(self):
        script_content = """
        setHeader('Content-Type', 'application/json')
        """
        result = self.analyzer.analyze(script_content)
        self.assertIn('operations', result)
        self.assertIn('setHeader', result['operations'])

    def test_analyze_body_modification(self):
        script_content = """
        setBody('{"message": "Hello World"}')
        """
        result = self.analyzer.analyze(script_content)
        self.assertIn('operations', result)
        self.assertIn('setBody', result['operations'])

    def test_analyze_data_transformation(self):
        script_content = """
        import groovy.json.JsonOutput
        def jsonOutput = JsonOutput.toJson(['key': 'value'])
        """
        result = self.analyzer.analyze(script_content)
        self.assertIn('has_transformation', result)
        self.assertTrue(result['has_transformation'])

    def test_analyze_empty_script(self):
        script_content = ""
        result = self.analyzer.analyze(script_content)
        self.assertEqual(result['summary'], 'Processes message data')

if __name__ == '__main__':
    unittest.main()