import pandas as pd
from core import ContextStrategy
from binance.client import Client as BinanceClient
from config import settings
import logging
import numpy as np
from datetime import datetime, timedelta, timezone

logger = logging.getLogger("TRADING_BOT")

def convertir_a_tipo_nativo(val):
    if isinstance(val, (np.integer, np.int64)):
        return int(val)
    elif isinstance(val, (np.floating, np.float64)):
        return float(val)
    elif isinstance(val, (pd.Timestamp, np.datetime64)):
        # Convertir a string con formato específico y timezone si existe
        if isinstance(val, pd.Timestamp):
            # Mantener la información de la zona horaria si está presente
            return val.strftime('%Y-%m-%d %H:%M:%S %Z') if val.tzinfo else val.strftime('%Y-%m-%d %H:%M:%S')
        return str(val) # Fallback para np.datetime64 si no es pd.Timestamp
    else:
        return val

class BinanceAPIMockClient:
    """
    Un cliente mock para pruebas locales sin conectar a la API real.
    Útil para desarrollo y para CI/CD.
    """
    def __init__(self, api_key=None, api_secret=None):
        logger.info("BinanceAPIMockClient inicializado. NO se conectará a la API real.")

    def get_historical_klines(self, symbol, interval, start_str, end_str=None):
        logger.info(f"MOCK: Solicitando klines históricos para {symbol}, {interval}, desde {start_str} hasta {end_str}")
        if "days ago UTC" in start_str:
            days_ago = int(start_str.split(" ")[0])
            end_dt_for_calc = datetime.utcnow()
            start_dt_for_calc = end_dt_for_calc - timedelta(days=days_ago)
        elif start_str and end_str:
            start_dt_for_calc = pd.to_datetime(start_str, utc=True)
            end_dt_for_calc = pd.to_datetime(end_str, utc=True)
        elif start_str:
            start_dt_for_calc = pd.to_datetime(start_str, utc=True)
            end_dt_for_calc = datetime.utcnow()
        else:
            logger.warning("MOCK: Fechas de klines no especificadas correctamente, generando datos por defecto.")
            end_dt_for_calc = datetime.utcnow()
            start_dt_for_calc = end_dt_for_calc - timedelta(days=getattr(settings, 'DEFAULT_PERIOD_DAYS_HISTORICAL', 30))

        if interval == '1m': delta = timedelta(minutes=1)
        elif interval == '5m': delta = timedelta(minutes=5)
        elif interval == '15m': delta = timedelta(minutes=15)
        elif interval == '1h': delta = timedelta(hours=1)
        elif interval == '4h': delta = timedelta(hours=4)
        elif interval == '1d': delta = timedelta(days=1)
        else: delta = timedelta(minutes=15)

        klines_data = []
        current_dt = start_dt_for_calc
        base_price = 10000
        idx = 0
        while current_dt < end_dt_for_calc:
            open_price = base_price + (idx % 10 - 5) * 10
            close_price = open_price + (idx % 7 - 3) * 5
            high_price = max(open_price, close_price) + abs(idx % 3 * 2)
            low_price = min(open_price, close_price) - abs(idx % 4 * 2)
            volume = 10 + (idx % 5)
            timestamp_ms = int(current_dt.timestamp() * 1000)
            klines_data.append([
                timestamp_ms, str(open_price), str(high_price), str(low_price),
                str(close_price), str(volume), int((current_dt + delta).timestamp() * 1000) -1,
                str(volume * close_price), idx + 1, str(volume / 2),
                str((volume / 2) * close_price), "0"
            ])
            current_dt += delta
            idx +=1
            if idx > 50000: # Aumentado límite para pruebas más largas
                logger.warning("MOCK: Límite de 50000 velas alcanzado.")
                break
        if not klines_data:
            logger.error(f"MOCK: No se generaron klines para {symbol} con los parámetros dados.")
        else:
            logger.info(f"MOCK: Generadas {len(klines_data)} velas de ejemplo para {symbol}.")
        return klines_data

