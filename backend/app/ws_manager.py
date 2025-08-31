from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # user_id -> ws objekat
        self.active_connections = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        # await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int):
        self.active_connections.pop(user_id, None)

    async def send_personal_message(self, user_id: int, message: dict):
        ws = self.active_connections.get(user_id)
        if ws:
            await ws.send_json(message)

    async def broadcast(self, user_ids: list[int], message: dict):
        for uid in user_ids:
            await self.send_personal_message(uid, message)


manager = ConnectionManager()
