from fastapi import WebSocket
from typing import Dict, List
import json

class ConnectionManager:
    def __init__(self):
        self.active: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str, home_id: str):
        await websocket.accept()
        key = f"{user_id}:{home_id}"
        if key not in self.active:
            self.active[key] = []
        self.active[key].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str, home_id: str):
        key = f"{user_id}:{home_id}"
        if key in self.active:
            self.active[key] = [w for w in self.active[key] if w != websocket]
            if not self.active[key]:
                del self.active[key]

    async def broadcast_home(self, home_id: str, message: dict):
        # Send to all users connected to this home
        for key, sockets in list(self.active.items()):
            if key.endswith(f":{home_id}"):
                dead = []
                for ws in sockets:
                    try:
                        await ws.send_json(message)
                    except Exception:
                        dead.append(ws)
                for ws in dead:
                    self.disconnect(ws, key.split(":")[0], home_id)

    async def broadcast_user(self, user_id: str, message: dict):
        for key, sockets in list(self.active.items()):
            if key.startswith(f"{user_id}:"):
                dead = []
                for ws in sockets:
                    try:
                        await ws.send_json(message)
                    except Exception:
                        dead.append(ws)
                for ws in dead:
                    rest = key.split(":", 1)[1] if ":" in key else ""
                    self.disconnect(ws, user_id, rest)

    async def broadcast_priority(self, home_id: str, message: dict):
        """Push event with priority flag — AR Premium dashboards handle immediately."""
        message["_priority"] = True
        for key, sockets in list(self.active.items()):
            if key.endswith(f":{home_id}"):
                dead = []
                for ws in sockets:
                    try:
                        await ws.send_json(message)
                    except Exception:
                        dead.append(ws)
                for ws in dead:
                    self.disconnect(ws, key.split(":")[0], home_id)

manager = ConnectionManager()
