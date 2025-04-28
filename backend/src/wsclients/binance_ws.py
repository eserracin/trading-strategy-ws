from binance.websocket.um_futures.websocket_client import UMFuturesWebsocketClient
import asyncio
import logging
import json

class BinanceWebSocket:
    def __init__(self, symbol, interval, logger: logging.Logger = None):
        self.symbol = symbol.upper()
        self.interval = interval
        self.client = None
        self.logger = logger or logging.getLogger(__name__)
        self.loop = None
        self.queue = asyncio.Queue()

    def message_handler(self, _, message: dict):
        try:
            if isinstance(message, str):
                message = json.loads(message)
            if "k" not in message:
                return
            self.loop.call_soon_threadsafe(self.queue.put_nowait, message)
        except Exception as e:
            self.logger.exception(f"❌ Error procesando mensaje del WebSocket. Mensaje original: {message}")

    async def __aenter__(self):
        self.loop = asyncio.get_running_loop()
        self.client = UMFuturesWebsocketClient(on_message=self.message_handler)
        self.client.kline(symbol=self.symbol, interval=self.interval, id=1)
        self.logger.info("Conexión WebSocket establecida con Binance Future")
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.client:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self.client.stop)
            await self.queue.put(None)  # Señal para terminar generador
            self.logger.info("Conexión WebSocket cerrada con Binance Future")

    async def klines_stream(self):
        try:
            while True:
                message = await self.queue.get()
                if message is None:  # Salir del generador
                    break
                yield message
        except asyncio.CancelledError:
            self.logger.info("⛔ klines_stream() cancelado con éxito.")
            return

    
    async def close(self):
        if self.client:
            await self.client.stop()
            await self.queue.put(None)  # Señal para terminar generador
            self.logger.info("🔌 WebSocket Binance cerrado correctamente.")
