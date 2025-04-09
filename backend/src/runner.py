import asyncio
import threading
from core import ContextStrategy, TradeExecutor
from api.websocket import clients
from binance.client import Client
from config import *
import pandas as pd
import logging

# Diccionario en memerioa para almacenar operaciones activas
operaciones = []

class StrategyRunner:
    def __init__(self):
        self.task = {}
        self.client = Client(api_key=API_KEY, api_secret=API_SECRET)

    def estrategias_disponibles(self):
        return ContextStrategy.STRATEGIES.keys()
    
    def iniciar_estrategia(self, symbol, strategy_name, test=False):
        loop = asyncio.new_event_loop()
        tread = threading.Thread(target=self.__run_loop, args=(loop, symbol, strategy_name, test))
        tread.start()
        return f"Strategy {strategy_name} started for {symbol}"
    
    def __run_loop(self, loop, symbol, strategy_name, test):
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._run_strategy(symbol, strategy_name, test))

    async def _run_strategy(self, symbol, strategy_name, test):
        logger = logging.getLogger(f"{symbol}_{strategy_name}")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)

        logger.info(f"symbol: {symbol}, strategy: {strategy_name}, test: {test}")
        logger.info("Iniciando estrategia...")

        self.client = Client(api_key=API_KEY, api_secret=API_SECRET, testnet=test)
        trade_strategy = ContextStrategy.get_strategy(strategy=strategy_name, binance_client=self.client, logger=logger)
        trade_executor = TradeExecutor(client=self.client, symbol=symbol, logger=logger)

        # Obtiene historial inicial sufiecient antes de arrancar el websocket
        df_hist = trade_strategy.obtener_historial_inicial(symbol, INTERVAL, period=50) 

        from wsclient.binance_ws import BinanceWebSocket
        async with BinanceWebSocket(symbol, INTERVAL, logger) as bws:
            try:
                async for kline in bws.klines_stream():
                    candle = kline["k"]
                    if candle["x"]:
                        nueva_fila = pd.DataFrame([{
                            "open_time": candle["t"],
                            "open": float(candle["o"]),
                            "high": float(candle["h"]),
                            "low": float(candle["l"]),
                            "close": float(candle["c"]),
                            "volume": float(candle["v"]),
                            "close_time": candle["T"],
                            "symbol": symbol,
                        }])
                        df_hist = pd.concat([df_hist, nueva_fila], ignore_index=True).iloc[-100:]

                        modo, entry_price, sl, tp = trade_strategy.check_entry(df_hist)
                        if modo:
                            qty = trade_strategy.calculate_position_size(entry_price, sl)
                            logger.info(f"💥 Señal {modo} - Entry: {entry_price}, SL: {sl}, TP: {tp}")
                            operaciones.append(
                                {
                                    "symbol": symbol,
                                    "strategy": strategy_name,
                                    "modo": modo, 
                                    "entry_price": entry_price, 
                                    "sl": sl, 
                                    "tp": tp, 
                                    "qty": qty}
                            )
                            await self.notificar_entrada(operaciones)
                            # Implementar Trade Manager
                            # resultado = trade_executor.place_order(mode=mode, entry_price=entry_price, sl_price=sl, tp_price=tp, quantity=position_size)
                            resultado = None
                            if resultado:
                                logger.info(f"Ordenes de compra y venta creadas: {resultado}")
                            else:
                                logger.error("Error al crear las órdenes de compra y venta.")
            except Exception as e:
                logger.exception(f"Error en el bucle principal: {e}")

    async def notificar_entrada(data: dict):
        data["type"] = "nuevo-trade"
        for client in clients:
            try:
                await client.send_text(data)
            except Exception as e:
                print(f"Error al enviar notificación: {e}")

    def get_symbols(self):
        exchange_info = self.client.futures_exchange_info()
        symbols = [symbol["symbol"] for symbol in exchange_info["symbols"] if symbol["status"] == "TRADING"]
        return sorted(symbols)

strategy_runner = StrategyRunner()

def get_operations():
    return operaciones