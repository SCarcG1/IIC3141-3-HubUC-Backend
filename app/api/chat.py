from typing import List, Dict
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.usernames: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, username: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.usernames[websocket] = username
        # mensaje “sistema” de nuevo ingreso
        await self.broadcast({"system": True, "message": f"✅ {username} se ha unido al chat"})

    def disconnect(self, websocket: WebSocket) -> str:
        username = self.usernames.get(websocket, "Alguien")
        self.active_connections.remove(websocket)
        del self.usernames[websocket]
        return username

    async def broadcast(self, data: dict):
        for connection in list(self.active_connections):
            await connection.send_json(data)

# instancia compartida
manager = ConnectionManager()
