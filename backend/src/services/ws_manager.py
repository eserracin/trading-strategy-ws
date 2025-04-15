from fastapi import WebSocket
import logging

class WebSocketManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.logger = logging.getLogger(__name__)
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.logger.info(f"🔗 Nuevo cliente WebSocket conectado: {websocket}")

    async def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            self.logger.info(f"🔌 Cliente WebSocket desconectado: {websocket}")

    async def broadcast(self, message: dict):
        disconnected_clients = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                self.logger.warning(f"⚠️ No se pudo enviar al cliente WebSocket: {e}")
                disconnected_clients.append(connection)

        for ws in disconnected_clients:
            self.disconnect(ws)

        if self.active_connections:
            self.logger.info(f"📡 Mensaje enviado a WebSocket: {message}")
        else:
            self.logger.warning("⚠️ No hay clientes WebSocket conectados.")

ws_manager = WebSocketManager()