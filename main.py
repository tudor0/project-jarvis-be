
# Example of how to integrate WebSocketManager into your existing FastAPI app

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from websocket_manager import WebSocketManager
import json

# Your existing FastAPI app
app = FastAPI()

# Create WebSocket manager instance
websocket_manager = WebSocketManager()

# Add WebSocket endpoint to your existing routes
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for tablet connections"""
    await websocket_manager.connect(websocket)
    try:
        while True:
            # Receive text from the frontend tablet
            data = await websocket.receive_text()
            # Process the message using the manager
            await websocket_manager.handle_message(websocket, data)
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)

# Optional: Add REST endpoints for monitoring WebSocket connections
@app.get("/api/ws/status")
async def websocket_status():
    """Get WebSocket connection status"""
    return {
        "active_connections": websocket_manager.get_connection_count(),
        "clients": websocket_manager.get_client_info(),
        "status": "running"
    }

@app.post("/api/ws/broadcast")
async def broadcast_to_clients(message: dict):
    """Broadcast a message to all connected WebSocket clients"""
    try:
        await websocket_manager.broadcast(json.dumps(message))
        return {
            "status": "success",
            "message": "Broadcasted to all clients",
            "recipient_count": websocket_manager.get_connection_count()
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Broadcast failed: {str(e)}"
        }

@app.get("/api/ws/send/{client_host}")
async def send_to_specific_client(client_host: str, message: dict):
    """Send message to a specific client (if you need this functionality later)"""
    # This is a placeholder - you'd need to modify WebSocketManager to support this
    return {"status": "Feature not implemented yet"}
