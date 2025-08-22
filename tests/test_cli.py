import unittest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from cli import main, parse_option_symbol
import datetime

class TestCli(unittest.TestCase):

    def test_parse_option_symbol(self):
        # Arrange
        symbol = "AAPL251231C00150000"
        underlying = "AAPL"

        # Act
        parsed = parse_option_symbol(symbol, underlying)

        # Assert
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed['symbol'], symbol)
        self.assertEqual(parsed['expiration_date'], datetime.date(2025, 12, 31))
        self.assertEqual(parsed['strike_price'], 150.0)
        self.assertEqual(parsed['type'], 'call')

    @patch('cli.AlpacaClient')
    def test_trade_command(self, mock_alpaca_client):
        # Arrange
        mock_client_instance = mock_alpaca_client.return_value
        mock_client_instance.get_latest_stock_price.return_value = 150.0

        mock_snapshot = MagicMock()

        mock_client_instance.get_option_chain.return_value = {
            'AAPL251231C00150000': mock_snapshot,
            'AAPL251231P00150000': mock_snapshot,
        }
        mock_client_instance.find_next_friday_expiration.return_value = datetime.date(2025, 12, 31)
        mock_client_instance.find_nearest_strike.return_value = 150.0

        mock_quote = MagicMock()
        mock_quote.bid_price = 1.0
        mock_quote.ask_price = 1.1
        mock_client_instance.get_option_quote.return_value = {
            'AAPL251231C00150000': mock_quote,
            'AAPL251231P00150000': mock_quote
        }

        mock_order = MagicMock()
        mock_order.id = 'test_order_id'
        mock_order.status = 'filled'
        mock_client_instance.place_order.return_value = mock_order
        mock_client_instance.get_order_by_id.return_value = mock_order

        runner = CliRunner()

        # Act
        result = runner.invoke(main, ['trade', 'AAPL'], input='buy\ncall\n1.0\n1.0\n')

        # Assert
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Current price of AAPL: $150.00", result.output)
        self.assertIn("Using expiration date: 2025-12-31", result.output)
        self.assertIn("Using nearest strike price: $150.00", result.output)

    @patch('cli.AlpacaClient')
    def test_orders_list_command(self, mock_alpaca_client):
        # Arrange
        mock_client_instance = mock_alpaca_client.return_value
        mock_order = MagicMock()
        mock_order.id = 'order1'
        mock_order.symbol = 'AAPL'
        mock_order.side = 'buy'
        mock_order.qty = '1'
        mock_order.status = 'open'
        mock_client_instance.get_orders.return_value = [mock_order]
        runner = CliRunner()

        # Act
        result = runner.invoke(main, ['orders', 'list'])

        # Assert
        self.assertEqual(result.exit_code, 0)
        self.assertIn("ID: order1, Symbol: AAPL, Side: buy, Qty: 1, Status: open", result.output)

    @patch('cli.AlpacaClient')
    def test_positions_list_command(self, mock_alpaca_client):
        # Arrange
        mock_client_instance = mock_alpaca_client.return_value
        mock_position = MagicMock()
        mock_position.symbol = 'AAPL'
        mock_position.qty = '1'
        mock_position.side = 'long'
        mock_position.market_value = '150.0'
        mock_client_instance.get_positions.return_value = [mock_position]
        runner = CliRunner()

        # Act
        result = runner.invoke(main, ['positions', 'list'])

        # Assert
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Symbol: AAPL, Qty: 1, Side: long, Market Value: 150.0", result.output)


if __name__ == '__main__':
    unittest.main()
