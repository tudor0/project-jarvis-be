import asyncio
import json
import logging
from datetime import datetime
from typing import Set
from fastapi import WebSocket, WebSocketDisconnect

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WebSocketManager:
    """WebSocket connection manager for FastAPI integration"""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        client_addr = f"{websocket.client.host}:{websocket.client.port}"
        logger.info(f"New client connected: {client_addr} - Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        self.active_connections.discard(websocket)
        client_addr = f"{websocket.client.host}:{websocket.client.port}"
        logger.info(f"Client disconnected: {client_addr} - Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket connection"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending message to client: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: str):
        """Send a message to all connected clients"""
        if not self.active_connections:
            logger.warning("No active connections for broadcast")
            return

        disconnected = []
        for connection in self.active_connections.copy():
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    async def handle_message(self, websocket: WebSocket, message: str):
        """Process incoming messages from clients"""
        client_addr = f"{websocket.client.host}:{websocket.client.port}"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            logger.info(f"[{timestamp}] Received from {client_addr}: {message}")

            # Try to parse as JSON (handles both plain text and JSON)
            try:
                data = json.loads(message)
                if isinstance(data, dict):
                    # Handle structured data
                    message_type = data.get('type', 'unknown')
                    content = data.get('content', data.get('message', ''))
                    logger.info(f"Message type: {message_type}, Content: {content}")

                    # You can add custom logic here based on message type
                    await self._handle_structured_message(websocket, data, client_addr)
                else:
                    # Handle JSON strings/arrays
                    logger.info(f"JSON data: {data}")
                    await self._handle_json_data(websocket, data, client_addr)

            except json.JSONDecodeError:
                # Handle plain text messages
                logger.info(f"Plain text message: {message}")
                await self._handle_text_message(websocket, message, client_addr)

        except Exception as e:
            logger.error(f"Error processing message from {client_addr}: {e}")
            await self._send_error_response(websocket, str(e))

    async def _handle_structured_message(self, websocket: WebSocket, data: dict, client_addr: str):
        """Handle structured JSON messages"""
        message_type = data.get('type', 'unknown')

        # Add your custom message handling logic here
        if message_type == 'ping':
            await self._send_response(websocket, {
                "type": "pong",
                "timestamp": datetime.now().isoformat()
            })
        elif message_type == 'echo':
            await self._send_response(websocket, {
                "type": "echo_response",
                "original_message": data,
                "timestamp": datetime.now().isoformat()
            })
        else:
            # Default acknowledgment
            await self._send_response(websocket, {
                "status": "received",
                "message_type": message_type,
                "timestamp": datetime.now().isoformat(),
                "message": "Structured message received successfully"
            })

    async def _handle_json_data(self, websocket: WebSocket, data, client_addr: str):
        """Handle JSON data that isn't a structured message"""
        await self._send_response(websocket, {
            "status": "received",
            "data_type": type(data).__name__,
            "timestamp": datetime.now().isoformat(),
            "message": "JSON data received successfully"
        })

    async def _handle_text_message(self, websocket: WebSocket, message: str, client_addr: str):
        """Handle plain text messages"""
        # Add your custom text processing logic here

        await self._send_response(websocket, {
            "status": "received",
            "message_length": len(message),
            "timestamp": datetime.now().isoformat(),
            "message": "Text message received successfully"
        })

    async def _send_response(self, websocket: WebSocket, response_data: dict):
        """Send a JSON response to the client"""
        try:
            response = json.dumps(response_data)
            await websocket.send_text(response)
        except Exception as e:
            logger.error(f"Error sending response: {e}")

    async def _send_error_response(self, websocket: WebSocket, error_message: str):
        """Send an error response to the client"""
        error_response = {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "message": f"Error processing message: {error_message}"
        }
        await self._send_response(websocket, error_response)

    def get_connection_count(self) -> int:
        """Get the number of active connections"""
        return len(self.active_connections)

    def get_client_info(self) -> list:
        """Get information about connected clients"""
        clients = []
        for ws in self.active_connections:
            clients.append({
                "host": ws.client.host,
                "port": ws.client.port,
                "address": f"{ws.client.host}:{ws.client.port}"
            })
        return clients


# Usage example for FastAPI integration
"""
# In your main FastAPI file, add this:

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from websocket_manager import WebSocketManager

app = FastAPI()
manager = WebSocketManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.handle_message(websocket, data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Optional: Add REST endpoints for WebSocket info
@app.get("/ws/connections")
async def get_connections():
    return {
        "active_connections": manager.get_connection_count(),
        "clients": manager.get_client_info()
    }

@app.post("/ws/broadcast")
async def broadcast_message(message: dict):
    await manager.broadcast(json.dumps(message))
    return {"status": "Message broadcasted to all clients"}
"""