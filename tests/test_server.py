import unittest
from unittest.mock import patch, MagicMock
from server.server import AlpacaServer

class TestServer(unittest.TestCase):

    @patch('server.server.AlpacaService')
    def setUp(self, mock_alpaca_service):
        self.server = AlpacaServer()
        self.server.alpaca_service = mock_alpaca_service.return_value

    def test_process_ping_request(self):
        request = {'action': 'ping'}
        response = self.server._process_request(request)
        self.assertTrue(response['success'])
        self.assertEqual(response['message'], 'pong')

    def test_process_unknown_action(self):
        request = {'action': 'unknown_action'}
        response = self.server._process_request(request)
        self.assertFalse(response['success'])
        self.assertIn('Invalid action', response['error'])

    def test_process_get_latest_stock_price(self):
        request = {'action': 'get_latest_stock_price', 'symbol': 'AAPL'}
        self.server.alpaca_service.get_latest_stock_price.return_value = 150.0

        response = self.server._process_request(request)

        self.assertTrue(response['success'])
        self.assertEqual(response['data'], 150.0)
        self.server.alpaca_service.get_latest_stock_price.assert_called_with('AAPL')

if __name__ == '__main__':
    unittest.main()
