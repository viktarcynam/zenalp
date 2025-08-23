import socket
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def recv_all(sock, n):
    # Helper function to receive n bytes or return None if EOF is hit
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    return data

class ApiClient:
    """
    A client for communicating with the Alpaca trade server.
    """
    def __init__(self, host='127.0.0.1', port=65432):
        self.host = host
        self.port = port
        self.socket = None

    def connect(self):
        """
        Connects to the server.
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            logging.info(f"Connected to server at {self.host}:{self.port}")
        except Exception as e:
            logging.error(f"Failed to connect to server: {e}")
            raise

    def disconnect(self):
        """
        Disconnects from the server.
        """
        if self.socket:
            self.socket.close()
            self.socket = None
            logging.info("Disconnected from server.")

    def send_request(self, request_data: dict):
        """
        Sends a request to the server and returns the response.
        """
        if not self.socket:
            raise ConnectionError("Not connected to server.")

        try:
            request_json = json.dumps(request_data)
            request_bytes = request_json.encode('utf-8')
            header = len(request_bytes).to_bytes(4, byteorder='big')
            self.socket.sendall(header + request_bytes)

            response_header = recv_all(self.socket, 4)
            if not response_header:
                return {'success': False, 'error': 'Connection closed by server'}

            response_length = int.from_bytes(response_header, 'big')
            response_bytes = recv_all(self.socket, response_length)
            if not response_bytes:
                return {'success': False, 'error': 'Connection closed by server during body read'}

            response_data = json.loads(response_bytes.decode('utf-8'))
            return response_data
        except Exception as e:
            logging.error(f"Error sending/receiving request: {e}")
            return {'success': False, 'error': str(e)}

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
