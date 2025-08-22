import os
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.data.historical.option import OptionHistoricalDataClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, ReplaceOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.requests import StockLatestQuoteRequest, OptionChainRequest, OptionLatestQuoteRequest
import datetime

class AlpacaClient:
    """
    A client for interacting with the Alpaca API.
    """

    def __init__(self):
        """
        Initializes the AlpacaClient.
        """
        load_dotenv()
        self.api_key = os.getenv("APCA_API_KEY_ID")
        self.secret_key = os.getenv("APCA_API_SECRET_KEY")

        if not self.api_key or not self.secret_key:
            raise ValueError("API keys not found. Please set APCA_API_KEY_ID and APCA_API_SECRET_KEY environment variables.")

        self.trading_client = TradingClient(self.api_key, self.secret_key, paper=True)
        self.option_data_client = OptionHistoricalDataClient(self.api_key, self.secret_key)

    def get_latest_stock_price(self, symbol: str) -> float:
        """
        Gets the latest price of an underlying asset.
        """
        request_params = StockLatestQuoteRequest(symbol_or_symbols=symbol)
        latest_quote = self.trading_client.get_stock_latest_quote(request_params)
        return latest_quote[symbol].ask_price

    def get_option_chain(self, symbol: str) -> dict:
        """
        Gets the option chain for a given symbol.
        """
        request_params = OptionChainRequest(underlying_symbol=symbol)
        option_chain = self.option_data_client.get_option_chain(request_params)
        return option_chain

    def find_nearest_strike(self, current_price: float, strikes: list[float]) -> float:
        """
        Finds the nearest strike price to the current price.
        """
        return min(strikes, key=lambda x: abs(x - current_price))

    def find_next_friday_expiration(self) -> datetime.date:
        """
        Finds the upcoming Friday expiration date.
        """
        today = datetime.date.today()
        days_until_friday = (4 - today.weekday() + 7) % 7
        next_friday = today + datetime.timedelta(days=days_until_friday)
        return next_friday

    def get_option_quote(self, symbol: str) -> dict:
        """
        Gets the latest quote for an option contract.
        """
        request_params = OptionLatestQuoteRequest(symbol_or_symbols=symbol)
        latest_quote = self.option_data_client.get_option_latest_quote(request_params)
        return latest_quote

    def place_order(self, symbol: str, qty: float, side: OrderSide, limit_price: float) -> dict:
        """
        Places a limit order.
        """
        order_data = LimitOrderRequest(
            symbol=symbol,
            qty=qty,
            side=side,
            time_in_force=TimeInForce.GTC,
            limit_price=limit_price
        )
        order = self.trading_client.submit_order(order_data)
        return order

    def get_orders(self):
        """
        Gets all orders.
        """
        return self.trading_client.get_orders()

    def get_order_by_id(self, order_id: str):
        """
        Gets an order by its ID.
        """
        return self.trading_client.get_order_by_id(order_id)

    def cancel_order(self, order_id: str):
        """
        Cancels an order.
        """
        return self.trading_client.cancel_order_by_id(order_id)

    def replace_order(self, order_id: str, new_limit_price: float):
        """
        Replaces an order.
        """
        replace_order_data = ReplaceOrderRequest(
            limit_price=new_limit_price
        )
        return self.trading_client.replace_order_by_id(order_id, replace_order_data)

    def get_positions(self):
        """
        Gets all positions.
        """
        return self.trading_client.get_all_positions()
