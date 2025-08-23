import os
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.data.historical.option import OptionHistoricalDataClient
from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, ReplaceOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.requests import StockLatestQuoteRequest, OptionChainRequest, OptionLatestQuoteRequest
import datetime
import logging

class AlpacaService:
    """
    A service for interacting with the Alpaca API.
    """

    def __init__(self):
        """
        Initializes the AlpacaService.
        """
        load_dotenv()
        self.api_key = os.getenv("APCA_API_KEY_ID")
        self.secret_key = os.getenv("APCA_API_SECRET_KEY")
        self.trading_client = None
        self.option_data_client = None
        self.stock_data_client = None

        if not self.api_key or not self.secret_key:
            raise ValueError("API keys not found. Please set APCA_API_KEY_ID and APCA_API_SECRET_KEY environment variables.")

        try:
            self.trading_client = TradingClient(self.api_key, self.secret_key, paper=True)
            self.option_data_client = OptionHistoricalDataClient(self.api_key, self.secret_key)
            self.stock_data_client = StockHistoricalDataClient(self.api_key, self.secret_key)
            # A simple check to see if keys are valid
            self.trading_client.get_account()
        except Exception as e:
            logging.warning(f"Could not initialize Alpaca clients, possibly due to invalid keys. API calls will fail. Error: {e}")
            self.trading_client = None
            self.option_data_client = None
            self.stock_data_client = None

    def _check_clients(self):
        if not self.trading_client or not self.option_data_client or not self.stock_data_client:
            raise Exception("Alpaca clients not initialized. Check API keys.")

    def get_latest_stock_price(self, symbol: str) -> float:
        self._check_clients()
        request_params = StockLatestQuoteRequest(symbol_or_symbols=symbol)
        latest_quote = self.stock_data_client.get_stock_latest_quote(request_params)
        return latest_quote[symbol].ask_price

    def get_option_chain(self, symbol: str) -> dict:
        self._check_clients()
        request_params = OptionChainRequest(underlying_symbol=symbol)
        option_chain = self.option_data_client.get_option_chain(request_params)
        return option_chain

    def get_option_quote(self, symbol: str) -> dict:
        self._check_clients()
        request_params = OptionLatestQuoteRequest(symbol_or_symbols=symbol)
        latest_quote = self.option_data_client.get_option_latest_quote(request_params)
        return latest_quote

    def place_order(self, symbol: str, qty: float, side: OrderSide, limit_price: float) -> dict:
        self._check_clients()
        order_data = LimitOrderRequest(
            symbol=symbol,
            qty=qty,
            side=side,
            time_in_force=TimeInForce.DAY,
            limit_price=limit_price
        )
        order = self.trading_client.submit_order(order_data)
        return order

    def get_orders(self):
        self._check_clients()
        return self.trading_client.get_orders()

    def get_order_by_id(self, order_id: str):
        self._check_clients()
        return self.trading_client.get_order_by_id(order_id)

    def cancel_order(self, order_id: str):
        self._check_clients()
        return self.trading_client.cancel_order_by_id(order_id)

    def replace_order(self, order_id: str, new_limit_price: float):
        self._check_clients()
        replace_order_data = ReplaceOrderRequest(
            limit_price=new_limit_price
        )
        return self.trading_client.replace_order_by_id(order_id, replace_order_data)

    def get_positions(self):
        self._check_clients()
        return self.trading_client.get_all_positions()
