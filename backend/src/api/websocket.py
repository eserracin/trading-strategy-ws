from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

clients = []

@router.websocket("/status-stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        clients.remove(websocket)
        await websocket.close()