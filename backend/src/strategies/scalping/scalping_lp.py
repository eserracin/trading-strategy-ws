# src/strategies/scalping/scalping_lp_v2.py
import pandas_ta as ta
import pandas as pd
from core import BaseStrategy
from datetime import timezone, timedelta, datetime # Añadir datetime
import logging
from sqlalchemy.orm import Session # Para type hinting
from sqlalchemy import select, text # Para consultas
from sqlalchemy.dialects.postgresql import insert # Para ON CONFLICT DO NOTHING

# Importar el modelo de KlinesCache
from database.models import KlinesCache # Ajusta la ruta si es necesario

APP_TZ = timezone(timedelta(hours=-5)) # UTC-5
DB_TZ = timezone.utc # UTC

class ScalpingStrategyLP(BaseStrategy):
    def __init__(self, binance_client, db_session: Session, logger=None): # db_session añadido
        self.client = binance_client
        self.db_session = db_session # Almacenar la sesión de BD
        self.logger = logger if logger else logging.getLogger(f"TRADING_BOT.{self.__class__.__name__}")
        if not self.logger.hasHandlers():
            self.logger.setLevel(logging.INFO)
            ch = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)
            self.logger.propagate = False

    def _klines_api_to_db_format(self, klines_api_data, symbol: str, interval: str):
        """
        Convierte klines de la API (lista de listas) a una lista de dicts para inserción en BD.
        Los timestamps se convierten a datetime UTC.
        """
        records_to_insert = []
        for kline in klines_api_data:
            records_to_insert.append({
                "symbol": symbol,
                "interval": interval,
                "timestamp": pd.to_datetime(kline[0], unit='ms', utc=True), # Almacenar como datetime UTC
                "open": float(kline[1]),
                "high": float(kline[2]),
                "low": float(kline[3]),
                "close": float(kline[4]),
                "volume": float(kline[5]),
            })
        return records_to_insert

    def _klines_db_to_api_format(self, klines_db_data):
        """
        Convierte klines de la BD (objetos KlinesCache) al formato de lista de listas esperado por _procesar_klines_a_dataframe.
        """
        # El timestamp en la BD ya es datetime UTC. Convertir a ms para _procesar_klines_a_dataframe
        return [
            [
                int(k.timestamp.replace(tzinfo=timezone.utc).timestamp() * 1000), # Convertir a ms UTC
                k.open,
                k.high,
                k.low,
                k.close,
                k.volume,
                int(k.timestamp.replace(tzinfo=timezone.utc).timestamp() * 1000 + pd.Timedelta(self.interval_to_timedelta(k.interval)).total_seconds() * 1000 -1) if k.interval else None, # close_time (aproximado)
                None, None, None, None, None # Otros campos que _procesar_klines_a_dataframe espera
            ] for k in klines_db_data
        ]

    def _kline_websocket_to_db_format(self, klines_ws_data: dict, symbol: str, interval: str):
        """
        Convierte una vela del WebSocket (formato dict) a un dict para inserción en BD.
        Los timestamps se convierten a datetime UTC.
        """
        # klines_ws_data["t"] es el open_time en ms
        # klines_ws_data["T"] es el close_time en ms
        return {
            "symbol": symbol,
            "interval": interval,
            "timestamp": pd.to_datetime(klines_ws_data["t"], unit='ms', utc=True), # Almacenar como datetime UTC
            "open": float(klines_ws_data["o"]),
            "high": float(klines_ws_data["h"]),
            "low": float(klines_ws_data["l"]),
            "close": float(klines_ws_data["c"]),
            "volume": float(klines_ws_data["v"]),
            # "close_time_ms": klines_ws_data["T"] # Opcional, si tu tabla tiene este campo
                                            # Nota: KlinesCache usa 'timestamp' como open_time
        }


    @staticmethod
    def interval_to_timedelta(interval_str: str) -> timedelta:
        """Convierte un string de intervalo (ej: '15m', '1h', '1d') a timedelta."""
        # Esta función es básica, expandir según los intervalos que uses.
        # Binance usa: m -> minutes; h -> hours; d -> days; w -> weeks; M -> months
        num = int(interval_str[:-1])
        unit = interval_str[-1]
        if unit == 'm':
            return timedelta(minutes=num)
        elif unit == 'h':
            return timedelta(hours=num)
        elif unit == 'd':
            return timedelta(days=num)
        elif unit == 'w':
            return timedelta(weeks=num)
        # Añadir más unidades si es necesario (M para meses es más complejo)
        else:
            raise ValueError(f"Intervalo no soportado para conversión a timedelta: {interval_str}")

    def save_realtime_kline_to_cache(self, candle_data: dict, symbol: str, interval: str):
        """
        Guarda una vela individual (recibida del WebSocket) en la KlinesCache.
        """
        if not self.db_session:
            self.logger.error("No hay sesión de base de datos disponible para guardar kline en caché.")
            return

        record_to_store = self._kline_websocket_to_db_format(candle_data, symbol, interval)

        if record_to_store:
            try:
                stmt = insert(KlinesCache).values(record_to_store)
                stmt = stmt.on_conflict_do_nothing(
                    index_elements=['symbol', 'interval', 'timestamp']
                )
                self.db_session.execute(stmt)
                self.db_session.commit()
                self.logger.debug(f"Vela en tiempo real para {symbol} ({interval}) guardada en caché. Timestamp: {record_to_store['timestamp']}")
            except Exception as e:
                self.db_session.rollback()
                self.logger.error(f"Error guardando vela en tiempo real en caché para {symbol} ({interval}): {e}", exc_info=True)

    def _fetch_data_with_cache(self, symbol: str, interval: str, start_dt_utc: datetime, end_dt_utc: datetime = None):
        """
        Función central para obtener klines, usando caché y fallback a API.
        start_dt_utc y end_dt_utc deben ser datetime objects timezone-aware (UTC).
        """

        if start_dt_utc.tzinfo is None or start_dt_utc.tzinfo.utcoffset(start_dt_utc) != timedelta(0):
            self.logger.error(f"start_dt_utc debe ser UTC y timezone-aware. Recibido: {start_dt_utc}")
            start_dt_utc = start_dt_utc.astimezone(timezone.utc) if start_dt_utc.tzinfo else start_dt_utc.replace(tzinfo=timezone.utc)

        # Define effective_end_dt_utc early and ensure it's UTC
        effective_end_dt_utc = end_dt_utc if end_dt_utc else datetime.now(timezone.utc)
        if isinstance(effective_end_dt_utc, datetime) and (effective_end_dt_utc.tzinfo is None or effective_end_dt_utc.tzinfo.utcoffset(effective_end_dt_utc) != timedelta(0)):
            effective_end_dt_utc = effective_end_dt_utc.astimezone(timezone.utc) if effective_end_dt_utc.tzinfo else effective_end_dt_utc.replace(tzinfo=timezone.utc)
        
        # self.logger.info(f"Solicitando datos para {symbol} ({interval}) entre {start_dt_utc} y {effective_end_dt_utc}")

        # 1. Intentar obtener de la BD (querying for the whole potential window from start_dt_utc)
        stmt = select(KlinesCache).where(
            KlinesCache.symbol == symbol,
            KlinesCache.interval == interval,
            KlinesCache.timestamp >= start_dt_utc # Get all cache from the start of our interest
        )
        # If end_dt_utc is provided, we can limit the initial query, but it might be better to get all from start_dt_utc
        # and then filter/use as needed, especially if we are fetching a tail.
        # For now, let's keep it simple: if end_dt_utc is specified, use it in the query.
        if end_dt_utc: # Original end_dt_utc, not effective_end_dt_utc for this initial DB query
            stmt = stmt.where(KlinesCache.timestamp <= end_dt_utc) 
        
        stmt = stmt.order_by(KlinesCache.timestamp)
        cached_klines_db_objects = self.db_session.execute(stmt).scalars().all()

        interval_td = None
        try:
            interval_td = self.interval_to_timedelta(interval)
        except ValueError:
            self.logger.warning(f"No se pudo convertir el intervalo {interval} a timedelta. La lógica de caché optimizada se saltará; se podría recurrir a un full fetch de API.")
            # Proceeding without interval_td means we can't accurately check end_covered or density.

        if cached_klines_db_objects and interval_td: # interval_td is crucial for this advanced cache logic
            first_cached_ts_in_results = cached_klines_db_objects[0].timestamp
            if first_cached_ts_in_results.tzinfo is None: first_cached_ts_in_results = first_cached_ts_in_results.replace(tzinfo=timezone.utc)
            else: first_cached_ts_in_results = first_cached_ts_in_results.astimezone(timezone.utc)

            last_cached_ts_in_results = cached_klines_db_objects[-1].timestamp
            if last_cached_ts_in_results.tzinfo is None: last_cached_ts_in_results = last_cached_ts_in_results.replace(tzinfo=timezone.utc)
            else: last_cached_ts_in_results = last_cached_ts_in_results.astimezone(timezone.utc)

            start_covered_by_cache = first_cached_ts_in_results <= start_dt_utc
            end_covered_by_cache = (last_cached_ts_in_results + interval_td) >= effective_end_dt_utc
            
            expected_candles = 0
            if start_dt_utc < effective_end_dt_utc:
                 expected_candles = (effective_end_dt_utc - start_dt_utc) / interval_td
            
            # Density check considers all items returned by the query (>= start_dt_utc)
            # This might overestimate density if cache extends far beyond effective_end_dt_utc,
            # but it's a pragmatic check.
            cache_is_dense_enough = len(cached_klines_db_objects) >= expected_candles * 0.95

            self.logger.info(f"***DEBUG CACHE CHECK (MODIFICADO)***")
            self.logger.info(f"Rango Solicitado (UTC): {start_dt_utc} a {effective_end_dt_utc}")
            self.logger.info(f"Primer TS Cacheado en resultados (UTC): {first_cached_ts_in_results}")
            self.logger.info(f"Último TS Cacheado en resultados (UTC): {last_cached_ts_in_results}")
            self.logger.info(f"Último TS Cacheado + Intervalo (UTC): {last_cached_ts_in_results + interval_td}")
            self.logger.info(f"Start Covered: {start_covered_by_cache}, End Covered: {end_covered_by_cache}, Dense Enough: {cache_is_dense_enough} (Esperadas ~{int(expected_candles)}, Encontradas {len(cached_klines_db_objects)})")

            if start_covered_by_cache and end_covered_by_cache and cache_is_dense_enough:
                self.logger.info(f"Cache HIT TOTAL para {symbol} {interval}. Rango: {start_dt_utc} a {effective_end_dt_utc}.")
                # Filter cached_klines_db_objects to only those strictly within [start_dt_utc, effective_end_dt_utc] if needed,
                # or let _procesar_klines_a_dataframe handle it.
                # For now, pass all results from query; _procesar_klines_a_dataframe will set index and select columns.
                klines_for_df = self._klines_db_to_api_format(cached_klines_db_objects)
                return self._procesar_klines_a_dataframe(klines_for_df, interval_str=interval)

            elif start_covered_by_cache and not end_covered_by_cache: # Cache covers start, but not the end. Fetch the tail.
                self.logger.info(f"Cache PARCIAL (gap al final) para {symbol} {interval}. Obteniendo datos faltantes (tail) de API...")
                api_fetch_start_dt_for_tail = last_cached_ts_in_results + interval_td
                
                if api_fetch_start_dt_for_tail < effective_end_dt_utc:
                    start_str_api_tail = api_fetch_start_dt_for_tail.strftime("%d %b, %Y %H:%M:%S")
                    end_str_api_tail = effective_end_dt_utc.strftime("%d %b, %Y %H:%M:%S")
                    
                    self.logger.info(f"Obteniendo tail de API: Desde {start_str_api_tail} hasta {end_str_api_tail}")
                    api_klines_tail_raw = []
                    try:
                        api_klines_tail_raw = self.client.get_historical_klines(symbol, interval, start_str_api_tail, end_str_api_tail)
                    except Exception as e:
                        self.logger.error(f"Error obteniendo tail de klines de API para {symbol} {interval}: {e}", exc_info=True)
                        self.logger.warning("Usando datos de caché existentes (sin tail) debido a fallo de API al obtener el gap.")
                        klines_for_df = self._klines_db_to_api_format(cached_klines_db_objects) # Use all results from initial query
                        return self._procesar_klines_a_dataframe(klines_for_df, interval_str=interval)

                    if api_klines_tail_raw:
                        self.logger.info(f"Tail de {len(api_klines_tail_raw)} klines obtenido de API.")
                        records_to_store_tail = self._klines_api_to_db_format(api_klines_tail_raw, symbol, interval)
                        if records_to_store_tail:
                            try:
                                stmt_tail = insert(KlinesCache).values(records_to_store_tail)
                                stmt_tail = stmt_tail.on_conflict_do_nothing(index_elements=['symbol', 'interval', 'timestamp'])
                                self.db_session.execute(stmt_tail)
                                self.db_session.commit()
                                self.logger.info(f"Guardados {len(records_to_store_tail)} klines del tail en caché.")
                            except Exception as e:
                                self.db_session.rollback()
                                self.logger.error(f"Error guardando klines del tail en caché: {e}", exc_info=True)
                        
                        # Combine all cached data from initial query (which starts at start_dt_utc) with the new tail
                        combined_klines_raw = self._klines_db_to_api_format(cached_klines_db_objects) + api_klines_tail_raw
                        # _procesar_klines_a_dataframe will handle potential duplicates by timestamp due to its set_index logic
                        return self._procesar_klines_a_dataframe(combined_klines_raw, interval_str=interval)
                    else: # API tail fetch returned no data
                        self.logger.info("No se obtuvieron datos del tail de la API. Usando datos de caché existentes.")
                        klines_for_df = self._klines_db_to_api_format(cached_klines_db_objects)
                        return self._procesar_klines_a_dataframe(klines_for_df, interval_str=interval)
                else: # Cache is already up-to-date (last_cached_ts + interval_td >= effective_end_dt_utc)
                    self.logger.info("Cache ya está actualizado hasta el final del rango solicitado (o más allá). No se necesita fetch de tail.")
                    klines_for_df = self._klines_db_to_api_format(cached_klines_db_objects)
                    return self._procesar_klines_a_dataframe(klines_for_df, interval_str=interval)
            else: # Cache does not cover start, or other unhandled partial cache scenario (e.g., very gappy despite start_covered)
                self.logger.info(f"Cache no cubre el inicio del rango ({start_dt_utc} vs {first_cached_ts_in_results}), o es insuficiente de otra manera. Se procederá a un full fetch para el rango solicitado.")
                # Fall through to full API fetch logic below
        
        # Fallback: Cache MISS, INCOMPLETO de forma no manejable por la lógica anterior, o interval_td no disponible.
        self.logger.info(f"Cache MISS o INCOMPLETO para {symbol} ({interval}). Obteniendo rango completo de API de Binance: {start_dt_utc} a {effective_end_dt_utc}")
        
        start_str_api = start_dt_utc.strftime("%d %b, %Y %H:%M:%S")
        end_str_api = effective_end_dt_utc.strftime("%d %b, %Y %H:%M:%S") if effective_end_dt_utc else None # API client might handle None as "most recent"

        api_klines_raw = []
        try:
            api_klines_raw = self.client.get_historical_klines(symbol, interval, start_str_api, end_str_api)
        except Exception as e:
            self.logger.error(f"Error obteniendo klines de API para {symbol} {interval}: {e}", exc_info=True)
            if cached_klines_db_objects: # Fallback to any cache we might have queried initially
                self.logger.warning("Usando datos de caché (posiblemente incompletos) debido a fallo de API en full fetch.")
                klines_for_df = self._klines_db_to_api_format(cached_klines_db_objects)
                return self._procesar_klines_a_dataframe(klines_for_df, interval_str=interval)
            return pd.DataFrame() # No cache and API failed

        if not api_klines_raw:
            self.logger.warning(f"No se obtuvieron datos de API para {symbol} {interval} en el rango {start_str_api} - {end_str_api}.")
            if cached_klines_db_objects: # Fallback to any cache we might have queried initially
                 self.logger.warning("API no devolvió datos en full fetch, usando datos de caché existentes.")
                 klines_for_df = self._klines_db_to_api_format(cached_klines_db_objects)
                 return self._procesar_klines_a_dataframe(klines_for_df, interval_str=interval)
            return pd.DataFrame() # No cache and API returned empty

        # 3. Guardar los datos obtenidos de la API (full fetch) en la BD
        records_to_store = self._klines_api_to_db_format(api_klines_raw, symbol, interval)
        if records_to_store:
            try:
                stmt = insert(KlinesCache).values(records_to_store)
                stmt = stmt.on_conflict_do_nothing(
                    index_elements=['symbol', 'interval', 'timestamp']
                )
                self.db_session.execute(stmt)
                self.db_session.commit()
                self.logger.info(f"Guardados/actualizados {len(records_to_store)} klines en caché para {symbol} ({interval}).")
            except Exception as e:
                self.db_session.rollback()
                self.logger.error(f"Error guardando klines en caché para {symbol} ({interval}): {e}", exc_info=True)
        
        return self._procesar_klines_a_dataframe(api_klines_raw, interval_str=interval)

    def _procesar_klines_a_dataframe(self, klines, interval_str: str = None): # Añadir interval_str
        """
        Convierte la respuesta de klines de la API (o datos de BD formateados como API) a un DataFrame.
        interval_str es necesario para la conversión de close_time si se usa.
        """
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time',
            'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume',
            'taker_buy_quote_asset_volume', 'ignore'
        ])
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df.rename(columns={
            'open': 'Open', 'high': 'High', 'low': 'Low',
            'close': 'Close', 'volume': 'Volume'
        }, inplace=True)
        
        # Timestamp ya debería ser ms UTC si viene de _klines_db_to_api_format
        # O es ms UTC si viene directamente de la API
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
        df.set_index('timestamp', inplace=True)

        # Convertir close_time. Si no está (datos de BD podrían no tenerlo exactamente), calcularlo.
        if 'close_time' not in df.columns or df['close_time'].isnull().all():
            if interval_str:
                try:
                    interval_delta = self.interval_to_timedelta(interval_str)
                    # close_time es el timestamp de la siguiente vela - 1ms, o timestamp + duracion_intervalo - 1ms
                    df['close_time'] = df.index.map(lambda ts: ts + interval_delta - timedelta(milliseconds=1))
                except ValueError as e:
                    self.logger.warning(f"No se pudo calcular close_time: {e}. Columna close_time podría faltar o ser NaT.")
                    df['close_time'] = pd.NaT # Asignar NaT si no se puede calcular
            else:
                 self.logger.warning("No se proporcionó interval_str a _procesar_klines_a_dataframe, no se puede calcular close_time.")
                 df['close_time'] = pd.NaT
        else:
            df['close_time'] = pd.to_datetime(df['close_time'], unit='ms', utc=True)


        target_tz_datetime = timezone(timedelta(hours=-5))
        df.index = df.index.tz_convert(target_tz_datetime)

        if 'close_time' in df.columns and pd.api.types.is_datetime64_any_dtype(df['close_time']):
            df['close_time'] = df['close_time'].dt.tz_convert(target_tz_datetime)

        return df[['Open', 'High', 'Low', 'Close', 'Volume', 'close_time']].dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])

    def obtener_historial_inicial_con_periodo(self, symbol, interval='15m', period_days=50):
        """
        Obtiene datos históricos de klines para un símbolo y un período de días hacia atrás.
        """
        # Calcular las fechas UTC para la consulta
        end_dt_utc = datetime.now(timezone.utc)
        start_dt_utc = end_dt_utc - timedelta(days=period_days)

        self.logger.info(f"***** Solicitando historial para {symbol} desde {start_dt_utc} hasta {end_dt_utc} (intervalo {interval}) usando _fetch_data_with_cache...")

        df_historical = self._fetch_data_with_cache(
                symbol=symbol,
                interval=interval,
                start_dt_utc=start_dt_utc,
                end_dt_utc=end_dt_utc # _fetch_data_with_cache manejará end_dt_utc como "ahora" si es necesario
            )
        
        if df_historical.empty:
            self.logger.warning(f"No se obtuvieron datos históricos para {symbol} ({period_days} días atrás, intervalo {interval}).")

        return df_historical

    def obtener_historial_inicial_con_rango(self, symbol, interval='15m', startDate=None, endDate=None):
        """
        Obtiene datos históricos de klines para un símbolo dentro de un rango de fechas.
        """
        try:
            if isinstance(startDate, str):
                try:
                    # Intenta parsear con hora, si falla, solo fecha
                    start_dt_utc_query = datetime.strptime(startDate, "%Y-%m-%d %H:%M:%S").replace(tzinfo=APP_TZ)
                except ValueError:
                    start_dt_utc_query = datetime.strptime(startDate, "%Y-%m-%d").replace(tzinfo=APP_TZ)
            elif isinstance(startDate, datetime):
                start_dt_utc_query = startDate if startDate.tzinfo else startDate.replace(tzinfo=APP_TZ)
            else:
                # Considerar un default o error si startDate es None o tipo incorrecto
                self.logger.error("startDate es None o tipo incorrecto, no se puede proceder.")
                return pd.DataFrame() # O lanzar error
            
            if endDate:
                if isinstance(endDate, str):
                    try:
                        end_dt_utc_query = datetime.strptime(endDate, "%Y-%m-%d %H:%M:%S").replace(tzinfo=APP_TZ)
                    except ValueError:
                        # Si es solo fecha, tomar hasta el final de ese día
                        parse_date_only = datetime.strptime(endDate, "%Y-%m-%d")
                        end_dt_utc_query = datetime.combine(parse_date_only, datetime.max.time()).replace(tzinfo=APP_TZ)
                elif isinstance(endDate, datetime):
                    end_dt_utc_query = endDate if endDate.tzinfo else endDate.replace(tzinfo=APP_TZ)
                else:
                    self.logger.error("endDate es de tipo incorrecto.")
                    return pd.DataFrame() # O lanzar error
            else:
                end_dt_utc_query = datetime.now(timezone.utc) # Hasta ahora si endDate no se provee
                
        except ValueError as e:
            self.logger.error(f"Error parseando fechas para rango: {e}. startDate='{startDate}', endDate='{endDate}'")
            return pd.DataFrame()

        self.logger.info(f"***** Solicitando historial para {symbol} desde {start_dt_utc_query} hasta {end_dt_utc_query} (intervalo {interval}) usando _fetch_data_with_cache...")

        df_historical = self._fetch_data_with_cache(
            symbol=symbol,
            interval=interval,
            start_dt_utc=start_dt_utc_query,
            end_dt_utc=end_dt_utc_query
        )

        if df_historical.empty:
            self.logger.warning(f"No se pudieron obtener datos (ni de caché ni de API) para {symbol} ({interval}) con rango {startDate}-{endDate}.")
            
        return df_historical
    


    def calcular_indicadores(self, df: pd.DataFrame, params: dict) -> pd.DataFrame:
        """
        Calcula y añade los indicadores técnicos necesarios al DataFrame,
        utilizando los parámetros proporcionados.
        """
        if df.empty:
            self.logger.warning("DataFrame vacío recibido en calcular_indicadores. No se calcularán indicadores.")
            return df 
        
        self.logger.info("Calculando indicadores técnicos con parámetros específicos...")
        
        # Parámetros de indicadores
        atr_len = params['ATR_LEN']
        breakout_window = params.get('BREAKOUT_WINDOW', 5) # Default si no está en params
        ema_daily_len = params['EMA_DAILY_LEN']
        ema_long_len = params['EMA_LONG_LEN']
        ema_short_len = params['EMA_SHORT_LEN']
        ema_trend_filter_len = params.get('EMA_TREND_FILTER_LEN') # Puede ser None
        rsi_len = params['RSI_LEN']
        vol_sma_len = params['VOL_SMA_LEN']
              
        
        # Parámetros adicionales que definiste en StrategyConfigParams (con defaults si son Optional)
        vol_sma_multiplier = params.get('VOL_SMA_MULTIPLIER', 1.5)
        rsi_buy_threshold = params.get('RSI_BUY_THRESHOLD', 60)
        rsi_sell_threshold = params.get('RSI_SELL_THRESHOLD', 40)

        try:
            df.ta.ema(close='Close', length=ema_short_len, append=True, col_names=(f'EMA_{ema_short_len}',))
            df.ta.ema(close='Close', length=ema_long_len, append=True, col_names=(f'EMA_{ema_long_len}',))
            df.ta.rsi(close='Close', length=rsi_len, append=True, col_names=(f'RSI_{rsi_len}',))
            df.ta.sma(close='Volume', length=vol_sma_len, append=True, col_names=(f'VOL_SMA_{vol_sma_len}',))
            df.ta.atr(length=atr_len, append=True, col_names=(f'ATR_{atr_len}',))
            if ema_trend_filter_len: # Solo calcular si se proporciona y es > 0
                 df.ta.ema(close='Close', length=ema_trend_filter_len, append=True, col_names=(f'EMA_TF_{ema_trend_filter_len}',))
        except Exception as e:
             self.logger.error(f"Error calculando indicadores base: {e}", exc_info=True)
             raise

        # Filtro de Tendencia Marco Diario
        if not df['Close'].empty: # Asegurar que hay datos para resamplear
            daily_close = df['Close'].resample('D').last()
            if not daily_close.empty:
                ema_daily_series = ta.ema(daily_close, length=ema_daily_len)
                ema_daily_col_name = f'EMA_D_{ema_daily_len}'
                df[ema_daily_col_name] = ema_daily_series.reindex(df.index, method='ffill')
                df[ema_daily_col_name].bfill(inplace=True) 
                df['ema_daily_rising_3'] = (df[ema_daily_col_name] > df[ema_daily_col_name].shift(3)).fillna(False)
                df['ema_daily_falling_3'] = (df[ema_daily_col_name] < df[ema_daily_col_name].shift(3)).fillna(False) 
                df['permitido_long_diario'] = (df['Close'] > df[ema_daily_col_name]) & df['ema_daily_rising_3']
                df['permitido_short_diario'] = (df['Close'] < df[ema_daily_col_name]) & df['ema_daily_falling_3']
            else: # Si daily_close es vacío
                self.logger.warning("No hay suficientes datos para resamplear a diario y calcular EMA diaria.")
                for col in [f'EMA_D_{ema_daily_len}', 'ema_daily_rising_3', 'ema_daily_falling_3', 'permitido_long_diario', 'permitido_short_diario']:
                    df[col] = False # o pd.NA
        else: # Si df['Close'] es vacío
            self.logger.warning("Columna 'Close' vacía, no se puede calcular EMA diaria.")
            for col in [f'EMA_D_{ema_daily_len}', 'ema_daily_rising_3', 'ema_daily_falling_3', 'permitido_long_diario', 'permitido_short_diario']:
                df[col] = False # o pd.NA

        # Detección de Velas y Breakouts
        df['vela_alcista'] = df['Close'] > df['Open']
        df['vela_bajista'] = df['Close'] < df['Open']

        df[f'highest_prev_{breakout_window}_high'] = df['High'].shift(1).rolling(window=breakout_window, min_periods=max(1, breakout_window)).max() # min_periods=1 si breakout_window es pequeño
        df[f'lowest_prev_{breakout_window}_low'] = df['Low'].shift(1).rolling(window=breakout_window, min_periods=max(1, breakout_window)).min()
        df['breakout_alcista'] = (df['High'] > df[f'highest_prev_{breakout_window}_high']) & (df['Close'] > df[f'highest_prev_{breakout_window}_high'])
        df['breakout_bajista'] = (df['Low'] < df[f'lowest_prev_{breakout_window}_low']) & (df['Close'] < df[f'lowest_prev_{breakout_window}_low'])

        # Cruces y Volumen
        df[f'ema_cruce_alcista'] = (df[f'EMA_{ema_short_len}'] > df[f'EMA_{ema_long_len}']) & \
                                  (df[f'EMA_{ema_short_len}'].shift(1) <= df[f'EMA_{ema_long_len}'].shift(1))
        df[f'ema_cruce_bajista'] = (df[f'EMA_{ema_short_len}'] < df[f'EMA_{ema_long_len}']) & \
                                   (df[f'EMA_{ema_short_len}'].shift(1) >= df[f'EMA_{ema_long_len}'].shift(1))
        df['volumen_ok'] = df['Volume'] > (df[f'VOL_SMA_{vol_sma_len}'] * vol_sma_multiplier)

        # Combinar Condiciones Finales
        # Crear columnas base aunque estén vacías para evitar KeyErrors
        df['permitido_long_diario'] = df.get('permitido_long_diario', pd.Series(False, index=df.index))
        df['permitido_short_diario'] = df.get('permitido_short_diario', pd.Series(False, index=df.index))

        base_cond_long = (df[f'ema_cruce_alcista'] & \
                          df['breakout_alcista'] & \
                          df['volumen_ok'] & \
                          (df.get(f'RSI_{rsi_len}', pd.Series(0, index=df.index)) > rsi_buy_threshold) & \
                          df['vela_alcista'] & \
                          df['permitido_long_diario'])

        base_cond_short = (df[f'ema_cruce_bajista'] & \
                           df['breakout_bajista'] & \
                           df['volumen_ok'] & \
                           (df.get(f'RSI_{rsi_len}', pd.Series(100, index=df.index)) < rsi_sell_threshold) & \
                           df['vela_bajista'] & \
                           df['permitido_short_diario'])

        if ema_trend_filter_len and f'EMA_TF_{ema_trend_filter_len}' in df.columns:
            df['condicion_long'] = base_cond_long & (df['Close'] > df[f'EMA_TF_{ema_trend_filter_len}'])
            df['condicion_short'] = base_cond_short & (df['Close'] < df[f'EMA_TF_{ema_trend_filter_len}'])
        else:
            df['condicion_long'] = base_cond_long
            df['condicion_short'] = base_cond_short
        
        cols_condiciones = ['condicion_long', 'condicion_short', 'breakout_alcista', 'breakout_bajista',
                            f'ema_cruce_alcista', f'ema_cruce_bajista'] 
        cols_condiciones.extend([f'highest_prev_{breakout_window}_high', f'lowest_prev_{breakout_window}_low'])
        
        for col in cols_condiciones:
            if col in df.columns:
                 if df[col].dtype == 'bool': 
                      df[col].fillna(False, inplace=True)
            else: # Si la columna no existe (p.ej. por df vacío o pocos datos), crearla como False
                 df[col] = False


        self.logger.info("Cálculo de indicadores completado.")
        # df.dropna() puede eliminar todas las filas si hay pocos datos iniciales.
        # Considerar si esto es deseable o si se deben manejar NaNs de otra forma.
        # Por ahora, mantenemos el dropna() pero con la conciencia de que puede vaciar el df.
        return df.dropna()

    def check_entry(self, df: pd.DataFrame, params: dict):
        """
        Ejecuta el backtesting de la estrategia sobre los datos históricos con indicadores,
        utilizando los parámetros proporcionados.
        """
        if df.empty:
            self.logger.warning("DataFrame vacío recibido en check_entry. No se realizará backtesting.")
            return [], params.get('INITIAL_BALANCE', 0) # Devuelve lista de trades vacía y capital inicial

        self.logger.info("Iniciando backtest (check_entry) con parámetros específicos...")
        
        initial_balance = params['INITIAL_BALANCE']
        risk_percent_per_trade = params['RISK_PERCENT_PER_TRADE']
        atr_multiplier_sl = params['ATR_MULTIPLIER_SL']
        rr_factor_tp = params['RR_FACTOR_TP']
        min_bars_entre_trades = params['MIN_BARS_ENTRE_TRADES']
        min_position_size = params['MIN_POSITION_SIZE']
        atr_len = params['ATR_LEN'] 
        
        capital = initial_balance
        trades = []
        active_trade = None
        last_entry_bar_iloc = -(min_bars_entre_trades + 1) 

        atr_col_name = f'ATR_{atr_len}'
        if atr_col_name not in df.columns:
            self.logger.error(f"Columna ATR '{atr_col_name}' no encontrada. SL/TP dinámico fallará.")
            return trades, capital 
        
        condicion_long_col = 'condicion_long'
        condicion_short_col = 'condicion_short'
        if condicion_long_col not in df.columns or condicion_short_col not in df.columns:
            self.logger.error("Columnas de condición ('condicion_long' o 'condicion_short') no encontradas.")
            return trades, capital

        for i in range(len(df)):
            current_bar = df.iloc[i]
            current_bar_timestamp = df.index[i]

            if capital <= 0: 
                self.logger.warning(f"Capital insuficiente ({capital:.2f}) para continuar operando en {current_bar_timestamp}. Deteniendo backtest.")
                break 

            if active_trade:
                pnl = 0
                exit_price = None
                exit_reason = ""
                if active_trade['type'] == 'long':
                    if current_bar['Low'] <= active_trade['sl']:
                        exit_price = active_trade['sl']
                        exit_reason = "SL"
                    elif current_bar['High'] >= active_trade['tp']:
                        exit_price = active_trade['tp']
                        exit_reason = "TP"
                elif active_trade['type'] == 'short':
                    if current_bar['High'] >= active_trade['sl']:
                        exit_price = active_trade['sl']
                        exit_reason = "SL"
                    elif current_bar['Low'] <= active_trade['tp']:
                        exit_price = active_trade['tp']
                        exit_reason = "TP"

                if exit_price is not None:
                    if active_trade['type'] == 'long':
                        pnl = (exit_price - active_trade['entry_price']) * active_trade['size']
                    else: # short
                        pnl = (active_trade['entry_price'] - exit_price) * active_trade['size']
                    capital += pnl
                    capital = round(capital, 8) 
                    trades.append({
                        'entry_time': active_trade['entry_time'],
                        'exit_time': current_bar_timestamp,
                        'type': active_trade['type'],
                        'entry_price': active_trade['entry_price'],
                        'exit_price': exit_price,
                        'sl': active_trade['sl'],
                        'tp': active_trade['tp'],
                        'size': active_trade['size'],
                        'pnl': pnl,
                        'capital_after_trade': capital,
                        'exit_reason': exit_reason
                    })
                    active_trade = None

            if not active_trade:
                puede_entrar_por_frecuencia = (i - last_entry_bar_iloc) > min_bars_entre_trades
                
                entry_price_candidate = current_bar['Close']
                sl_price_candidate = None
                tp_price_candidate = None
                trade_type_candidate = None

                current_atr = current_bar.get(atr_col_name) 
                if pd.isna(current_atr) or current_atr <= 1e-9: 
                    if puede_entrar_por_frecuencia and (current_bar.get(condicion_long_col, False) or current_bar.get(condicion_short_col, False)):
                        self.logger.debug(f"Skipping trade at {current_bar_timestamp} due to invalid ATR: {current_atr}")
                    continue 

                sl_distance_atr = current_atr * atr_multiplier_sl 
                
                if current_bar.get(condicion_long_col, False) and puede_entrar_por_frecuencia:
                    trade_type_candidate = "long"
                    sl_price_candidate = entry_price_candidate - sl_distance_atr
                    tp_price_candidate = entry_price_candidate + (sl_distance_atr * rr_factor_tp)
                elif current_bar.get(condicion_short_col, False) and puede_entrar_por_frecuencia:
                    trade_type_candidate = "short"
                    sl_price_candidate = entry_price_candidate + sl_distance_atr
                    tp_price_candidate = entry_price_candidate - (sl_distance_atr * rr_factor_tp)

                if trade_type_candidate:
                    riesgo_maximo_permitido_en_capital = capital * risk_percent_per_trade
                    riesgo_por_unidad_de_activo = abs(entry_price_candidate - sl_price_candidate) if sl_price_candidate is not None else float('inf')
                    
                    position_size = 0
                    if riesgo_por_unidad_de_activo > 1e-9: 
                        position_size = riesgo_maximo_permitido_en_capital / riesgo_por_unidad_de_activo
                    
                    sl_tp_valido = False
                    if trade_type_candidate == "long" and sl_price_candidate is not None and tp_price_candidate is not None and \
                       sl_price_candidate < entry_price_candidate and tp_price_candidate > entry_price_candidate:
                        sl_tp_valido = True
                    elif trade_type_candidate == "short" and sl_price_candidate is not None and tp_price_candidate is not None and \
                         sl_price_candidate > entry_price_candidate and tp_price_candidate < entry_price_candidate:
                        sl_tp_valido = True
                    
                    entrada_valida = position_size >= min_position_size and sl_tp_valido

                    if entrada_valida:
                        active_trade = {
                            'entry_time': current_bar_timestamp,
                            'type': trade_type_candidate,
                            'entry_price': entry_price_candidate,
                            'sl': sl_price_candidate,
                            'tp': tp_price_candidate,
                            'size': position_size
                        }
                        last_entry_bar_iloc = i 

        if active_trade: 
            last_bar = df.iloc[-1]
            last_close_price = last_bar['Close']
            last_bar_timestamp = df.index[-1]
            pnl = 0
            if active_trade['type'] == 'long':
                pnl = (last_close_price - active_trade['entry_price']) * active_trade['size']
            else: # short
                pnl = (active_trade['entry_price'] - last_close_price) * active_trade['size']
            capital += pnl
            capital = round(capital, 8)
            trades.append({
                'entry_time': active_trade['entry_time'],
                'exit_time': last_bar_timestamp,
                'type': active_trade['type'],
                'entry_price': active_trade['entry_price'],
                'exit_price': last_close_price,
                'sl': active_trade['sl'],
                'tp': active_trade['tp'],
                'size': active_trade['size'],
                'pnl': pnl,
                'capital_after_trade': capital,
                'exit_reason': "End of Data"
            })

        self.logger.info(f"\nBacktest Finalizado. Capital Inicial: ${initial_balance:.2f}, Capital Final: ${capital:.2f}") 
        if trades:
            self.logger.info(f"Total trades: {len(trades)}")
        else:
            self.logger.info("No se realizaron trades.")
            
        return trades, capital 

    def check_signal_realtime(self, df_with_indicators: pd.DataFrame, params: dict):
        """
        Verifica si hay señales de trading en tiempo real.
        """
        if df_with_indicators.empty:
            self.logger.warning("DataFrame vacío recibido en check_signal_realtime. No se verificará señal.")
            return None, None

        self.logger.info("Verificando señales en tiempo real...")

        last_bar = df_with_indicators.iloc[-1] # La vela más reciente con todos los indicadores calculados

        # Parámetros necesarios para la decisión y SL/TP
        atr_len = params['ATR_LEN']
        atr_multiplier_sl = params['ATR_MULTIPLIER_SL']
        rr_factor_tp = params['RR_FACTOR_TP']
        # min_bars_entre_trades = params['MIN_BARS_ENTRE_TRADES'] # Lógica de frecuencia de trade debe manejarse externamente
                                                                # o con estado persistente en la estrategia

        atr_col_name = f'ATR_{atr_len}'
        if atr_col_name not in last_bar or pd.isna(last_bar[atr_col_name]) or last_bar[atr_col_name] <= 1e-9:
            self.logger.debug(f"ATR inválido ({last_bar.get(atr_col_name)}) en la última vela. No hay señal.")
            return None
        
        entry_price = last_bar['Close'] # O podrías usar el precio de apertura de la siguiente vela si esperas confirmación
        sl_distance_atr = last_bar[atr_col_name] * atr_multiplier_sl

        signal_info = {'mode': None, 'entry_price': None, 'sl': None, 'tp': None}

        # Verificar condiciones LONG
        if 'condicion_long' in last_bar and last_bar['condicion_long']:
            signal_info['mode'] = "long"
            signal_info['entry_price'] = entry_price
            signal_info['sl'] = entry_price - sl_distance_atr
            signal_info['tp'] = entry_price + (sl_distance_atr * rr_factor_tp)
            
            # Validar SL/TP
            if not (signal_info['sl'] < entry_price and signal_info['tp'] > entry_price):
                self.logger.debug(f"SL/TP inválido para LONG: E={entry_price}, SL={signal_info['sl']}, TP={signal_info['tp']}")
                return None # SL/TP no son lógicos
            self.logger.info(f"Señal LONG detectada: E={entry_price:.5f}, SL={signal_info['sl']:.5f}, TP={signal_info['tp']:.5f}")
            return signal_info

        # Verificar condiciones SHORT
        if 'condicion_short' in last_bar and last_bar['condicion_short']:
            signal_info['mode'] = "short"
            signal_info['entry_price'] = entry_price
            signal_info['sl'] = entry_price + sl_distance_atr
            signal_info['tp'] = entry_price - (sl_distance_atr * rr_factor_tp)

            if not (signal_info['sl'] > entry_price and signal_info['tp'] < entry_price):
                self.logger.debug(f"SL/TP inválido para SHORT: E={entry_price}, SL={signal_info['sl']}, TP={signal_info['tp']}")
                return None # SL/TP no son lógicos
            self.logger.info(f"Señal SHORT detectada: E={entry_price:.5f}, SL={signal_info['sl']:.5f}, TP={signal_info['tp']:.5f}")
            return signal_info
            
        return None # No hay señal
    
    def calculate_position_size(self, capital: float, risk_percent_per_trade: float, entry_price: float, sl_price: float, min_position_size: float) -> float:
        """
        Calcula el tamaño de la posición basado en el riesgo.
        Esta función es un helper y no se llama directamente desde el bucle de check_entry en esta versión,
        ya que el cálculo está integrado. Podría ser externalizada.
        """
        if capital <= 0 or risk_percent_per_trade <= 0:
            return 0.0
        
        riesgo_maximo_permitido_en_capital = capital * risk_percent_per_trade
        riesgo_por_unidad_de_activo = abs(entry_price - sl_price)

        if riesgo_por_unidad_de_activo <= 1e-9: # Evitar división por cero o ATR muy pequeño
            return 0.0
            
        position_size = riesgo_maximo_permitido_en_capital / riesgo_por_unidad_de_activo
        
        if position_size < min_position_size:
            return 0.0 # No operar si el tamaño es menor al mínimo permitido
            
        return position_size