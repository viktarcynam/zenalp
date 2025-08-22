import click
import time
import datetime
from client import AlpacaClient
from alpaca.trading.enums import OrderSide

@click.group()
def main():
    """
    A CLI for trading options using the Alpaca API.
    """
    pass

@main.command()
@click.argument('symbol')
def trade(symbol):
    """
    Trade options for a given symbol.
    """
    try:
        client = AlpacaClient()
        click.echo(f"Fetching data for {symbol}...")

        # 1. Get latest stock price
        current_price = client.get_latest_stock_price(symbol)
        click.echo(f"Current price of {symbol}: ${current_price:.2f}")

        # 2. Get option chain
        option_chain = client.get_option_chain(symbol)

        # Extract unique expirations and strikes
        expirations = sorted(list(set([contract.expiration_date for contract in option_chain])))
        strikes = sorted(list(set([contract.strike_price for contract in option_chain])))

        # 3. Find next Friday expiration
        today = datetime.date.today()
        expirations_in_future = [exp for exp in expirations if datetime.datetime.strptime(exp, "%Y-%m-%d").date() >= today]
        if not expirations_in_future:
            click.echo("No future expiration dates found.")
            return

        next_friday = client.find_next_friday_expiration()

        # Find closest expiration date to next_friday
        target_expiration_str = min(expirations_in_future, key=lambda d: abs(datetime.datetime.strptime(d, "%Y-%m-%d").date() - next_friday))

        target_expiration = datetime.datetime.strptime(target_expiration_str, "%Y-%m-%d").date()
        click.echo(f"Using expiration date: {target_expiration}")

        # 4. Find nearest strike
        nearest_strike = client.find_nearest_strike(current_price, strikes)
        click.echo(f"Using nearest strike price: ${nearest_strike:.2f}")

        # 5. Find the call and put contracts
        call_contract = None
        put_contract = None
        for contract in option_chain:
            if contract.expiration_date == target_expiration_str and contract.strike_price == nearest_strike:
                if contract.type == 'call':
                    call_contract = contract
                elif contract.type == 'put':
                    put_contract = contract

        if not call_contract or not put_contract:
            click.echo("Could not find call/put contracts for the selected strike and expiration.")
            return

        # 6. Get quotes
        call_quote = client.get_option_quote(call_contract.symbol)
        put_quote = client.get_option_quote(put_contract.symbol)

        call_bid = call_quote[call_contract.symbol].bid_price
        call_ask = call_quote[call_contract.symbol].ask_price
        put_bid = put_quote[put_contract.symbol].bid_price
        put_ask = put_quote[put_contract.symbol].ask_price

        # 7. Display quotes
        click.echo("\n--- Options Quotes ---")
        click.echo(f"Call ({call_contract.symbol}): Bid=${call_bid:.2f}, Ask=${call_ask:.2f}")
        click.echo(f"Put ({put_contract.symbol}): Bid=${put_bid:.2f}, Ask=${put_ask:.2f}")
        click.echo("----------------------\n")

        # 8. Prompt for trade
        trade_side_str = click.prompt("Buy or Sell? (buy/sell)", type=click.Choice(['buy', 'sell']))
        trade_side = OrderSide.BUY if trade_side_str == 'buy' else OrderSide.SELL

        option_type = click.prompt("Call or Put? (call/put)", type=click.Choice(['call', 'put']))

        limit_price = click.prompt("Limit Price", type=float)

        trade_symbol = call_contract.symbol if option_type == 'call' else put_contract.symbol

        # 9. Place order
        click.echo(f"Placing order: {trade_side.value} 1 {trade_symbol} @ ${limit_price:.2f}")
        order = client.place_order(
            symbol=trade_symbol,
            qty=1,
            side=trade_side,
            limit_price=limit_price
        )
        click.echo(f"Order placed with ID: {order.id}")

        # 10. Monitor order
        while True:
            time.sleep(5)
            order_status = client.get_order_by_id(order.id)
            click.echo(f"Order status: {order_status.status}")
            if order_status.status == 'filled':
                click.echo("Order filled!")
                break
            elif order_status.status in ['canceled', 'expired', 'rejected']:
                click.echo("Order not filled.")
                return

        # 11. Prompt for closing order
        click.echo("\n--- Place Closing Order ---")
        closing_limit_price = click.prompt("Limit Price for closing order", type=float)
        closing_side = OrderSide.SELL if trade_side == OrderSide.BUY else OrderSide.BUY

        # 12. Place closing order
        click.echo(f"Placing closing order: {closing_side.value} 1 {trade_symbol} @ ${closing_limit_price:.2f}")
        closing_order = client.place_order(
            symbol=trade_symbol,
            qty=1,
            side=closing_side,
            limit_price=closing_limit_price
        )
        click.echo(f"Closing order placed with ID: {closing_order.id}")

        # 13. Monitor closing order
        while True:
            time.sleep(5)
            order_status = client.get_order_by_id(closing_order.id)
            click.echo(f"Closing order status: {order_status.status}")
            if order_status.status == 'filled':
                click.echo("Closing order filled!")
                break
            elif order_status.status in ['canceled', 'expired', 'rejected']:
                click.echo("Closing order not filled.")
                return

    except Exception as e:
        click.echo(f"An error occurred: {e}", err=True)

@main.group()
def orders():
    """
    Manage orders.
    """
    pass

@orders.command(name="list")
def list_orders():
    """
    List all open orders.
    """
    client = AlpacaClient()
    open_orders = client.get_orders()
    if not open_orders:
        click.echo("No open orders.")
        return
    for order in open_orders:
        click.echo(f"ID: {order.id}, Symbol: {order.symbol}, Side: {order.side}, Qty: {order.qty}, Status: {order.status}")

@orders.command()
@click.argument('order_id')
def cancel(order_id):
    """
    Cancel an open order.
    """
    client = AlpacaClient()
    try:
        client.cancel_order(order_id)
        click.echo(f"Order {order_id} canceled.")
    except Exception as e:
        click.echo(f"Error canceling order: {e}", err=True)

@orders.command()
@click.argument('order_id')
@click.option('--price', type=float, required=True, help="New limit price")
def replace(order_id, price):
    """
    Replace an open order.
    """
    client = AlpacaClient()
    try:
        client.replace_order(order_id, price)
        click.echo(f"Order {order_id} replaced with new price ${price:.2f}.")
    except Exception as e:
        click.echo(f"Error replacing order: {e}", err=True)

@main.group()
def positions():
    """
    Manage positions.
    """
    pass

@positions.command(name="list")
def list_positions():
    """
    List all positions.
    """
    client = AlpacaClient()
    all_positions = client.get_positions()
    if not all_positions:
        click.echo("No positions.")
        return
    for position in all_positions:
        click.echo(f"Symbol: {position.symbol}, Qty: {position.qty}, Side: {position.side}, Market Value: {position.market_value}")

if __name__ == '__main__':
    main()
