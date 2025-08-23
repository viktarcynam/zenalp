import json
import sys
import select
import termios
import tty
import time
from datetime import datetime
from client.client import ApiClient
from client.trading_utils import find_nearest_strike, find_next_friday_expiration, parse_option_symbol, SimpleContract

def format_price(price):
    if price is None: return "N/A"
    return f"{price:.2f}"

def print_response(title, response):
    print(f"\n{'='*20} {title} {'='*20}")
    print(json.dumps(response, indent=2))
    print(f"{'='*52}")

def get_input(prompt):
    print(prompt, end='', flush=True)
    old_settings = termios.tcgetattr(sys.stdin)
    try:
        tty.setraw(sys.stdin.fileno())
        line = ""
        while True:
            char = sys.stdin.read(1)
            if char in ['\r', '\n']:
                print()
                break
            elif char == '\x03': raise KeyboardInterrupt
            elif char == '\x7f':
                if line:
                    line = line[:-1]
                    sys.stdout.write('\b \b')
                    sys.stdout.flush()
            else:
                line += char
                sys.stdout.write(char)
                sys.stdout.flush()
        return line
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

def poll_order_status(client, order_id):
    print("\nMonitoring order... Press 'A' to adjust, 'Q' to cancel.")
    old_settings = termios.tcgetattr(sys.stdin)
    try:
        tty.setcbreak(sys.stdin.fileno())
        while True:
            rlist, _, _ = select.select([sys.stdin], [], [], 2) # 2-second timeout
            if rlist:
                char = sys.stdin.read(1).upper()
                if char == 'A':
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                    new_price_str = input("\nEnter new limit price: ")
                    try:
                        new_price = float(new_price_str)
                        replace_res = client.send_request({'action': 'replace_order', 'order_id': order_id, 'limit_price': new_price})
                        print_response("Replace Order Response", replace_res)
                        if replace_res.get('success'):
                            order_id = replace_res['data']['id']
                            print(f"Order replaced. New order ID: {order_id}")
                    except ValueError:
                        print("Invalid price.")
                    finally:
                        tty.setcbreak(sys.stdin.fileno())
                elif char == 'Q':
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                    if input("Are you sure you want to cancel? (y/n): ").lower() == 'y':
                        cancel_res = client.send_request({'action': 'cancel_order', 'order_id': order_id})
                        print_response("Cancel Order Response", cancel_res)
                        return None # Order canceled
                    tty.setcbreak(sys.stdin.fileno())

            status_res = client.send_request({'action': 'get_order_by_id', 'order_id': order_id})
            if status_res.get('success'):
                status = status_res['data']['status']
                print(f"Status: {status}", end='\r', flush=True)
                if status == 'filled':
                    print("\nOrder filled!")
                    return status_res['data']
                elif status in ['canceled', 'expired', 'rejected']:
                    print(f"\nOrder not filled. Status: {status}")
                    return None
            else:
                print(f"\nError getting status: {status_res.get('error')}")
                return None
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

def main():
    print("--- Alpaca Interactive Option Client ---")
    try:
        with ApiClient() as client:
            while True:
                symbol = get_input("\nEnter symbol (q to quit): ").upper()
                if symbol in ['Q', 'QUIT']: break

                price_res = client.send_request({'action': 'get_latest_stock_price', 'symbol': symbol})
                if not price_res.get('success'):
                    print(f"Error: {price_res.get('error')}"); continue
                last_price = price_res['data']
                print(f"Last price for {symbol}: {format_price(last_price)}")

                chain_res = client.send_request({'action': 'get_option_chain', 'symbol': symbol})
                if not chain_res.get('success'):
                    print(f"Error: {chain_res.get('error')}"); continue

                contracts = []
                if chain_res.get('data'):
                    for option_symbol in chain_res['data'].keys():
                        parsed_data = parse_option_symbol(option_symbol, symbol)
                        if parsed_data:
                            contracts.append(SimpleContract(parsed_data))

                if not contracts:
                    print("No option chain found for this symbol.")
                    continue

                expirations = sorted(list(set([c.expiration_date for c in contracts])))

                today = datetime.today().date()
                expirations_in_future = [exp for exp in expirations if exp >= today]
                if not expirations_in_future:
                    print("No future expiration dates found.")
                    continue

                next_friday = find_next_friday_expiration()
                target_expiration = min(expirations_in_future, key=lambda d: abs(d - next_friday))
                print(f"Using expiration date: {target_expiration}")

                # Filter contracts by target expiration
                contracts_for_expiry = [c for c in contracts if c.expiration_date == target_expiration]

                # Find strikes that have both a call and a put
                call_strikes = {c.strike_price for c in contracts_for_expiry if c.type == 'call'}
                put_strikes = {c.strike_price for c in contracts_for_expiry if c.type == 'put'}
                valid_strikes = sorted(list(call_strikes.intersection(put_strikes)))

                if not valid_strikes:
                    print(f"No valid call/put pairs found for {target_expiration}.")
                    continue

                # Find the nearest strike from the valid strikes
                nearest_strike = find_nearest_strike(last_price, valid_strikes)
                print(f"Using nearest valid strike: {format_price(nearest_strike)}")

                call_contract = next((c for c in contracts_for_expiry if c.strike_price == nearest_strike and c.type == 'call'), None)
                put_contract = next((c for c in contracts_for_expiry if c.strike_price == nearest_strike and c.type == 'put'), None)

                call_quote_res = client.send_request({'action': 'get_option_quote', 'symbol': call_contract.symbol})
                put_quote_res = client.send_request({'action': 'get_option_quote', 'symbol': put_contract.symbol})

                call_bid = call_quote_res.get('data', {}).get(call_contract.symbol, {}).get('bid_price')
                call_ask = call_quote_res.get('data', {}).get(call_contract.symbol, {}).get('ask_price')
                put_bid = put_quote_res.get('data', {}).get(put_contract.symbol, {}).get('bid_price')
                put_ask = put_quote_res.get('data', {}).get(put_contract.symbol, {}).get('ask_price')

                print(f"CALL: {format_price(call_bid)}/{format_price(call_ask)}  |  PUT: {format_price(put_bid)}/{format_price(put_ask)}")

                action_input = get_input("Action (B/S C/P PRICE [QTY]): ").upper().split()

                if len(action_input) < 3:
                    print("Invalid action format. Use: B/S C/P PRICE [QTY]")
                    continue

                side, opt_type, price_str = action_input[0], action_input[1], action_input[2]
                qty = 1
                if len(action_input) == 4:
                    try:
                        qty = int(action_input[3])
                    except ValueError:
                        print("Invalid quantity. Must be an integer.")
                        continue

                try:
                    price = float(price_str)
                except ValueError:
                    print("Invalid price. Must be a number.")
                    continue

                target_contract = next((c for c in contracts if c.strike_price == nearest_strike and c.type == ('call' if opt_type == 'C' else 'put')), None)
                if not target_contract:
                    print("Could not find specified contract."); continue

                order_res = client.send_request({
                    'action': 'place_order', 'symbol': target_contract.symbol,
                    'qty': qty, 'side': 'buy' if side == 'B' else 'sell', 'limit_price': price
                })

                if not order_res.get('success'):
                    print(f"Error placing order: {order_res.get('error')}"); continue

                filled_order = poll_order_status(client, order_res['data']['id'])
                if filled_order:
                    print("Closing order workflow not implemented yet.")

    except KeyboardInterrupt: print("\nClient shutdown.")
    except Exception as e: print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    main()
