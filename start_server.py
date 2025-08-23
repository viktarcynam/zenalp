import logging
from server.server import AlpacaServer

def main():
    """Main function to start the server."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    server = AlpacaServer()
    try:
        server.initialize_services()
        server.start()
    except KeyboardInterrupt:
        logging.info("Server interrupted by user.")
    except Exception as e:
        logging.error(f"Server startup error: {e}")
    finally:
        server.stop()

if __name__ == "__main__":
    main()
