from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.services.ws_manager import ws_manager

router = APIRouter()

# clients = []

# Para status stream (ordenes nuevas)
@router.websocket("/status-stream")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket, group="status")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, group="status")

# Para candle-stream (velas en tiempo real)
@router.websocket("/candle-stream")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket, group="candles")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, group="candles")