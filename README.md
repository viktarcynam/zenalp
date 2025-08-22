# trade1

A CLI for trading options using the Alpaca API.

## Setup

1. **Install dependencies:**

   ```bash
   pip install poetry
   poetry install
   ```

2. **Set up environment variables:**

   Create a `.env` file in the root of the project and add your Alpaca API keys. You can get your keys from the [Alpaca dashboard](https://app.alpaca.markets/).

   ```
   APCA_API_KEY_ID="YOUR_API_KEY_ID"
   APCA_API_SECRET_KEY="YOUR_API_SECRET_KEY"
   ```

   **Note:** For development, it is recommended to use paper trading keys.

## Usage

The application provides three CLI commands:

- `trade1`: The main command to trade options.
- `orders`: To manage open orders.
- `positions`: To view your current positions.

### `trade1`

```bash
poetry run trade1 <SYMBOL>
```

This command will:
1. Find the nearest strike price and the next Friday's expiration date for the given symbol.
2. Display the bid/ask prices for the call and put options.
3. Prompt you to enter a trade (buy/sell, call/put, limit price).
4. Place the order and monitor it until it's filled.
5. Once the order is filled, it will prompt you for a closing order.
6. Place the closing order and monitor it until it's filled.

### `orders`

```bash
# List all open orders
poetry run orders list

# Cancel an order
poetry run orders cancel <ORDER_ID>

# Replace an order
poetry run orders replace <ORDER_ID>
```

### `positions`

```bash
# List all positions
poetry run positions list
```
