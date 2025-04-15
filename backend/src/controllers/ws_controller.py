from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.services.ws_manager import ws_manager

router = APIRouter()

# clients = []

@router.websocket("/status-stream")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        await websocket.close()