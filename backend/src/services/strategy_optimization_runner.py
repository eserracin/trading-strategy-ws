import pandas as pd
from core import ContextStrategy
from binance.client import Client as BinanceClient
# Se comenta la importación directa de settings si los parámetros clave vendrán de fuera
# from config import settings 
import logging
import numpy as np
from datetime import datetime, timedelta, timezone

logger = logging.getLogger("TRADING_BOT")

# **** Inicio - Funciones Auxiliares (Sin cambios respecto a tu versión) ****
def convertir_a_tipo_nativo(val):
    # Se añade manejo de NaN y Infinito para robustez con Optuna y métricas
    if pd.isna(val): 
        return None
    if isinstance(val, (np.integer, np.int64)):
        return int(val)
    elif isinstance(val, (np.floating, np.float64)):
        if np.isinf(val):
            return "Infinity" if val > 0 else "-Infinity"
        return float(val)
    elif isinstance(val, (pd.Timestamp, np.datetime64)):
        if isinstance(val, pd.Timestamp):
            return val.strftime('%Y-%m-%d %H:%M:%S %Z') if val.tzinfo else val.strftime('%Y-%m-%d %H:%M:%S')
        return str(val) 
    elif isinstance(val, str) and val == "N/A": 
        return val
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
        # Importar settings aquí solo si es estrictamente necesario para valores por defecto del mock
        from config import settings 
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
# **** Fin - Funciones Auxiliares ****

