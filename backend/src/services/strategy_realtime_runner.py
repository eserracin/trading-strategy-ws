# src/services/strategy_runtime.py
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
from src.models.strategy_config import StrategyConfigParams # Importar el modelo
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import timedelta, timezone



APP_TZ = timezone(timedelta(hours=-5)) # UTC-5

logger = logging.getLogger("TRADING_BOT")

class StrategyRealTimeRunner:
    def __init__(self):
        self.task = {}
        self.client = Client(api_key=API_KEY, api_secret=API_SECRET)
        self.timeframe = INTERVAL
        self.operaciones = []

    def configure_runner(self, symbol, strategy_name, 
                          timeframe, start_date=None, end_date=None, 
                          period_days=None, db_session : Session = None, config_params_obj: Optional[StrategyConfigParams] = None):
        self.symbol = symbol
        self.strategy_name = strategy_name
        self.timeframe = timeframe
        self.start_date = start_date
        self.end_date = end_date
        self.period_days = period_days
        self.db_session = db_session
        self.config_params_obj = config_params_obj
    
    def iniciar_estrategia(self, test: bool = False):
        
        key = f"{self.symbol}_{self.strategy_name}"

        if key in self.task:
            _, thread = self.task[key]
            if thread.is_alive():
                logger.info(f"⚠️ La estrategia {self.strategy_name} ya está en ejecución para {self.symbol}")
                return f"La estrategia {self.strategy_name} ya está en ejecución para {self.symbol}"
            else:
                del self.task[key]

        thread = threading.Thread(target=self.__run_loop, args=(test,)) # Asegurar que args es una tupla
        thread.start()

        logger.info(f"🚀 Lanzando nueva estrategia: {key}, thread id: {thread.ident}")
        logger.info(f"🔎 Estado actual de tareas: {list(self.task.keys())}")

        # Guardamos el thread, pero aun no tenemos el loop
        self.task[key] = (None, thread)
        return f"Strategy {self.strategy_name} started for {self.symbol}"
    
    def __run_loop(self, test):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        self.task[f'{self.symbol}_{self.strategy_name}'] = (loop, threading.current_thread())
        task = loop.create_task(self._run_strategy(test))

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

    async def _run_strategy(self, test):
        logger.info("Iniciando estrategia...")

        trade_strategy = ContextStrategy.get_strategy(
                    strategy=self.strategy_name, 
                    binance_client=self.client,
                    db_session=self.db_session,
                    logger=logger)
        trade_executor = TradeExecutor(client=self.client, symbol=self.symbol, logger=logger, isMock=test)

        # Obtiene historial inicial sufiecient antes de arrancar el websocket
        logger.info(f"Llamando a obtener_historial_inicial_con_periodo con: symbol={self.symbol}, timeframe={self.timeframe}, period_days={self.period_days}")
        df_hist = trade_strategy.obtener_historial_inicial_con_periodo(self.symbol, self.timeframe, self.period_days)

        if df_hist is None or df_hist.empty:
            log_message = f"No se obtuvieron datos históricos para {self.symbol} con los parámetros dados."
            if df_hist is None:
                log_message = f"La obtención de datos históricos para {self.symbol} con los parámetros dados devolvió None."
            
            logger.warning(log_message)
            config_params_dump = self.config_params_obj.model_dump() if self.config_params_obj else {}
            return {"success": False, "error": "No se obtuvieron datos históricos.", "trades": [], "metrics": {}, "config_params": config_params_dump}

        try:
            async with BinanceWebSocket(self.symbol, self.timeframe, logger) as bws:
                async for kline in bws.klines_stream():
                    candle = kline["k"]

                    groupName = self.symbol + self.strategy_name + self.timeframe

                    # Siempre que recibimos nueva data, enviamos a clientes
                    await self.notificar_candle({
                        "symbol": self.symbol,
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

                        # 1. Guardar la vela cerrada en la base de datos KlinesCache
                        if hasattr(trade_strategy, 'save_realtime_kline_to_cache'):
                            # El método save_realtime_kline_to_cache usará su propia db_session
                            trade_strategy.save_realtime_kline_to_cache(
                                candle_data=candle, 
                                symbol=self.symbol, 
                                interval=self.timeframe # o candle_ws["i"]
                            )
                        else:
                            logger.warning(f"La estrategia {self.strategy_name} no tiene el método 'save_realtime_kline_to_cache'.")


                        # 2. Actualizar el DataFrame en memoria (df_hist)
                        # Convertir la vela del WebSocket al formato que usa tu DataFrame histórico.
                        # El df_hist de obtener_historial_inicial_con_periodo tiene el índice como datetime UTC-5
                        # y columnas 'Open', 'High', 'Low', 'Close', 'Volume', 'close_time'.

                        # El timestamp de la vela (open_time)
                        new_kline_timestamp_utc = pd.to_datetime(candle["t"], unit='ms', utc=True)
                        new_kline_timestamp_apptz = new_kline_timestamp_utc.tz_convert(APP_TZ) # UTC-5

                        # El close_time de la vela
                        new_kline_close_time_utc = pd.to_datetime(candle["T"], unit='ms', utc=True)
                        new_kline_close_time_apptz = new_kline_close_time_utc.tz_convert(APP_TZ)

                        nueva_fila_data = {
                            'Open': float(candle["o"]),
                            'High': float(candle["h"]),
                            'Low': float(candle["l"]),
                            'Close': float(candle["c"]),
                            'Volume': float(candle["v"]),
                            'close_time': new_kline_close_time_apptz
                        }

                        # Crear una nueva fila como DataFrame con el índice correcto
                        nueva_fila_df = pd.DataFrame([nueva_fila_data], index=[new_kline_timestamp_apptz])
                        nueva_fila_df.index.name = 'timestamp'

                        # Concatenar y mantener el tamaño del buffer
                        if not df_hist.empty:
                            if 'close_time' in df_hist.columns and not pd.api.types.is_datetime64_any_dtype(df_hist['close_time']):
                                df_hist['close_time'] = pd.to_datetime(df_hist['close_time'], errors='coerce')
                            if not pd.api.types.is_datetime64_any_dtype(nueva_fila_df['close_time']):
                                nueva_fila_df['close_time'] = pd.to_datetime(nueva_fila_df['close_time'], errors='coerce')

                            df_hist = pd.concat([df_hist, nueva_fila_df])
                        else:
                            df_hist = nueva_fila_df

                        min_required_candles = MIN_REQUIRED_CANDLES
                        if len(df_hist) > min_required_candles * 2: # Mantén un buffer un poco más grande para evitar recalculos constantes desde cero
                            df_hist = df_hist.iloc[-min_required_candles:]
                        
                        logger.debug(f"DataFrame actualizado. Última vela: {df_hist.index[-1]}, Close: {df_hist['Close'].iloc[-1]}. Tamaño: {len(df_hist)}")

                        # Calcualar indicadores
                        df_with_indicators = trade_strategy.calcular_indicadores(df_hist.copy(), params=self.config_params_obj)

                        if df_with_indicators.empty:
                            logger.warning("DataFrame vacío después de calcular indicadores. Saltando evaluación de entrada.")
                            continue

                        # 3. Evaluar la señal de entrada
                        signal_info = trade_strategy.check_signal_realtime(df_with_indicators, self.config_params_obj)

                        if signal_info and signal_info.get('mode'):
                            modo = signal_info['mode']
                            entry_price = signal_info['entry_price']
                            sl = signal_info['sl']
                            tp = signal_info['tp']

                            current_capital_for_sizing = self.config_params_obj.INITIAL_BALANCE

                            qty = trade_strategy.calculate_position_size(
                                capital=current_capital_for_sizing,
                                risk_percent_per_trade=self.config_params_obj.RISK_PERCENT_PER_TRADE,
                                entry_price=entry_price,
                                sl_price=sl,
                                min_position_size=self.config_params_obj.MIN_POSITION_SIZE
                            )

                            if qty > 0:
                                logger.info(f"💥 Señal {modo} - Entry: {entry_price}, SL: {sl}, TP: {tp}, Qty: {qty}")
                                resultado = await trade_executor.place_order_async( # Asumiendo que tienes un place_order_async
                                    mode=modo, 
                                    entry_price=entry_price, 
                                    sl_price=sl, 
                                    tp_price=tp, 
                                    quantity=qty
                                )
                                # ... resto de tu lógica de manejo de `resultado` y `operaciones` ...
                                if resultado:
                                    logger.info(f"Órdenes creadas: {resultado}")
                                    # Lógica de notificación y almacenamiento de `operaciones`
                                    # (tu código existente aquí)
                                    new_operations_list = [] # Para recolectar operaciones de este evento
                                    entry_order = resultado.get('order')
                                    if entry_order:
                                        op_data = {
                                            "tipo": "new-trade", "simbolo": self.symbol, "estrategia": self.strategy_name,
                                            "orden": "ENTRY", "orden_id": entry_order['orderId'], "precio": entry_order['price'],
                                            "quantity": entry_order['executedQty'], "side": entry_order['side'],
                                            "status": entry_order['status'], "timestamp": candle['T'],
                                        }
                                        self.operaciones.append(op_data)
                                        new_operations_list.append(op_data)

                                    sl_order_res = resultado.get('sl_order')
                                    if sl_order_res:
                                        op_data = {
                                            "tipo": "new-trade", "simbolo": self.symbol, "estrategia": self.strategy_name,
                                            "orden": "STOP_LOSS", "orden_id": sl_order_res['orderId'], "precio": sl_order_res['stopPrice'],
                                            "quantity": sl_order_res.get('origQty'), "side": sl_order_res['side'], # Ajusta quantity si es necesario
                                            "status": sl_order_res['status'], "timestamp": candle['T'],
                                        }
                                        self.operaciones.append(op_data)
                                        new_operations_list.append(op_data)

                                    tp_order_res = resultado.get('tp_order')
                                    if tp_order_res:
                                        op_data = {
                                            "tipo": "new-trade", "simbolo": self.symbol, "estrategia": self.strategy_name,
                                            "orden": "TAKE_PROFIT", "orden_id": tp_order_res['orderId'], "precio": tp_order_res['price'],
                                            "quantity": tp_order_res.get('origQty'), "side": tp_order_res['side'], # Ajusta quantity
                                            "status": tp_order_res['status'], "timestamp": candle['T'],
                                        }
                                        self.operaciones.append(op_data)
                                        new_operations_list.append(op_data)
                                    
                                    if new_operations_list: # Solo notificar si hubo nuevas operaciones
                                        await self.notificar_entrada(new_operations_list, "status") # Pasa solo las nuevas
                                else:
                                    logger.error(f"Error al crear las órdenes para {self.symbol} {modo}.")
                            else:
                                logger.info(f"Señal {modo} para {self.symbol} no generó una cantidad válida de posición (Qty: {qty}).")

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
        # logger.info(f"📊 Enviando candle a clientes: {mensaje}, en el grupo {group}")
        await ws_manager.broadcast(mensaje, group=group)

    def detener_estrategia(self, symbol, strategy_name):
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

        # loop.close()

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

strategy_runner = StrategyRealTimeRunner()

def get_operations():
    return strategy_runner.operaciones