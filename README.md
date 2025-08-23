# Alpaca Trading App - Client-Server

This application has been refactored into a client-server architecture for trading options using the Alpaca API.

The server runs in the background, handles communication with the Alpaca API, and caches data. The client is an interactive terminal application for placing and managing trades.

## Architecture

- **Server (`server/`):** A multithreaded TCP server that handles the business logic.
  - `server.py`: The main server application.
  - `alpaca_service.py`: A wrapper for all interactions with the Alpaca API.
  - `cache_manager.py`: Handles caching of data.
- **Client (`client/`):** An interactive terminal client.
  - `noni.py`: The main interactive client application, inspired by `noni-1.py`.
  - `client.py`: A simple TCP client for communicating with the server.
  - `trading_utils.py`: Helper functions for the client.
- **Common (`common/`):** Shared code.
  - `json_parser.py`: Defines and validates the JSON-based communication protocol.

## Setup

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Set up environment variables:**
    Create a `.env` file in the root of the project and add your Alpaca API keys.
    ```
    APCA_API_KEY_ID="YOUR_API_KEY_ID"
    APCA_API_SECRET_KEY="YOUR_API_SECRET_KEY"
    ```

## Usage

1.  **Start the Server:**
    Open a terminal and run the following command from the root of the project:
    ```bash
    PYTHONPATH=. python3 start_server.py
    ```
    The server will start and run in the foreground.

2.  **Run the Interactive Client:**
    Open another terminal and run the client:
    ```bash
    PYTHONPATH=. python3 -m client.noni
    ```
    The interactive client will start. You can now enter stock symbols and follow the prompts to trade.

### Interactive Client Features

-   Enter a stock symbol to get the latest price.
-   The application will suggest the nearest strike and a suitable expiration date.
-   It will display the current bid/ask prices for the call and put options.
-   You can place an order by specifying the action (B/S), type (C/P), price, and quantity.
-   Once an order is placed, the application will monitor its status.
-   While monitoring, you can press:
    -   `A` to adjust the limit price of the order.
    -   `Q` to cancel the order.