class StrategyOptimizationRunner:
    def __init__(self, use_mock_client=False, strategy=None):
        self.logger = logger
        self.use_mock_client = use_mock_client
        # Importar settings aquí SÓLO para configuración del runner (API keys, etc.)
        from config import settings 

        if self.use_mock_client:
            self.client = BinanceAPIMockClient()
            self.logger.info("Usando BinanceAPIMockClient para pruebas.")
        else:
            self.client = BinanceClient(api_key=getattr(settings, 'API_KEY', None), 
                                      api_secret=getattr(settings, 'API_SECRET', None))
            self.logger.info("Usando BinanceClient real.")  

        self.strategy = ContextStrategy.get_strategy(strategy=strategy, binance_client=self.client, logger=logger)
        if not self.strategy:
             raise ValueError(f"No se pudo cargar la estrategia: {strategy}")

    def _calculate_metrics(self, trades_df: pd.DataFrame, initial_capital: float) -> dict:
        # **** Inicio - Cálculo de Métricas (Sin cambios lógicos respecto a tu versión) ****
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
        # **** Cambio para usar initial_capital pasado como argumento ****
        final_capital_calc = initial_capital + total_pnl # Calcular basado en PnL total
        
        average_pnl_per_trade = total_pnl / total_trades if total_trades > 0 else 0

        gross_profit = winning_trades_series.sum()
        gross_loss = abs(losing_trades_series.sum())
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf') if gross_profit > 0 else 0

        if not trades_df.empty:
            # Asegurar que el cálculo de drawdown use el initial_capital correcto
            capital_series = pd.concat([pd.Series([initial_capital]), trades_df['capital_after_trade']]).reset_index(drop=True)
        else:
            capital_series = pd.Series([initial_capital])
            
        if len(capital_series) > 1 : 
            peak = capital_series.expanding(min_periods=1).max()
            drawdown = (capital_series - peak) / peak
            # Asegurar que el drawdown se calcule sobre el pico correcto
            valid_peaks = peak[peak != 0] # Evitar división por cero si el capital llega a 0
            if not valid_peaks.empty:
                 drawdown_percent = (capital_series - peak) / valid_peaks * 100
                 max_drawdown_percent = abs(drawdown_percent.min()) if not drawdown_percent.empty and drawdown_percent.min() < 0 else 0
            else:
                 max_drawdown_percent = 0
        else: 
            max_drawdown_percent = 0

        average_win_amount = winning_trades_series.mean() if num_winning_trades > 0 else 0
        average_loss_amount = abs(losing_trades_series.mean()) if num_losing_trades > 0 else 0
        loss_rate_percent = (num_losing_trades / total_trades) * 100 if total_trades > 0 else 0
        expectancy = ((win_rate_percent/100 * average_win_amount) - (loss_rate_percent/100 * average_loss_amount)) if total_trades > 0 else 0

        # Aplicar conversión al final
        final_metrics = {
            "total_trades": total_trades,
            "winning_trades": num_winning_trades,
            "losing_trades": num_losing_trades,
            "win_rate_percent": round(win_rate_percent, 2),
            "total_pnl": round(total_pnl, 2),
            "average_pnl_per_trade": round(average_pnl_per_trade, 2),
            "profit_factor": round(profit_factor, 2) if profit_factor != float('inf') else "Infinity",
            "max_drawdown_percent": round(max_drawdown_percent, 2),
            "average_win_amount": round(average_win_amount, 2),
            "average_loss_amount": round(average_loss_amount, 2),
            "expectancy": round(expectancy, 2)
        }
        return {k: convertir_a_tipo_nativo(v) for k, v in final_metrics.items()}
        # **** Fin - Cálculo de Métricas ****

    # **** Cambio: Añadido argumento 'strategy_params' ****
    def simular(self, symbol: str, interval: str, start_date: str = None, end_date: str = None, period_days: int = None, strategy_params: dict = None):
        self.logger.info(f"Iniciando simulación para {symbol} ({interval}) con mock={self.use_mock_client}")

        # **** Cambio: Validar y obtener parámetros de 'strategy_params' ****
        if strategy_params is None:
            self.logger.error("Error: strategy_params no fue proporcionado a simular().")
            return {"success": False, "error": "Parámetros de estrategia no proporcionados."}
            
        # **** Cambio: Obtener initial_balance desde los parámetros recibidos ****
        initial_balance = strategy_params.get('INITIAL_BALANCE', 10000) # Usar default si no está

        try:
            # Importar settings aquí solo para el default period si es necesario
            from config import settings
            default_period = getattr(settings, 'DEFAULT_PERIOD_DAYS_HISTORICAL', 30)
            
            # **** Inicio - Obtención de Datos Históricos (Sin cambios lógicos) ****
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
                self.logger.info(f"Usando período por defecto: {default_period} días.")
                df_historical = self.strategy.obtener_historial_inicial_con_periodo(
                    symbol=symbol, interval=interval, period_days=default_period
                )
            # **** Fin - Obtención de Datos Históricos ****

            if df_historical.empty:
                self.logger.warning(f"No se obtuvieron datos históricos para {symbol} con los parámetros dados.")
                # **** Cambio: Devolver strategy_params en caso de error ****
                return {"success": False, "error": "No se obtuvieron datos históricos.", "trades": [], "metrics": {}, "config_params": {k: convertir_a_tipo_nativo(v) for k, v in strategy_params.items()}}

            # **** Cambio: Pasar 'strategy_params' a los métodos de la estrategia ****
            # El comentario solicitado por el usuario no aplica directamente aquí, 
            # sino dentro de los métodos de la estrategia que usan los parámetros.
            df_with_indicators = self.strategy.calcular_indicadores(df_historical.copy(), params=strategy_params)
            trades_list, final_capital = self.strategy.check_entry(df_with_indicators, params=strategy_params)
            
            trades_df = pd.DataFrame(trades_list)

            # **** Inicio - Procesamiento de Resultados (Sin cambios lógicos) ****
            if not trades_df.empty:
                trades_df['entry_time'] = trades_df['entry_time'].astype(str)
                trades_df['exit_time'] = trades_df['exit_time'].astype(str)
                for col in trades_df.columns:
                    trades_df[col] = trades_df[col].apply(convertir_a_tipo_nativo)
                trades_output = trades_df.to_dict(orient='records')
            else:
                trades_output = []
            # **** Fin - Procesamiento de Resultados ****
            
            # **** Cambio: Pasar el initial_balance correcto a _calculate_metrics ****
            metrics = self._calculate_metrics(trades_df, initial_balance)

            self.logger.info(f"Simulación completada para {symbol}. Capital Final: {final_capital:.2f}. Trades: {len(trades_list)}")
            
            return {
                "success": True,
                "data": {
                    "symbol": symbol,
                    "interval": interval,
                    "data_range_start": convertir_a_tipo_nativo(df_historical.index.min()) if not df_historical.empty else "N/A",
                    "data_range_end": convertir_a_tipo_nativo(df_historical.index.max()) if not df_historical.empty else "N/A",
                    "initial_capital": convertir_a_tipo_nativo(initial_balance),
                    "final_capital": convertir_a_tipo_nativo(round(final_capital, 2)),
                    "trades": trades_output,
                    "metrics": metrics,
                    # **** Cambio: Devolver los parámetros usados en esta simulación ****
                    "config_params": {k: convertir_a_tipo_nativo(v) for k, v in strategy_params.items()}
                }
            }
        except Exception as e:
            self.logger.error(f"Error durante la simulación para {symbol}: {e}", exc_info=True)
             # **** Cambio: Devolver strategy_params en caso de error ****
            return {"success": False, "error": str(e), "trades": [], "metrics": {}, "config_params": {k: convertir_a_tipo_nativo(v) for k, v in strategy_params.items()}}

    def _get_current_config(self):
       # Esta función ya no es representativa de los parámetros usados durante la optimización.
       # Se deja por si se llama fuera de Optuna, pero devolverá los valores de settings.
       from config import settings
       self.logger.warning("_get_current_config devolverá valores de config/settings, no necesariamente los usados en la última simulación optimizada.")
       config = {
            "EMA_SHORT_LEN": getattr(settings, 'EMA_SHORT_LEN', None),
            "EMA_LONG_LEN": getattr(settings, 'EMA_LONG_LEN', None),
            "EMA_TREND_LEN": getattr(settings, 'EMA_TREND_LEN', None), 
            "RSI_LEN": getattr(settings, 'RSI_LEN', None),
            "VOL_SMA_LEN": getattr(settings, 'VOL_SMA_LEN', None),
            "EMA_DAILY_LEN": getattr(settings, 'EMA_DAILY_LEN', None),
            "INITIAL_BALANCE": getattr(settings, 'INITIAL_BALANCE', None),
            "RISK_PERCENT_PER_TRADE": getattr(settings, 'RISK_PERCENT_PER_TRADE', None),
            "ATR_LEN": getattr(settings, 'ATR_LEN', None),
            "ATR_MULTIPLIER_SL": getattr(settings, 'ATR_MULTIPLIER_SL', None),
            "RR_FACTOR_TP": getattr(settings, 'RR_FACTOR_TP', None),
            "EMA_TREND_FILTER_LEN": getattr(settings, 'EMA_TREND_FILTER_LEN', "No Usado"),
            "MIN_BARS_ENTRE_TRADES": getattr(settings, 'MIN_BARS_ENTRE_TRADES', None),
            "MIN_POSITION_SIZE": getattr(settings, 'MIN_POSITION_SIZE', None),
            "BREAKOUT_WINDOW": getattr(settings, 'BREAKOUT_WINDOW', None) # Añadido si está en settings
        }
       return {k: convertir_a_tipo_nativo(v) for k, v in config.items() if v is not None}