import unittest
from unittest.mock import patch, MagicMock
from client import AlpacaClient
import datetime

class TestAlpacaClient(unittest.TestCase):

    @patch('client.StockHistoricalDataClient')
    @patch('client.TradingClient')
    @patch('client.OptionHistoricalDataClient')
    @patch('os.getenv')
    def test_init(self, mock_getenv, mock_option_client, mock_trading_client, mock_stock_client):
        # Arrange
        mock_getenv.side_effect = ['test_key', 'test_secret']

        # Act
        client = AlpacaClient()

        # Assert
        mock_getenv.assert_any_call("APCA_API_KEY_ID")
        mock_getenv.assert_any_call("APCA_API_SECRET_KEY")
        mock_trading_client.assert_called_with('test_key', 'test_secret', paper=True)
        mock_option_client.assert_called_with('test_key', 'test_secret')
        mock_stock_client.assert_called_with('test_key', 'test_secret')
        self.assertIsNotNone(client)

    @patch('client.StockHistoricalDataClient')
    @patch('client.TradingClient')
    @patch('client.OptionHistoricalDataClient')
    @patch('os.getenv')
    def test_get_latest_stock_price(self, mock_getenv, mock_option_client, mock_trading_client, mock_stock_client):
        # Arrange
        mock_getenv.side_effect = ['test_key', 'test_secret']
        client = AlpacaClient()

        mock_quote = MagicMock()
        mock_quote.ask_price = 150.0
        client.stock_data_client.get_stock_latest_quote.return_value = {'AAPL': mock_quote}

        # Act
        price = client.get_latest_stock_price('AAPL')

        # Assert
        self.assertEqual(price, 150.0)
        client.stock_data_client.get_stock_latest_quote.assert_called_once()

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
    @patch('client.datetime')
    def test_find_next_friday_expiration(self, mock_datetime, mock_getenv):
        # Arrange
        mock_getenv.side_effect = ['test_key', 'test_secret']
        client = AlpacaClient()

        # we need to make sure timedelta is the real timedelta
        mock_datetime.timedelta = datetime.timedelta

        # Test case 1: Today is Monday
        mock_datetime.date.today.return_value = datetime.date(2025, 8, 25) # A Monday
        expected_friday = datetime.date(2025, 8, 29)
        self.assertEqual(client.find_next_friday_expiration(), expected_friday)

        # Test case 2: Today is Friday
        mock_datetime.date.today.return_value = datetime.date(2025, 8, 29) # A Friday
        expected_friday = datetime.date(2025, 9, 5) # Next Friday
        self.assertEqual(client.find_next_friday_expiration(), expected_friday)

        # Test case 3: Today is Saturday
        mock_datetime.date.today.return_value = datetime.date(2025, 8, 30) # A Saturday
        expected_friday = datetime.date(2025, 9, 5)
        self.assertEqual(client.find_next_friday_expiration(), expected_friday)

if __name__ == '__main__':
    unittest.main()
