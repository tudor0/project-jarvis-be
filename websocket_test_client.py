import websocket
import json
import time
import threading


class WebSocketTestClient:
    def __init__(self, url):
        self.url = url
        self.ws = None

    def on_message(self, ws, message):
        print(f"Received from server: {message}")

    def on_error(self, ws, error):
        print(f"WebSocket error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print("Connection closed")

    def on_open(self, ws):
        print("Connected to WebSocket server")

    def connect(self):
        """Connect to the WebSocket server"""
        websocket.enableTrace(True)  # Enable debug traces
        self.ws = websocket.WebSocketApp(
            self.url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )

        # Run in a separate thread
        wst = threading.Thread(target=self.ws.run_forever)
        wst.daemon = True
        wst.start()

        # Wait a moment for connection
        time.sleep(1)
        return self.ws

    def send_message(self, message):
        """Send a message to the server"""
        if self.ws:
            self.ws.send(message)
            print(f"Sent: {message}")
        else:
            print("Not connected!")

    def send_json(self, data):
        """Send JSON data to the server"""
        json_message = json.dumps(data)
        self.send_message(json_message)

    def close(self):
        """Close the connection"""
        if self.ws:
            self.ws.close()


def interactive_test():
    """Interactive test function"""
    client = WebSocketTestClient("ws://localhost:8765")

    try:
        client.connect()

        print("\n=== WebSocket Test Client ===")
        print("Commands:")
        print("  text <message>  - Send plain text")
        print("  json <message>  - Send JSON with message")
        print("  quit           - Exit")
        print("================================\n")

        while True:
            user_input = input("Enter command: ").strip()

            if user_input.lower() == 'quit':
                break
            elif user_input.startswith('text '):
                message = user_input[5:]
                client.send_message(message)
            elif user_input.startswith('json '):
                message = user_input[5:]
                client.send_json({
                    "type": "test_message",
                    "content": message,
                    "timestamp": time.time()
                })
            else:
                print("Invalid command. Use 'text <message>', 'json <message>', or 'quit'")

    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        client.close()
        print("Disconnected")


def automated_test():
    """Automated test function"""
    client = WebSocketTestClient("ws://localhost:8765")

    try:
        client.connect()

        # Test messages
        test_messages = [
            "Hello, WebSocket!",
            "This is a test message",
            "Testing special characters: åéîøü",
            "Numbers and symbols: 12345 !@#$%"
        ]

        test_json_messages = [
            {"type": "greeting", "content": "Hello from test client"},
            {"type": "data", "content": "Some test data", "id": 1},
            {"type": "status", "content": "Testing JSON messages"}
        ]

        print("Sending test messages...")

        # Send plain text messages
        for i, msg in enumerate(test_messages, 1):
            print(f"\nTest {i}: Sending plain text")
            client.send_message(msg)
            time.sleep(1)

        # Send JSON messages
        for i, msg in enumerate(test_json_messages, 1):
            print(f"\nJSON Test {i}: Sending JSON data")
            client.send_json(msg)
            time.sleep(1)

        print("\nAll tests completed! Check server logs.")
        time.sleep(2)

    except Exception as e:
        print(f"Test error: {e}")
    finally:
        client.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "auto":
        automated_test()
    else:
        interactive_test()