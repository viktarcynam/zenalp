import re
from datetime import datetime, timedelta

class SimpleContract:
    def __init__(self, data):
        self.symbol = data['symbol']
        self.expiration_date = data['expiration_date']
        self.strike_price = data['strike_price']
        self.type = data['type']

def parse_option_symbol(symbol: str, underlying_symbol: str):
    """
    Parses an option symbol string to extract details.
    """
    # Remove underlying symbol from the start
    details_str = symbol[len(underlying_symbol):]

    # Extract date, type, and strike
    match = re.match(r'(\d{6})([CP])(\d+)', details_str)
    if not match:
        return None

    date_str, option_type, strike_str = match.groups()

    expiration_date = datetime.strptime(date_str, '%y%m%d').date()
    strike_price = float(strike_str) / 1000.0

    return {
        'symbol': symbol,
        'expiration_date': expiration_date,
        'strike_price': strike_price,
        'type': 'call' if option_type == 'C' else 'put'
    }

def find_nearest_strike(current_price: float, strikes: list[float]) -> float:
    """
    Finds the nearest strike price to the current price.
    """
    if not strikes:
        return None
    return min(strikes, key=lambda x: abs(x - current_price))

def find_next_friday_expiration() -> datetime.date:
    """
    Finds the upcoming Friday expiration date. If today is Friday, it returns next Friday.
    """
    today = datetime.today().date()
    days_until_friday = (4 - today.weekday() + 7) % 7
    next_friday = today + timedelta(days=days_until_friday)
    if next_friday == today:
        next_friday += timedelta(days=7)
    return next_friday
