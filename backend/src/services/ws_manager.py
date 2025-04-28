from fastapi import WebSocket
import logging

class WebSocketManager:
    def __init__(self):
        # self.active_connections: list[WebSocket] = []
        self.active_connections: dict[str, list[WebSocket]] = {
            "status": [],
            "candles": []
        }
        self.logger = logging.getLogger(__name__)
    
    async def connect(self, websocket: WebSocket, group: str = "status"):
        await websocket.accept()
        if group not in self.active_connections:
            self.active_connections[group] = []
        self.active_connections[group].append(websocket)
        self.logger.info(f"🔗 Nuevo cliente WebSocket conectado en grupo: '{group}': {websocket}")

    async def disconnect(self, websocket: WebSocket, group: str = "status"):
        if group in self.active_connections and websocket in self.active_connections[group]:
            if websocket in self.active_connections[group]:
                self.active_connections[group].remove(websocket)
                self.logger.info(f"🔌 Cliente WebSocket desconectado del grupo: '{group}': {websocket}")
        # if websocket in self.active_connections:
        #     self.active_connections.remove(websocket)
        #     self.logger.info(f"🔌 Cliente WebSocket desconectado: {websocket}")

    async def broadcast(self, message: dict, group: str = "status"):
        if group not in self.active_connections:
            self.logger.warning(f"⚠️ Grupo '{group}' no encontrado para el broadcast.")
            return
    
        disconnected_clients = []
        for connection in self.active_connections[group]:
            try:
                await connection.send_json(message)
            except Exception as e:
                self.logger.warning(f"⚠️ No se pudo mensaje a websocket ({group}): Error: {e}")
                disconnected_clients.append(connection)

        for ws in disconnected_clients:
            self.disconnect(ws, group)

        if self.active_connections[group]:
            self.logger.info(f"📡 Mensaje enviado a {len(self.active_connections[group])} clientes en grupo '{group}'.")
        else:
            self.logger.warning(f"⚠️ No hay clientes conectados en el grupo '{group}'.")

ws_manager = WebSocketManager()