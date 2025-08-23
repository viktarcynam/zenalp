import unittest
import json
from common.json_parser import json_parser

class TestJsonParser(unittest.TestCase):

    def test_valid_ping_request(self):
        req = '{"action": "ping"}'
        result = json_parser.format_request(req)
        self.assertTrue(result['success'])
        self.assertEqual(result['request']['action'], 'ping')

    def test_missing_action(self):
        req = '{"payload": "test"}'
        result = json_parser.validate_request(json.loads(req))
        self.assertFalse(result['success'])
        self.assertIn('Missing required field: action', result['error'])

    def test_invalid_action(self):
        req = '{"action": "invalid_action"}'
        result = json_parser.validate_request(json.loads(req))
        self.assertFalse(result['success'])
        self.assertIn('Invalid action', result['error'])

    def test_missing_required_param(self):
        req = '{"action": "get_option_chain"}'
        result = json_parser.validate_request(json.loads(req))
        self.assertFalse(result['success'])
        self.assertIn('Missing required parameter', result['error'])

if __name__ == '__main__':
    unittest.main()
