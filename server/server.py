import socket
import threading
import json
import logging
import sys
from datetime import datetime

# This will be run with PYTHONPATH=.
from common.json_parser import json_parser
from server.alpaca_service import AlpacaService
from server.cache_manager import cache_manager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("server.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def recv_all(sock, n):
    # Helper function to receive n bytes or return None if EOF is hit
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    return data

class AlpacaServer:
    def __init__(self, host='127.0.0.1', port=65432):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        self.alpaca_service = None

    def initialize_services(self):
        try:
            self.alpaca_service = AlpacaService()
            logger.info("Alpaca services initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Alpaca services: {e}")
            raise

    def start(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)
        self.running = True
        logger.info(f"Server started on {self.host}:{self.port}")

        while self.running:
            try:
                client_socket, address = self.socket.accept()
                logger.info(f"New client connected from {address}")
                client_thread = threading.Thread(target=self._handle_client, args=(client_socket, address))
                client_thread.daemon = True
                client_thread.start()
            except socket.error as e:
                if self.running:
                    logger.error(f"Socket error: {e}")
                break

    def stop(self):
        self.running = False
        if self.socket:
            self.socket.close()
        logger.info("Server stopped.")

    def _handle_client(self, client_socket, address):
        try:
            while self.running:
                header_data = recv_all(client_socket, 4)
                if not header_data:
                    break

                msg_len = int.from_bytes(header_data, 'big')
                data = recv_all(client_socket, msg_len)
                if not data:
                    break

                request = json.loads(data.decode('utf-8'))
                logger.info(f"Received request from {address}: {request.get('action', 'unknown')}")

                response = self._process_request(request)

                response_json = json.dumps(response, default=str) # Use default=str to handle datetime objects
                response_bytes = response_json.encode('utf-8')
                response_header = len(response_bytes).to_bytes(4, byteorder='big')
                client_socket.sendall(response_header + response_bytes)
        except Exception as e:
            logger.error(f"Error handling client {address}: {e}")
        finally:
            client_socket.close()
            logger.info(f"Client {address} disconnected.")

    def _process_request(self, request):
        action = request.get('action', '').lower()

        validation_result = json_parser.validate_request(request)
        if not validation_result['success']:
            return validation_result

        try:
            if action == 'ping':
                return {'success': True, 'message': 'pong'}

            elif action == 'get_latest_stock_price':
                symbol = request.get('symbol')
                price = self.alpaca_service.get_latest_stock_price(symbol)
                return {'success': True, 'data': price}

            elif action == 'get_option_chain':
                symbol = request.get('symbol')
                chain = self.alpaca_service.get_option_chain(symbol)
                # The chain object is not directly serializable to JSON
                # I need to convert it to a dict of dicts
                chain_dict = {key: value.dict() for key, value in chain.items()}
                return {'success': True, 'data': chain_dict}

            elif action == 'get_option_quote':
                symbol = request.get('symbol')
                quote = self.alpaca_service.get_option_quote(symbol)
                # The quote object is not directly serializable to JSON
                quote_dict = {key: value.dict() for key, value in quote.items()}
                return {'success': True, 'data': quote_dict}

            elif action == 'place_order':
                order = self.alpaca_service.place_order(
                    symbol=request.get('symbol'),
                    qty=request.get('qty'),
                    side=request.get('side'),
                    limit_price=request.get('limit_price')
                )
                return {'success': True, 'data': order.dict()}

            elif action == 'get_order_by_id':
                order = self.alpaca_service.get_order_by_id(request.get('order_id'))
                return {'success': True, 'data': order.dict()}

            elif action == 'get_positions':
                positions = self.alpaca_service.get_positions()
                return {'success': True, 'data': [p.dict() for p in positions]}

            elif action == 'cancel_order':
                result = self.alpaca_service.cancel_order(request.get('order_id'))
                return {'success': True, 'data': result}

            elif action == 'replace_order':
                order = self.alpaca_service.replace_order(
                    order_id=request.get('order_id'),
                    new_limit_price=request.get('limit_price')
                )
                return {'success': True, 'data': order.dict()}

            else:
                return {'success': False, 'error': f'Unknown action: {action}'}

        except Exception as e:
            logger.error(f"Error processing action {action}: {e}")
            return {'success': False, 'error': str(e)}
