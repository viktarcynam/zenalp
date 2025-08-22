import unittest
from unittest.mock import patch, MagicMock
from client import AlpacaClient
import datetime

class TestAlpacaClient(unittest.TestCase):

    @patch('client.TradingClient')
    @patch('client.OptionHistoricalDataClient')
    @patch('os.getenv')
    def test_init(self, mock_getenv, mock_option_client, mock_trading_client):
        # Arrange
        mock_getenv.side_effect = ['test_key', 'test_secret']

        # Act
        client = AlpacaClient()

        # Assert
        mock_getenv.assert_any_call("APCA_API_KEY_ID")
        mock_getenv.assert_any_call("APCA_API_SECRET_KEY")
        mock_trading_client.assert_called_with('test_key', 'test_secret', paper=True)
        mock_option_client.assert_called_with('test_key', 'test_secret')
        self.assertIsNotNone(client)

    @patch('client.TradingClient')
    @patch('client.OptionHistoricalDataClient')
    @patch('os.getenv')
    def test_get_latest_stock_price(self, mock_getenv, mock_option_client, mock_trading_client):
        # Arrange
        mock_getenv.side_effect = ['test_key', 'test_secret']
        client = AlpacaClient()

        mock_quote = MagicMock()
        mock_quote.ask_price = 150.0
        client.trading_client.get_stock_latest_quote.return_value = {'AAPL': mock_quote}

        # Act
        price = client.get_latest_stock_price('AAPL')

        # Assert
        self.assertEqual(price, 150.0)
        client.trading_client.get_stock_latest_quote.assert_called_once()

    @patch('os.getenv')
    def test_find_nearest_strike(self, mock_getenv):
        # Arrange
        mock_getenv.side_effect = ['test_key', 'test_secret']
        client = AlpacaClient()
        strikes = [100.0, 110.0, 120.0, 130.0, 140.0]

        # Act & Assert
        self.assertEqual(client.find_nearest_strike(123.0, strikes), 120.0)
        self.assertEqual(client.find_nearest_strike(128.0, strikes), 130.0)
        self.assertEqual(client.find_nearest_strike(100.0, strikes), 100.0)

    @patch('os.getenv')
    def test_find_next_friday_expiration(self, mock_getenv):
        # Arrange
        mock_getenv.side_effect = ['test_key', 'test_secret']
        client = AlpacaClient()

        # Act & Assert
        today = datetime.date.today()
        days_until_friday = (4 - today.weekday() + 7) % 7
        expected_friday = today + datetime.timedelta(days=days_until_friday)
        self.assertEqual(client.find_next_friday_expiration(), expected_friday)

if __name__ == '__main__':
    unittest.main()
