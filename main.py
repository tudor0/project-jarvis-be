import asyncio
import websockets
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WebSocketServer:
    def __init__(self, host="0.0.0.0", port=8765):
        self.host = host
        self.port = port
        self.connected_clients = set()

    async def handle_client(self, websocket, path):
        """Handle individual client connections"""
        client_addr = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info(f"New client connected: {client_addr}")

        # Add client to connected clients set
        self.connected_clients.add(websocket)

        try:
            async for message in websocket:
                await self.process_message(websocket, message, client_addr)

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {client_addr}")
        except Exception as e:
            logger.error(f"Error handling client {client_addr}: {e}")
        finally:
            # Remove client from connected clients set
            self.connected_clients.discard(websocket)

    async def process_message(self, websocket, message, client_addr):
        """Process incoming messages from clients"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"[{timestamp}] Received from {client_addr}: {message}")

            # Try to parse as JSON (optional - handles both plain text and JSON)
            try:
                data = json.loads(message)
                if isinstance(data, dict):
                    # Handle structured data
                    message_type = data.get('type', 'unknown')
                    content = data.get('content', data.get('message', ''))
                    logger.info(f"Message type: {message_type}, Content: {content}")
                else:
                    # Handle JSON strings/arrays
                    logger.info(f"JSON data: {data}")
            except json.JSONDecodeError:
                # Handle plain text messages
                logger.info(f"Plain text message: {message}")

            # Send acknowledgment back to client (optional)
            response = {
                "status": "received",
                "timestamp": timestamp,
                "message": "Message received successfully"
            }
            await websocket.send(json.dumps(response))

        except Exception as e:
            logger.error(f"Error processing message from {client_addr}: {e}")
            error_response = {
                "status": "error",
                "message": f"Error processing message: {str(e)}"
            }
            await websocket.send(json.dumps(error_response))

    async def broadcast_message(self, message):
        """Broadcast message to all connected clients"""
        if self.connected_clients:
            await asyncio.gather(
                *[client.send(message) for client in self.connected_clients],
                return_exceptions=True
            )

    def get_connected_clients_count(self):
        """Get number of connected clients"""
        return len(self.connected_clients)

    async def start_server(self):
        """Start the WebSocket server"""
        logger.info(f"Starting WebSocket server on {self.host}:{self.port}")

        async with websockets.serve(
                self.handle_client,
                self.host,
                self.port,
                ping_interval=20,
                ping_timeout=10,
                max_size=1024 * 1024,  # 1MB max message size
        ):
            logger.info(f"WebSocket server running on ws://{self.host}:{self.port}")
            await asyncio.Future()  # Run forever


# Simple usage example
async def simple_handler(websocket, path):
    """Simplified handler function for basic use cases"""
    client_addr = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
    print(f"Client connected: {client_addr}")

    try:
        async for message in websocket:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] Received: {message}")

            # Send simple acknowledgment
            await websocket.send(f"Received: {message}")

    except websockets.exceptions.ConnectionClosed:
        print(f"Client disconnected: {client_addr}")


def main():
    """Main function to run the WebSocket server"""
    # Option 1: Use the WebSocketServer class (recommended)
    server = WebSocketServer(host="0.0.0.0", port=8765)
    asyncio.run(server.start_server())

    # Option 2: Use simple handler (uncomment to use instead)
    # asyncio.run(websockets.serve(simple_handler, "0.0.0.0", 8765))
    # print("Simple WebSocket server running on ws://0.0.0.0:8765")
    # asyncio.get_event_loop().run_forever()


if __name__ == "__main__":
    main()