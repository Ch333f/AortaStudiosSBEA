from locust import User, task, between, events
from websocket import create_connection, WebSocketConnectionClosedException
import json
import time
import random
import socket


WS_BASE_URL = "ws://localhost:8000/ws"


class ClassroomUser(User):
    wait_time = between(1, 3)


    def on_start(self):
        self.user_id = f"load_user_{random.randint(1, 1_000_000)}"
        self.ws = None
        self.connect()


    def on_stop(self):
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass


    # -------------------------
    # Connection Management
    # -------------------------
    def connect(self):
        self.ws = create_connection(f"{WS_BASE_URL}/{self.user_id}", timeout=5)

        # Initial sync
        msg = json.loads(self.ws.recv())
        self.server_offset = msg["server_time"] - time.time()


    def ensure_connected(self):
        if not self.ws:
            self.connect()
            return

        try:
            # lightweight heartbeat
            self.ws.send(json.dumps({"type": "ping"}))
        except (BrokenPipeError, WebSocketConnectionClosedException, socket.error):
            events.request.fire(
                request_type="WS",
                name="reconnect",
                response_time=0,
                response_length=0,
                exception=Exception("connection lost"),
            )
            self.connect()


    # -------------------------
    # Tasks
    # -------------------------
    @task(3)
    def send_comment(self):
        payload = {
            "type": "comment",
            "video_ts": random.uniform(0, 300),
            "message": "Load test comment",
            "author": "locust"
        }

        try:
            self.ensure_connected()
            start = time.time()
            self.ws.send(json.dumps(payload))

            events.request.fire(
                request_type="WS",
                name="send_comment",
                response_time=int((time.time() - start) * 1000),
                response_length=len(payload["message"]),
                exception=None,
            )

        except (BrokenPipeError, WebSocketConnectionClosedException, socket.error):
            events.request.fire(
                request_type="WS",
                name="send_comment",
                response_time=0,
                response_length=0,
                exception=Exception("WebSocket closed"),
            )


    @task(1)
    def receive_message(self):
        try:
            self.ws.settimeout(0.1)  # ⚠ prevent blocking
            self.ws.recv()
        except socket.timeout:
            pass
        except Exception:
            pass
