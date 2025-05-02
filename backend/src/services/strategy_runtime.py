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
import signal

# Diccionario en memerioa para almacenar operaciones activas    
operaciones = []

logger = logging.getLogger("TRADING_BOT")

class StrategyRunner:
    def __init__(self):
        self.task = {}
        self.client = Client(api_key=API_KEY, api_secret=API_SECRET)
        self.timeframe = INTERVAL

    # def estrategias_disponibles(self):
    #     return list(ContextStrategy.STRATEGIES.keys())
    
    def iniciar_estrategia(self, symbol, strategy_name, timeframe, test=False):
        key = f"{symbol}_{strategy_name}"
        self.timeframe = timeframe
        if key in self.task:
            _, thread = self.task[key]
            if thread.is_alive():
                logger.info(f"⚠️ La estrategia {strategy_name} ya está en ejecución para {symbol}")
                return f"La estrategia {strategy_name} ya está en ejecución para {symbol}"
            else:
                del self.task[key]

        thread = threading.Thread(target=self.__run_loop, args=(symbol, strategy_name, test))
        thread.start()

        logger.info(f"🚀 Lanzando nueva estrategia: {key}, thread id: {thread.ident}")
        logger.info(f"🔎 Estado actual de tareas: {list(self.task.keys())}")

        # Guardamos el thread, pero aun no tenemos el loop
        self.task[key] = (None, thread)
        return f"Strategy {strategy_name} started for {symbol}"
    
    def __run_loop(self, symbol, strategy_name, test):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        self.task[f'{symbol}_{strategy_name}'] = (loop, threading.current_thread())
        task = loop.create_task(self._run_strategy(symbol, strategy_name, test))

        try:
            loop.run_until_complete(task)
        except asyncio.CancelledError:
            logger.info("Tarea cancelada")
        except Exception as e:
            logger.exception(f"Error en el bucle de eventos: {e}")
        finally:
            logger.info("Tarea finalizada")
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()

            logger.info("🔎 Loop cerrado correctamente.")

    async def _run_strategy(self, symbol, strategy_name, test):
        logger.info(f"symbol: {symbol}, strategy: {strategy_name}, test: {test}")
        logger.info("Iniciando estrategia...")

        self.client = Client(api_key=API_KEY, api_secret=API_SECRET, testnet=test)
        trade_strategy = ContextStrategy.get_strategy(strategy=strategy_name, binance_client=self.client, logger=logger)
        trade_executor = TradeExecutor(client=self.client, symbol=symbol, logger=logger, isMock=test)

        # Obtiene historial inicial sufiecient antes de arrancar el websocket
        df_hist = trade_strategy.obtener_historial_inicial(symbol, INTERVAL, period=50) 

        try:
            async with BinanceWebSocket(symbol, self.timeframe, logger) as bws:
                async for kline in bws.klines_stream():
                    candle = kline["k"]

                    groupName = symbol + strategy_name + self.timeframe

                    # Siempre que recibimos nueva data, enviamos a clientes
                    await self.notificar_candle({
                        "symbol": symbol,
                        "open_time": candle["t"],
                        "open": float(candle["o"]),
                        "high": float(candle["h"]),
                        "low": float(candle["l"]),
                        "close": float(candle["c"]),
                        "volume": float(candle["v"]),
                        "interval": candle["i"],
                        "close_time": candle["T"],
                    }, group=groupName)


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
                            # Implementar Trade Manager
                            resultado = trade_executor.place_order(mode=modo, entry_price=entry_price, sl_price=sl, tp_price=tp, quantity=qty)
                            # resultado = None
                            if resultado:
                                logger.info(f"Ordenes de compra y venta creadas: {resultado}")

                                entry = resultado['order']
                                if entry:
                                    logger.info(f"Orden de entrada creada: {entry}")
                                    # Aquí puedes manejar la orden de entrada si es necesario
                                    operaciones.append(
                                        {
                                            "tipo": "new-trade",
                                            "simbolo": symbol,
                                            "estrategia": strategy_name,
                                            "orden": "ENTRY",
                                            "orden_id": entry['orderId'],
                                            "precio": entry['price'],
                                            "quantity": entry['executedQty'],
                                            "side": entry['side'],
                                            "status": entry['status'],
                                            "timestamp": candle['T'],
                                        }
                                    )

                                sl_order = resultado['sl_order']
                                if sl_order:
                                    logger.info(f"Orden de Stop Loss creada: {sl_order}")
                                    # Aquí puedes manejar la orden de Stop Loss si es 
                                    operaciones.append(
                                        {
                                            "tipo": "new-trade",
                                            "simbolo": symbol,
                                            "estrategia": strategy_name,
                                            "orden": "STOP_LOSS",
                                            "orden_id": sl_order['orderId'],
                                            "precio": sl_order['stopPrice'],
                                            "side": sl_order['side'],
                                            "status": sl_order['status'],
                                            "timestamp": candle['T'],
                                        }
                                    )           

                                tp_order = resultado['tp_order']
                                if tp_order:
                                    logger.info(f"Orden de Take Profit creada: {tp_order}")
                                    # Aquí puedes manejar la orden de Take Profit si es necesario
                                    operaciones.append(
                                        {
                                            "tipo": "new-trade",
                                            "simbolo": symbol,
                                            "estrategia": strategy_name,
                                            "orden": "TAKE_PROFIT",
                                            "orden_id": tp_order['orderId'],
                                            "precio": tp_order['price'],
                                            "side": tp_order['side'],
                                            "status": tp_order['status'],
                                            "timestamp": candle['T'],
                                        }
                                    )
                                
                                await self.notificar_entrada(operaciones, "status")
                            else:
                                logger.error("Error al crear las órdenes de compra y venta.")
        except asyncio.CancelledError:
            await bws.close()
            logger.warn("⚠️ Estrategia cancelada por el usuario y WebSocket cerrado.")
            raise
        except Exception as e:
            logger.exception(f"Error en el bucle principal: {e}")

    async def notificar_entrada(self, operaciones: dict, group="status"):
        for operacion in operaciones:
            mensaje = dict(operacion)
            await ws_manager.broadcast(mensaje, group=group)

    async def notificar_candle(self, candle: dict, group="candles"):
        mensaje = {
            "tipo": "candle",
            "symbol": candle["symbol"],
            "open_time": candle["open_time"],
            "open": candle["open"],
            "high": candle["high"],
            "low": candle["low"],
            "close": candle["close"],
            "volume": candle["volume"],
            "interval": candle["interval"],
            "close_time": candle["close_time"]
        }
        # logger.info(f"📊 Enviando candle a clientes: {mensaje}")
        await ws_manager.broadcast(mensaje, group=group)

    def detener_estrategia(self, symbol, strategy_name, timeframe):
        import time

        key = f"{symbol}_{strategy_name}"
        if key not in self.task:
            logger.warning(f"⚠️ La estrategia {strategy_name} no está en ejecución para {symbol}")
            return f"La estrategia {strategy_name} no está en ejecución para {symbol}"
        

        loop, thread = self.task[key]

        async def cancelar_tareas():
            tasks = [t for t in asyncio.all_tasks(loop) if t is not asyncio.current_task(loop)]
            for task in tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.info(f"⛔ Tarea {task.get_name()} cancelada correctamente.")
            loop.stop()

        asyncio.run_coroutine_threadsafe(cancelar_tareas(), loop=loop)
        thread.join()

        loop.close()

        del self.task[key]

        logger.info(f"🔎 Estado actual de tareas: {list(self.task.keys())}")
        return f"Strategy {strategy_name} detenida para {symbol}"

    def detener_todas(self):
        for key in list(self.task.keys()):
            symbol, strategy_name = key.split("_", 1)
            self.detener_estrategia(symbol, strategy_name)

    def get_symbols(self):
        exchange_info = self.client.futures_exchange_info()
        symbols = [symbol["symbol"] for symbol in exchange_info["symbols"] if symbol["status"] == "TRADING"]
        return sorted(symbols)

strategy_runner = StrategyRunner()

def get_operations():
    return operaciones