import asyncio
import threading
from core import ContextStrategy, TradeExecutor
from src.wsclients.binance_ws import BinanceWebSocket
# from src.controllers.ws_controller import clients
from src.services.ws_manager import ws_manager
from binance.client import Client
from config.settings import *
import pandas as pd
import logging

# Diccionario en memerioa para almacenar operaciones activas
operaciones = []
tareas = {}

class StrategyRunner:
    def __init__(self):
        self.task = {}
        self.client = Client(api_key=API_KEY, api_secret=API_SECRET)

    def estrategias_disponibles(self):
        return list(ContextStrategy.STRATEGIES.keys())
    
    def iniciar_estrategia(self, symbol, strategy_name, test=False):
        loop = asyncio.new_event_loop()
        tread = threading.Thread(target=self.__run_loop, args=(loop, symbol, strategy_name, test))
        tread.start()
        self.task[symbol] = (loop, tread)
        return f"Strategy {strategy_name} started for {symbol}"
    
    def __run_loop(self, loop, symbol, strategy_name, test):
        asyncio.set_event_loop(loop)
        self.task[symbol] = loop.create_task(self._run_strategy(symbol, strategy_name, test))
        try:
            loop.run_until_complete(self.task[symbol])
        except asyncio.CancelledError:
            self.logger.info("Tarea cancelada")
        except Exception as e:
            self.logger.exception(f"Error en el bucle de eventos: {e}")
        finally:
            self.logger.info("Tarea finalizada")
            loop.close()

    async def _run_strategy(self, symbol, strategy_name, test):
        self.logger = logging.getLogger(f"{symbol}_{strategy_name}")
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)

        self.logger.info(f"symbol: {symbol}, strategy: {strategy_name}, test: {test}")
        self.logger.info("Iniciando estrategia...")

        self.client = Client(api_key=API_KEY, api_secret=API_SECRET, testnet=test)
        trade_strategy = ContextStrategy.get_strategy(strategy=strategy_name, binance_client=self.client, logger=self.logger)
        trade_executor = TradeExecutor(client=self.client, symbol=symbol, logger=self.logger, isMock=test)

        # Obtiene historial inicial sufiecient antes de arrancar el websocket
        df_hist = trade_strategy.obtener_historial_inicial(symbol, INTERVAL, period=50) 

        async with BinanceWebSocket(symbol, INTERVAL, self.logger) as bws:
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
                            self.logger.info(f"💥 Señal {modo} - Entry: {entry_price}, SL: {sl}, TP: {tp}")
                            # operaciones.append(
                            #     {
                            #         "symbol": symbol,
                            #         "strategy": strategy_name,
                            #         "modo": modo, 
                            #         "entry_price": entry_price, 
                            #         "sl": sl, 
                            #         "tp": tp, 
                            #         "qty": qty}
                            # )
                            # await self.notificar_entrada(operaciones)
                            # Implementar Trade Manager
                            resultado = trade_executor.place_order(mode=modo, entry_price=entry_price, sl_price=sl, tp_price=tp, quantity=qty)
                            # resultado = None
                            if resultado:
                                self.logger.info(f"Ordenes de compra y venta creadas: {resultado}")

                                entry = resultado['order']
                                if entry:
                                    self.logger.info(f"Orden de entrada creada: {entry}")
                                    # Aquí puedes manejar la orden de entrada si es necesario
                                    operaciones.append(
                                        {
                                            "tipo": "nuevo-trade",
                                            "symbol": symbol,
                                            "strategy": strategy_name,
                                            "orden": "ENTRY",
                                            "order_id": entry['orderId'],
                                            "price": entry['price'],
                                            "side": entry['side'],
                                            "status": entry['status'],
                                            "timestamp": candle['T'],
                                        }
                                    )

                                sl_order = resultado['sl_order']
                                if sl_order:
                                    self.logger.info(f"Orden de Stop Loss creada: {sl_order}")
                                    # Aquí puedes manejar la orden de Stop Loss si es 
                                    operaciones.append(
                                        {
                                            "tipo": "nuevo-trade",
                                            "symbol": symbol,
                                            "strategy": strategy_name,
                                            "orden": "STOP_LOSS",
                                            "order_id": sl_order['orderId'],
                                            "price": sl_order['stopPrice'],
                                            "side": sl_order['side'],
                                            "status": sl_order['status'],
                                            "timestamp": candle['T'],
                                        }
                                    )           

                                tp_order = resultado['tp_order']
                                if tp_order:
                                    self.logger.info(f"Orden de Take Profit creada: {tp_order}")
                                    # Aquí puedes manejar la orden de Take Profit si es necesario
                                    operaciones.append(
                                        {
                                            "tipo": "nuevo-trade",
                                            "symbol": symbol,
                                            "strategy": strategy_name,
                                            "orden": "TAKE_PROFIT",
                                            "order_id": tp_order['orderId'],
                                            "price": tp_order['price'],
                                            "side": tp_order['side'],
                                            "status": tp_order['status'],
                                            "timestamp": candle['T'],
                                        }
                                    )
                                
                                await self.notificar_entrada(operaciones)
                            else:
                                self.logger.error("Error al crear las órdenes de compra y venta.")
            except asyncio.CancelledError:
                self.logger.warn("⚠️ Estrategia cancelada por el usuario.""Tarea cancelada")
                raise
            except Exception as e:
                self.logger.exception(f"Error en el bucle principal: {e}")

    async def notificar_entrada(self, operaciones: dict):
        for operacion in operaciones:
            mensaje = dict(operacion)
            mensaje["type"] = "nuevo-trade"
            await ws_manager.broadcast(mensaje)

    def detener_estrategia(self, symbol, strategy_name):
        self.logger = logging.getLogger(f"{symbol}_{strategy_name}")
        self.logger.setLevel(logging.INFO)
        if symbol in tareas:
            loop, tread = tareas[symbol]
            task = self.task.get(symbol)

            if task:
                def cancel_task():
                    if not task.done():
                        task.cancel()
                        self.logger.info(f"Tarea cancelada para {symbol}")

                loop.call_soon_threadsafe(cancel_task)
            else:
                self.logger.info(f"No se encontró la tarea para {symbol}")

            tread.join()
            del tareas[symbol]
            self.task.pop(symbol, None)
            return f"Strategy {strategy_name} stopped for {symbol}"
        else:
            return f"No active strategy found for {symbol}"


    def get_symbols(self):
        exchange_info = self.client.futures_exchange_info()
        symbols = [symbol["symbol"] for symbol in exchange_info["symbols"] if symbol["status"] == "TRADING"]
        return sorted(symbols)

strategy_runner = StrategyRunner()

def get_operations():
    return operaciones