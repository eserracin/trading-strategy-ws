# src/strategies/scalping/scalping_lp.py
from core import BaseStrategy
from indicators import crossover, ema, rsi_ta, volume_sma, ema_gpt, crossunder
from binance.client import Client
from config.settings import *
import pandas as pd
import logging


class ScalpingStrategyLP(BaseStrategy):
    def __init__(self, binance_client: Client, logger: logging.Logger = None):
        self.client = binance_client
        self.logger = logger

    def obtener_historial_inicial_con_periodo(self, symbol, interval='15m', period=50):
        self.logger.info(f"*****Obteniendo historial inicial para {symbol}")
        klines = self.client.get_historical_klines(symbol, interval, f"{period} days ago UTC")
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 
            'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 
            'taker_buy_quote_asset_volume', 'ignore'
        ])
        df['open'] = df['open'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)
        self.logger.info(f"*****Datos historicos obtenidos: {len(df)} filas")
        return df
    
    def obtener_historial_inicial_con_rango(self, symbol, interval='15m', startDate=None, endDate=None):
        pass

    def obtener_ema_diaria(self, symbol, period=20, days=30):
        # Obtener datos históricos
        historial = self.client.get_historical_klines(symbol, Client.KLINE_INTERVAL_1DAY, limit=50)
        closes = [float(kline[4]) for kline in historial]

        # calcular EMA
        serie_ema = ema_gpt(pd.Series(closes), period)

        # extraer el último valor de la EMA
        valor_actual = serie_ema.iloc[-1]

        return valor_actual, serie_ema

    def check_entry(self, df):
        # Validar que df no esta vacio
        if not df.empty or len(df) > 3:

            df_copy = df.copy()

            # self.logger.info(f'*****Contenido de df: {df}')
            df_copy["ema9"] = ema_gpt(df_copy["close"], 9)
            df_copy["ema26"] = ema_gpt(df_copy["close"], 26)
            df_copy["ema50"] = ema_gpt(df_copy["close"], 50)
            df_copy["rsi"] = rsi_ta(df_copy["close"], 5)
            df_copy["vol_prom"] = volume_sma(df_copy["volume"], 20)

            ema_cruce_alcista_series = crossover(df_copy["ema9"], df_copy["ema26"])
            ema_cruce_bajista_series = crossunder(df_copy["ema9"], df_copy["ema26"])

            hubo_ema_cruce_alcista = ema_cruce_alcista_series.fillna(False).iloc[-1]
            hubo_ema_cruce_bajista = ema_cruce_bajista_series.fillna(False).iloc[-1]

            breackout_alcista = df_copy["high"].iloc[-1] > df_copy["high"].iloc[-3:-1].max()
            breackout_bajista = df_copy["low"].iloc[-1] < df_copy["low"].iloc[-3:-1].min()

            volumen_ok = df_copy["volume"].iloc[-1] > df_copy["vol_prom"].iloc[-1] * 2
            rsi_long_ok = df_copy["rsi"].iloc[-1] > 50
            rsi_short_ok = df_copy["rsi"].iloc[-1] < 50


            vela_alcista = df_copy["close"].iloc[-1] > df_copy["open"].iloc[-1]
            vela_bajista = df_copy["close"].iloc[-1] < df_copy["open"].iloc[-1]

            # EMA diaria (Filtro tendencia flexible)
            ema_dia_actual, serie_ema_diaria = self.obtener_ema_diaria(df_copy["symbol"].iloc[-1])
            close_actual = df_copy["close"].iloc[-1]

            permitido_long = close_actual > ema_dia_actual or serie_ema_diaria.iloc[-3:].is_monotonic_increasing
            permitido_short = close_actual < ema_dia_actual or serie_ema_diaria.iloc[-3:].is_monotonic_decreasing

            # Condicion de entrada Long
            condicion_long = (
                hubo_ema_cruce_alcista and
                breackout_alcista and
                volumen_ok and
                rsi_long_ok and
                vela_alcista and
                permitido_long
            )

            # Condicion de entrada Short
            condicion_short = (
                hubo_ema_cruce_bajista and
                breackout_bajista and
                volumen_ok and
                rsi_short_ok and
                vela_bajista and
                permitido_short
            )


            if condicion_long:
                self.logger.info(f"*****hubo ema_cruce_alcista: {hubo_ema_cruce_alcista} hora: {df_copy['timestamp'].iloc[-1]}")
                entry_price = df_copy["close"].iloc[-1]
                sl = entry_price - SL_DOLLAR
                tp = entry_price + TP_DOLLAR
                return "LONG", entry_price, sl, tp
            elif condicion_short:
                self.logger.info(f"*****hubo ema_cruce_bajista: {hubo_ema_cruce_bajista} hora: {df_copy['timestamp'].iloc[-1]}")
                entry_price = df_copy["close"].iloc[-1]
                sl = entry_price + SL_DOLLAR
                tp = entry_price - TP_DOLLAR
                return "SHORT", entry_price, sl, tp
            
        return None, None, None, None

    def calculate_position_size(self, entry_price, stop_loss):
        diff_sl  = abs(entry_price - stop_loss)
        return (INITIAL_BALANCE * RISK_PERCENTAGE) / diff_sl if diff_sl else 0
        
    def cruce_sostenido(self, df: pd.DataFrame, col_corta: str, col_larga: str, tipo="alcista", col_fecha: str = "timestamp_iso"):
        """
        Detecta si hubo un cruce entre dos EMAs (alcista o bajista) y si se ha mantenido hasta la última vela.
        
        :param df: DataFrame con las columnas de EMAs
        :param col_corta: nombre de la EMA corta (ej. 'ema9')
        :param col_larga: nombre de la EMA larga (ej. 'ema26')
        :param tipo: 'alcista' o 'bajista'
        :param col_fecha: nombre de la columna de fechas en formato datetime
        :return: (bool, int or None, str or None) -> (cruce_sostenido, indice_cruce, fecha_iso_cruce)
        """
        cruce_idx = None

        for i in range(1, len(df)):
            if tipo == "alcista":
                if df[col_corta].iloc[i - 1] < df[col_larga].iloc[i - 1] and df[col_corta].iloc[i] > df[col_larga].iloc[i]:
                    cruce_idx = i
                    break
            elif tipo == "bajista":
                if df[col_corta].iloc[i - 1] > df[col_larga].iloc[i - 1] and df[col_corta].iloc[i] < df[col_larga].iloc[i]:
                    cruce_idx = i
                    break

        if cruce_idx is not None:
            if tipo == "alcista":
                sostenido = (df[col_corta].iloc[cruce_idx:] > df[col_larga].iloc[cruce_idx:]).all()
            else:
                sostenido = (df[col_corta].iloc[cruce_idx:] < df[col_larga].iloc[cruce_idx:]).all()

            fecha_cruce = None
            if col_fecha in df.columns:
                fecha_cruce = df[col_fecha].iloc[cruce_idx].isoformat()

            return sostenido, cruce_idx, fecha_cruce

        return False, None, None

