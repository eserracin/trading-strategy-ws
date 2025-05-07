# src/strategies/scalping/scalping_lp.py
from core import BaseStrategy
from indicators.ema import ema_gpt, ema
from indicators.rsi import rsi
from indicators.volume import volume_sma
from binance.client import Client
from config.settings import *
import pandas as pd
import logging

class ScalpingStrategyLP(BaseStrategy):
    def __init__(self, binance_client: Client, logger: logging.Logger = None):
        self.client = binance_client
        self.logger = logger

    def obtener_historial_inicial(self, symbol, interval='15m', period=50):
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
        # self.logger.info(f'*****Contenido de df: {df}')
        df["ema9"] = ema(df["close"], 9)
        df["ema26"] = ema(df["close"], 26)
        df["ema50"] = ema(df["close"], 50)
        df["rsi"] = rsi(df["close"], 5)
        df["vol_prom"] = volume_sma(df["volume"], 20)

        ema_cruce_alcista = (df["ema9"].iloc[-2] < df["ema26"].iloc[-2]) & (df["ema9"].iloc[-1] > df["ema26"].iloc[-1])
        ema_cruce_bajista = (df["ema9"].iloc[-2] > df["ema26"].iloc[-2]) & (df["ema9"].iloc[-1] < df["ema26"].iloc[-1])

        breackout_alcista = df["high"].iloc[-1] > df["high"].iloc[-3:-1].max()
        breackout_bajista = df["low"].iloc[-1] < df["low"].iloc[-3:-1].min()

        volumen_ok = df["volume"].iloc[-1] > df["vol_prom"].iloc[-1] * 2
        rsi_long_ok = df["rsi"].iloc[-1] > 50
        rsi_short_ok = df["rsi"].iloc[-1] < 50


        vela_alcista = df["close"].iloc[-1] > df["open"].iloc[-1]
        vela_bajista = df["close"].iloc[-1] < df["open"].iloc[-1]

        # EMA diaria (Filtro tendencia flexible)
        ema_dia_actual, serie_ema_diaria = self.obtener_ema_diaria(df["symbol"].iloc[-1])
        close_actual = df["close"].iloc[-1]

        permitido_long = close_actual > ema_dia_actual or serie_ema_diaria.iloc[-3:].is_monotonic_increasing
        permitido_short = close_actual < ema_dia_actual or serie_ema_diaria.iloc[-3:].is_monotonic_decreasing

        # Condicion de entrada Long
        condicion_long = (
            ema_cruce_alcista and
            breackout_alcista and
            volumen_ok and
            rsi_long_ok and
            vela_alcista and
            permitido_long
        )

        # Condicion de entrada Short
        condicion_short = (
            ema_cruce_bajista and
            breackout_bajista and
            volumen_ok and
            rsi_short_ok and
            vela_bajista and
            permitido_short
        )

        # self.logger.info(f"*****ema_cruce_alcista: {ema_cruce_alcista}")
        # self.logger.info(f"*****ema_cruce_bajista: {ema_cruce_bajista}")
        # self.logger.info(f"*****breackout_alcista: {breackout_alcista}")
        # self.logger.info(f"*****breackout_bajista: {breackout_bajista}")
        # self.logger.info(f"*****volumen_ok: {volumen_ok}")
        # self.logger.info(f"*****rsi_long_ok: {rsi_long_ok}")
        # self.logger.info(f"*****rsi_short_ok: {rsi_short_ok}")
        # self.logger.info(f"*****vela_alcista: {vela_alcista}")
        # self.logger.info(f"*****vela_bajista: {vela_bajista}")
        # self.logger.info(f"*****permitido_long: {permitido_long}")
        # self.logger.info(f"*****permitido_short: {permitido_short}")
        # self.logger.info(f"*****condicion_long: {condicion_long}")
        # self.logger.info(f"*****condicion_short: {condicion_short}")

        if condicion_long:
            entry_price = df["close"].iloc[-1]
            sl = entry_price - SL_DOLLAR
            tp = entry_price + TP_DOLLAR
            return "LONG", entry_price, sl, tp
        elif condicion_short:
            entry_price = df["close"].iloc[-1]
            sl = entry_price + SL_DOLLAR
            tp = entry_price - TP_DOLLAR
            return "SHORT", entry_price, sl, tp
        
        return None, None, None, None

    def calculate_position_size(self, entry_price, stop_loss):
        diff_sl  = abs(entry_price - stop_loss)
        return (INITIAL_BALANCE * RISK_PERCENTAGE) / diff_sl if diff_sl else 0
