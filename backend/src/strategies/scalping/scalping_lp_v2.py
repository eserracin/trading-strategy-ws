# src/backend/src/strategies/scalping/scalping_lp_v2.py
import pandas_ta as ta
import pandas as pd
from config.settings import * 
from core import BaseStrategy 
from datetime import timezone, timedelta


class ScalpingStrategyLPV2(BaseStrategy):
    """
    Estrategia de Scalping LPV2.
    Utiliza cruces de EMAs, breakouts, volumen y un filtro de tendencia diario
    para identificar oportunidades de entrada en marcos de tiempo cortos (ej. 15m).
    """
    def __init__(self, binance_client, logger=None):
        """
        Inicializa la estrategia.

        Args:
            binance_client: Cliente de la API de Binance para obtener datos.
            logger: Objeto logger para registrar información y errores.
        """
        self.client = binance_client
        self.logger = logger
        if self.logger is None:
            import logging
            self.logger = logging.getLogger(__name__)
            self.logger.setLevel(logging.INFO)
            if not self.logger.handlers:
                self.logger.addHandler(logging.StreamHandler())

    def _procesar_klines_a_dataframe(self, klines):
        """
        Convierte la respuesta de klines de la API a un DataFrame de pandas formateado.
        """
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time',
            'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume',
            'taker_buy_quote_asset_volume', 'ignore'
        ])
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        df.rename(columns={
            'open': 'Open', 'high': 'High', 'low': 'Low',
            'close': 'Close', 'volume': 'Volume'
        }, inplace=True)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
        df.set_index('timestamp', inplace=True)
        df['close_time'] = pd.to_datetime(df['close_time'], unit='ms', utc=True)
        target_tz_datetime = timezone(timedelta(hours=-5))
        df.index = df.index.tz_convert(target_tz_datetime)
        df['close_time'] = df['close_time'].dt.tz_convert(target_tz_datetime)
        return df[['Open', 'High', 'Low', 'Close', 'Volume', 'close_time']]


    def obtener_historial_inicial_con_periodo(self, symbol, interval='15m', period_days=50):
        """
        Obtiene datos históricos de klines para un símbolo y un período de días hacia atrás.

        Args:
            symbol (str): El par de trading (ej. 'BTCUSDT').
            interval (str): El intervalo de las velas (ej. '15m', '1h').
            period_days (int): Número de días de historial a obtener.

        Returns:
            pd.DataFrame: DataFrame con los datos históricos y el índice como timestamp.
        """
        self.logger.info(f"***** Obteniendo historial inicial para {symbol} ({period_days} días atrás, intervalo {interval})")
        klines = self.client.get_historical_klines(symbol, interval, f"{period_days} days ago UTC")
        return self._procesar_klines_a_dataframe(klines)

    def obtener_historial_inicial_con_rango(self, symbol, interval='15m', startDate=None, endDate=None):
        """
        Obtiene datos históricos de klines para un símbolo dentro de un rango de fechas.

        Args:
            symbol (str): El par de trading (ej. 'BTCUSDT').
            interval (str): El intervalo de las velas (ej. '15m', '1h').
            startDate (str, optional): Fecha de inicio (ej. "1 Jan, 2020").
            endDate (str, optional): Fecha de fin (ej. "1 Jan, 2021").

        Returns:
            pd.DataFrame: DataFrame con los datos históricos y el índice como timestamp.
        """
        self.logger.info(f"***** Obteniendo historial inicial para {symbol} desde {startDate} hasta {endDate} (intervalo {interval})")
        klines = self.client.get_historical_klines(symbol, interval, startDate, endDate)
        return self._procesar_klines_a_dataframe(klines)

    def calcular_indicadores(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula y añade los indicadores técnicos necesarios al DataFrame.

        Args:
            df (pd.DataFrame): DataFrame con columnas 'Open', 'High', 'Low', 'Close', 'Volume'
                               y un DatetimeIndex.

        Returns:
            pd.DataFrame: DataFrame original con columnas adicionales para los indicadores y condiciones.
        """
        self.logger.info("Calculando indicadores técnicos...")
        # --- Indicadores Básicos (EMAs, RSI, SMA de Volumen) ---
        df.ta.ema(close='Close', length=EMA_SHORT_LEN, append=True, col_names=(f'EMA_{EMA_SHORT_LEN}',))
        df.ta.ema(close='Close', length=EMA_LONG_LEN, append=True, col_names=(f'EMA_{EMA_LONG_LEN}',))
        
        
        df.ta.rsi(close='Close', length=RSI_LEN, append=True, col_names=(f'RSI_{RSI_LEN}',))
        
        # AQUÍ DEBES CONSIDERAR AJUSTAR EN settings.py: VOL_SMA_LEN. El valor original era 20.
        df.ta.sma(close='Volume', length=VOL_SMA_LEN, append=True, col_names=(f'VOL_SMA_{VOL_SMA_LEN}',))
        df.ta.atr(length=ATR_LEN, append=True, col_names=(f'ATR_{ATR_LEN}',))
        df.ta.ema(close='Close', length=EMA_TREND_FILTER_LEN, append=True, col_names=(f'EMA_TF_{EMA_TREND_FILTER_LEN}',))

        # --- Filtro de Tendencia Marco Diario Flexible ---
        daily_close = df['Close'].resample('D').last()
        ema_daily_series = ta.ema(daily_close, length=EMA_DAILY_LEN)
        ema_daily_col_name = f'EMA_D_{EMA_DAILY_LEN}'
        df[ema_daily_col_name] = ema_daily_series.reindex(df.index, method='ffill')
        daily_data_for_trend = pd.DataFrame({'ema_daily': ema_daily_series})
        daily_data_for_trend['ema_daily_rising_3'] = daily_data_for_trend['ema_daily'] > daily_data_for_trend['ema_daily'].shift(3)
        daily_data_for_trend['ema_daily_falling_3'] = daily_data_for_trend['ema_daily'] < daily_data_for_trend['ema_daily'].shift(3)
        df['ema_daily_rising_3'] = daily_data_for_trend['ema_daily_rising_3'].reindex(df.index, method='ffill')
        df['ema_daily_falling_3'] = daily_data_for_trend['ema_daily_falling_3'].reindex(df.index, method='ffill')

        # 3. Llenar NaNs iniciales del ffill para la EMA diaria y sus condiciones
        df[ema_daily_col_name].bfill(inplace=True) # bfill para las primeras barras
        df['ema_daily_rising_3'].fillna(False, inplace=True) # Asumir no rising si no hay datos
        df['ema_daily_falling_3'].fillna(False, inplace=True) # Asumir no falling si no hay datos

        # 4. Condiciones de permiso basadas en el filtro diario
        df['permitido_long_diario'] = (df['Close'] > df[ema_daily_col_name]) & df['ema_daily_rising_3']
        df['permitido_short_diario'] = (df['Close'] < df[ema_daily_col_name]) & df['ema_daily_falling_3']
        # df['permitido_long_diario'] = (df['Close'] > df[ema_daily_col_name]) | df['ema_daily_rising_3'] # Lógica original
        # df['permitido_short_diario'] = (df['Close'] < df[ema_daily_col_name]) | df['ema_daily_falling_3'] # Lógica original


        # --- Detección de Velas y Breakouts ---
        df['vela_alcista'] = df['Close'] > df['Open']
        df['vela_bajista'] = df['Close'] < df['Open']

        # AQUÍ DEBES CONSIDERAR AJUSTAR: Periodo de lookback para breakouts. Originalmente era 2.
        # Un valor mayor como 5 o 10 podría ser más robusto.
        # Por ejemplo, para un breakout de 5 velas:
        # df['highest_prev_N_high'] = df['High'].shift(1).rolling(window=5, min_periods=5).max()
        # df['lowest_prev_N_low'] = df['Low'].shift(1).rolling(window=5, min_periods=5).min()
        # Mantendremos el original por ahora, pero es un punto clave a optimizar.
        df['highest_prev_2_high'] = df['High'].shift(1).rolling(window=2, min_periods=2).max()
        df['breakout_alcista'] = df['High'] > df['highest_prev_2_high']
        df['lowest_prev_2_low'] = df['Low'].shift(1).rolling(window=2, min_periods=2).min()
        df['breakout_bajista'] = df['Low'] < df['lowest_prev_2_low']

        df['ema_cruce_alcista'] = (df[f'EMA_{EMA_SHORT_LEN}'] > df[f'EMA_{EMA_LONG_LEN}']) & \
                                  (df[f'EMA_{EMA_SHORT_LEN}'].shift(1) <= df[f'EMA_{EMA_LONG_LEN}'].shift(1))
        df['ema_cruce_bajista'] = (df[f'EMA_{EMA_SHORT_LEN}'] < df[f'EMA_{EMA_LONG_LEN}']) & \
                                   (df[f'EMA_{EMA_SHORT_LEN}'].shift(1) >= df[f'EMA_{EMA_LONG_LEN}'].shift(1))

        df['volumen_ok'] = df['Volume'] > (df[f'VOL_SMA_{VOL_SMA_LEN}'] * 1.5)

        # --- Combinar Condiciones Finales para Entradas ---
        # Construir condiciones base
        base_cond_long = (df['ema_cruce_alcista'] &
                        df['breakout_alcista'] &
                        df['volumen_ok'] &
                        (df[f'RSI_{RSI_LEN}'] > 60) &
                        df['vela_alcista'] &
                        df['permitido_long_diario'])

        base_cond_short = (df['ema_cruce_bajista'] &
                        df['breakout_bajista'] &
                        df['volumen_ok'] &
                        (df[f'RSI_{RSI_LEN}'] < 40) &
                        df['vela_bajista'] &
                        df['permitido_short_diario'])

        # Aplicar filtro de tendencia adicional si está configurado
        if 'EMA_TREND_FILTER_LEN' in globals() and f'EMA_TF_{EMA_TREND_FILTER_LEN}' in df.columns:
            df['condicion_long'] = base_cond_long & (df['Close'] > df[f'EMA_TF_{EMA_TREND_FILTER_LEN}'])
            df['condicion_short'] = base_cond_short & (df['Close'] < df[f'EMA_TF_{EMA_TREND_FILTER_LEN}'])
        else:
            df['condicion_long'] = base_cond_long
            df['condicion_short'] = base_cond_short
        
        cols_condiciones = ['condicion_long', 'condicion_short', 'breakout_alcista', 'breakout_bajista',
                            'ema_cruce_alcista', 'ema_cruce_bajista']
        for col in cols_condiciones:
            if col in df.columns:
                 df[col].fillna(False, inplace=True)
        
        self.logger.info("Cálculo de indicadores completado.")
        return df

    def check_entry(self, df: pd.DataFrame):
        """
        Ejecuta el backtesting de la estrategia sobre los datos históricos con indicadores.

        Args:
            df (pd.DataFrame): DataFrame con precios, indicadores y condiciones de entrada.

        Returns:
            tuple: (list_of_trades, final_capital)
                   list_of_trades: Una lista de diccionarios, cada uno representando un trade.
                   final_capital: El capital restante después de todos los trades.
        """
        self.logger.info("Iniciando backtest (check_entry)...")
        capital = INITIAL_BALANCE
        trades = []
        active_trade = None
        # Iniciar para permitir la primera entrada inmediatamente si se cumplen las condiciones
        last_entry_bar_iloc = -(MIN_BARS_ENTRE_TRADES + 1) 

        _RISK_PERCENT_PER_TRADE = RISK_PERCENT_PER_TRADE
        _ATR_MULTIPLIER_SL = ATR_MULTIPLIER_SL
        _RR_FACTOR_TP = RR_FACTOR_TP

        # Determinar el nombre de la columna ATR basado en si ATR_LEN fue definido
        atr_col_name = f'ATR_{ATR_LEN}' if 'ATR_LEN' in globals() else 'ATR_14'
        if atr_col_name not in df.columns:
            self.logger.error(f"Columna ATR '{atr_col_name}' no encontrada en el DataFrame. SL/TP dinámico fallará.")
            # Podrías detener el backtest aquí o usar un SL/TP fijo como fallback (no recomendado)
            return [], capital # Salir si no hay ATR


        for i in range(len(df)):
            current_bar = df.iloc[i]
            current_bar_timestamp = df.index[i]
            current_bar_iloc = i

            # --- AQUÍ DEBES AGREGAR EL CAMBIO: Comprobar si el capital es suficiente ---
            if capital <= 0: # O un umbral mínimo para operar, ej. capital < (MIN_POSITION_SIZE * current_bar['Close'])
                self.logger.warning(f"Capital insuficiente ({capital:.2f}) para continuar operando en {current_bar_timestamp}. Deteniendo backtest.")
                break # Detener el backtest si el capital se agota

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
                    else:
                        pnl = (active_trade['entry_price'] - exit_price) * active_trade['size']
                    capital += pnl
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
                puede_entrar_por_frecuencia = (current_bar_iloc - last_entry_bar_iloc) > MIN_BARS_ENTRE_TRADES
                entry_price_candidate = current_bar['Close']
                sl_price_candidate = None
                tp_price_candidate = None
                trade_type_candidate = None

                current_atr = current_bar.get(atr_col_name, 0) # Usar .get con fallback por si acaso
                if pd.isna(current_atr) or current_atr == 0: # Si ATR es NaN o 0, no podemos calcular SL/TP dinámico
                    if puede_entrar_por_frecuencia and (current_bar['condicion_long'] or current_bar['condicion_short']):
                        self.logger.debug(f"Skipping trade at {current_bar_timestamp} due to invalid ATR: {current_atr}")
                    continue # Saltar esta barra si ATR no es válido

                # --- AQUÍ DEBES AGREGAR EL CAMBIO: Cálculo de SL/TP dinámico con ATR ---
                sl_distance_atr = current_atr * _ATR_MULTIPLIER_SL

                if current_bar['condicion_long'] and puede_entrar_por_frecuencia:
                    trade_type_candidate = "long"
                    sl_price_candidate = entry_price_candidate - sl_distance_atr
                    tp_price_candidate = entry_price_candidate + (sl_distance_atr * _RR_FACTOR_TP)
                elif current_bar['condicion_short'] and puede_entrar_por_frecuencia:
                    trade_type_candidate = "short"
                    sl_price_candidate = entry_price_candidate + sl_distance_atr
                    tp_price_candidate = entry_price_candidate - (sl_distance_atr * _RR_FACTOR_TP)

                if trade_type_candidate:
                    
                    riesgo_maximo_permitido_en_capital = capital * _RISK_PERCENT_PER_TRADE
                    
                    # Distancia al SL en precio
                    riesgo_por_unidad_de_activo = abs(entry_price_candidate - sl_price_candidate) 
                    
                    position_size = 0
                    if riesgo_por_unidad_de_activo > 1e-9: # Evitar división por cero
                        position_size = riesgo_maximo_permitido_en_capital / riesgo_por_unidad_de_activo
                    
                    sl_tp_valido = False
                    if trade_type_candidate == "long" and \
                       sl_price_candidate < entry_price_candidate and \
                       tp_price_candidate > entry_price_candidate:
                        sl_tp_valido = True
                    elif trade_type_candidate == "short" and \
                         sl_price_candidate > entry_price_candidate and \
                         tp_price_candidate < entry_price_candidate:
                        sl_tp_valido = True
                    
                    entrada_valida = position_size >= MIN_POSITION_SIZE and sl_tp_valido

                    if entrada_valida:
                        active_trade = {
                            'entry_time': current_bar_timestamp,
                            'type': trade_type_candidate,
                            'entry_price': entry_price_candidate,
                            'sl': sl_price_candidate,
                            'tp': tp_price_candidate,
                            'size': position_size,
                            'entry_bar_iloc': current_bar_iloc # Guardar el iloc de la barra de entrada
                        }
                        last_entry_bar_iloc = current_bar_iloc

        if active_trade:
            last_bar = df.iloc[-1]
            last_close_price = last_bar['Close']
            last_bar_timestamp = df.index[-1]
            pnl = 0

            if active_trade['type'] == 'long':
                pnl = (last_close_price - active_trade['entry_price']) * active_trade['size']
            else:
                pnl = (active_trade['entry_price'] - last_close_price) * active_trade['size']
            capital += pnl
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

        self.logger.info(f"\nBacktest Finalizado. Capital Inicial: ${INITIAL_BALANCE:.2f}, Capital Final: ${capital:.2f}")
        if trades:
            self.logger.info(f"Total trades: {len(trades)}")
        else:
            self.logger.info("No se realizaron trades.")
            
        return trades, capital 

    def calculate_position_size(self, entry_price: float, sl_price: float) -> float:
        pass