class StrategySimulatorRunner:
    def __init__(self, use_mock_client=False, strategy=None):
        self.logger = logger
        self.use_mock_client = use_mock_client

        if self.use_mock_client:
            self.client = BinanceAPIMockClient()
            self.logger.info("Usando BinanceAPIMockClient para pruebas.")
        else:
            self.client = BinanceClient(api_key=settings.API_KEY, api_secret=settings.API_SECRET)
            self.logger.info("Usando BinanceClient real.")  

        self.strategy = ContextStrategy.get_strategy(strategy=strategy, binance_client=self.client, logger=logger)

    def _calculate_metrics(self, trades_df: pd.DataFrame, initial_capital: float, final_capital: float) -> dict:
        if trades_df.empty:
            return {
                "total_trades": 0, "winning_trades": 0, "losing_trades": 0,
                "win_rate_percent": 0, "total_pnl": 0, "average_pnl_per_trade": 0,
                "profit_factor": "N/A", "max_drawdown_percent": 0,
                "average_win_amount": 0, "average_loss_amount": 0, "expectancy": 0
            }

        total_trades = len(trades_df)
        winning_trades_series = trades_df[trades_df['pnl'] > 0]['pnl']
        losing_trades_series = trades_df[trades_df['pnl'] < 0]['pnl']
        num_winning_trades = len(winning_trades_series)
        num_losing_trades = len(losing_trades_series)
        win_rate_percent = (num_winning_trades / total_trades) * 100 if total_trades > 0 else 0
        total_pnl = trades_df['pnl'].sum()
        average_pnl_per_trade = total_pnl / total_trades if total_trades > 0 else 0

        gross_profit = winning_trades_series.sum()
        gross_loss = abs(losing_trades_series.sum())
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf') if gross_profit > 0 else 0

        # Corregir cálculo de Max Drawdown para evitar errores con Series vacías
        # y manejar el caso donde initial_capital es el único punto de datos.
        if not trades_df.empty:
            capital_series = pd.concat([pd.Series([initial_capital]), trades_df['capital_after_trade']]).reset_index(drop=True)
        else:
            capital_series = pd.Series([initial_capital])
            
        if len(capital_series) > 1 : # Solo calcular drawdown si hay al menos un trade
            peak = capital_series.expanding(min_periods=1).max()
            drawdown = (capital_series - peak) / peak
            max_drawdown_percent = abs(drawdown.min() * 100) if not drawdown.empty and drawdown.min() < 0 else 0
        else: # No hay trades o solo capital inicial
            max_drawdown_percent = 0

        
        average_win_amount = winning_trades_series.mean() if num_winning_trades > 0 else 0
        average_loss_amount = abs(losing_trades_series.mean()) if num_losing_trades > 0 else 0
        loss_rate_percent = (num_losing_trades / total_trades) * 100 if total_trades > 0 else 0
        expectancy = ((win_rate_percent/100 * average_win_amount) - (loss_rate_percent/100 * average_loss_amount)) if total_trades > 0 else 0


        return {
            "total_trades": convertir_a_tipo_nativo(total_trades),
            "winning_trades": convertir_a_tipo_nativo(num_winning_trades),
            "losing_trades": convertir_a_tipo_nativo(num_losing_trades),
            "win_rate_percent": convertir_a_tipo_nativo(round(win_rate_percent, 2)),
            "total_pnl": convertir_a_tipo_nativo(round(total_pnl, 2)),
            "average_pnl_per_trade": convertir_a_tipo_nativo(round(average_pnl_per_trade, 2)),
            "profit_factor": convertir_a_tipo_nativo(round(profit_factor, 2)) if profit_factor != float('inf') else "Infinity",
            "max_drawdown_percent": convertir_a_tipo_nativo(round(max_drawdown_percent, 2)),
            "average_win_amount": convertir_a_tipo_nativo(round(average_win_amount, 2)),
            "average_loss_amount": convertir_a_tipo_nativo(round(average_loss_amount, 2)),
            "expectancy": convertir_a_tipo_nativo(round(expectancy, 2))
        }

    def simular(self, symbol: str, interval: str, start_date: str = None, end_date: str = None, period_days: int = None):
        self.logger.info(f"Iniciando simulación para {symbol} ({interval}) con mock={self.use_mock_client}")

        try:
            if start_date:
                self.logger.info(f"Obteniendo historial por rango: {start_date} a {end_date}")
                df_historical = self.strategy.obtener_historial_inicial_con_rango(
                    symbol=symbol, interval=interval, startDate=start_date, endDate=end_date
                )
            elif period_days:
                self.logger.info(f"Obteniendo historial por período: {period_days} días.")
                df_historical = self.strategy.obtener_historial_inicial_con_periodo(
                    symbol=symbol, interval=interval, period_days=period_days
                )
            else:
                self.logger.info(f"Usando período por defecto: {getattr(settings, 'DEFAULT_PERIOD_DAYS_HISTORICAL', 30)} días.")
                df_historical = self.strategy.obtener_historial_inicial_con_periodo(
                    symbol=symbol, interval=interval, period_days=getattr(settings, 'DEFAULT_PERIOD_DAYS_HISTORICAL', 30)
                )

            if df_historical.empty:
                self.logger.warning(f"No se obtuvieron datos históricos para {symbol} con los parámetros dados.")
                return {"success": False, "error": "No se obtuvieron datos históricos.", "trades": [], "metrics": {}, "config_params": self._get_current_config()}

            df_with_indicators = self.strategy.calcular_indicadores(df_historical.copy())
            trades_list, final_capital = self.strategy.check_entry(df_with_indicators)
            trades_df = pd.DataFrame(trades_list)

            # Aplicar convertir_a_tipo_nativo a todas las celdas del DataFrame de trades
            # y luego a dict para asegurar la serialización JSON
            if not trades_df.empty:
                # Primero asegurar que las columnas de tiempo son strings
                trades_df['entry_time'] = trades_df['entry_time'].astype(str)
                trades_df['exit_time'] = trades_df['exit_time'].astype(str)
            
                # Convertir otros tipos problemáticos
                for col in trades_df.columns:
                    trades_df[col] = trades_df[col].apply(convertir_a_tipo_nativo)
                
                trades_output = trades_df.to_dict(orient='records')
            else:
                trades_output = []
            
            metrics = self._calculate_metrics(trades_df, settings.INITIAL_BALANCE, final_capital)

            self.logger.info(f"Simulación completada para {symbol}. Capital Final: {final_capital:.2f}. Trades: {len(trades_list)}")
            
            return {
                "success": True, # Añadido para consistencia con el JSON original
                "data": { # Añadido para consistencia con el JSON original
                "symbol": symbol,
                "interval": interval,
                    "data_range_start": convertir_a_tipo_nativo(df_historical.index.min()) if not df_historical.empty else "N/A",
                    "data_range_end": convertir_a_tipo_nativo(df_historical.index.max()) if not df_historical.empty else "N/A",
                    "initial_capital": convertir_a_tipo_nativo(settings.INITIAL_BALANCE),
                    "final_capital": convertir_a_tipo_nativo(round(final_capital, 2)),
                    "trades": trades_output,
                "metrics": metrics,
                "config_params": self._get_current_config()
            }
            }
        except Exception as e:
            self.logger.error(f"Error durante la simulación para {symbol}: {e}", exc_info=True)
            return {"success": False, "error": str(e), "trades": [], "metrics": {}, "config_params": self._get_current_config()}

    def _get_current_config(self):
        """Devuelve los parámetros de configuración actuales de la estrategia."""
        # AQUÍ DEBES AGREGAR EL CAMBIO: Actualizar los parámetros guardados
        config = {
            "EMA_SHORT_LEN": getattr(settings, 'EMA_SHORT_LEN', None),
            "EMA_LONG_LEN": getattr(settings, 'EMA_LONG_LEN', None),
            "EMA_TREND_LEN": getattr(settings, 'EMA_TREND_LEN', None), # Mantener si aún se usa en alguna parte
            "RSI_LEN": getattr(settings, 'RSI_LEN', None),
            "VOL_SMA_LEN": getattr(settings, 'VOL_SMA_LEN', None),
            "EMA_DAILY_LEN": getattr(settings, 'EMA_DAILY_LEN', None),
            "INITIAL_BALANCE": getattr(settings, 'INITIAL_BALANCE', None),
            
            # Nuevos parámetros para riesgo y SL/TP dinámico
            "RISK_PERCENT_PER_TRADE": getattr(settings, 'RISK_PERCENT_PER_TRADE', None),
            "ATR_LEN": getattr(settings, 'ATR_LEN', None),
            "ATR_MULTIPLIER_SL": getattr(settings, 'ATR_MULTIPLIER_SL', None),
            "RR_FACTOR_TP": getattr(settings, 'RR_FACTOR_TP', None),

            # Parámetros opcionales/ajustados
            "EMA_TREND_FILTER_LEN": getattr(settings, 'EMA_TREND_FILTER_LEN', "No Usado"), # Ejemplo de cómo manejar si no está

            "MIN_BARS_ENTRE_TRADES": getattr(settings, 'MIN_BARS_ENTRE_TRADES', None),
            "MIN_POSITION_SIZE": getattr(settings, 'MIN_POSITION_SIZE', None)
        }
        # Convertir todos los valores a tipos nativos para asegurar serialización
        return {k: convertir_a_tipo_nativo(v) for k, v in config.items()}