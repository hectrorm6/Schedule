from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict
import json
from backend.core.router import dispatcher
from backend.db.models import ChannelType

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        # Maps user_external_id -> list of active websockets
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                await connection.send_text(message)

manager = ConnectionManager()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Process via Dispatcher
            response = await dispatcher.process_message(
                external_user_id=user_id,
                content=message_data.get("text", ""),
                channel=ChannelType.DESKTOP
            )
            
            # Broadcast back to all user's desktop windows
            await manager.send_personal_message(json.dumps(response), user_id)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        print(f"WS Error: {e}")
        manager.disconnect(websocket, user_id)
