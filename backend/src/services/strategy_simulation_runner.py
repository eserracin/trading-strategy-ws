# src/services/strategy_simulation_runner.py
import pandas as pd
from core import ContextStrategy
from binance.client import Client as BinanceClient
from config import settings
import logging
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from src.models.strategy_config import StrategyConfigParams # Importar el modelo
from sqlalchemy.orm import Session

logger = logging.getLogger("TRADING_BOT")

def convertir_a_tipo_nativo(val):
    if isinstance(val, (np.integer, np.int64)):
        return int(val)
    elif isinstance(val, (np.floating, np.float64)):
        return float(val)
    elif isinstance(val, (pd.Timestamp, np.datetime64)):
        if isinstance(val, pd.Timestamp):
            return val.strftime('%Y-%m-%d %H:%M:%S %Z') if val.tzinfo else val.strftime('%Y-%m-%d %H:%M:%S')
        return str(val)
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
            end_dt_for_calc = datetime.now(timezone.utc) # Usar now con timezone
            start_dt_for_calc = end_dt_for_calc - timedelta(days=days_ago)
        elif start_str and end_str:
            start_dt_for_calc = pd.to_datetime(start_str, utc=True)
            end_dt_for_calc = pd.to_datetime(end_str, utc=True)
        elif start_str:
            start_dt_for_calc = pd.to_datetime(start_str, utc=True)
            end_dt_for_calc = datetime.now(timezone.utc)
        else: # Ni start_str/end_str ni "days ago"
            logger.warning("MOCK: Fechas de klines no especificadas correctamente, generando datos por defecto.")
            end_dt_for_calc = datetime.now(timezone.utc)
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
            open_price = base_price + (np.random.randn() * 10) # Añadir algo de aleatoriedad
            close_price = open_price + (np.random.randn() * 5)
            high_price = max(open_price, close_price) + abs(np.random.rand() * 2)
            low_price = min(open_price, close_price) - abs(np.random.rand() * 2)
            volume = 10 + (idx % 5) + np.random.rand() * 5
            timestamp_ms = int(current_dt.timestamp() * 1000)
            klines_data.append([
                timestamp_ms, str(open_price), str(high_price), str(low_price),
                str(close_price), str(volume), int((current_dt + delta - timedelta(milliseconds=1)).timestamp() * 1000), # close_time es fin de la vela
                str(volume * ((open_price + close_price)/2) ), # quote_asset_volume aproximado
                idx + 1, # number_of_trades
                str(volume / 2 * (1 + np.random.rand()*0.2-0.1) ), # taker_buy_base_asset_volume
                str((volume / 2 * ((open_price + close_price)/2)) * (1 + np.random.rand()*0.2-0.1) ), # taker_buy_quote_asset_volume
                "0" # ignore
            ])
            current_dt += delta
            idx +=1
            if idx > 50000:
                logger.warning("MOCK: Límite de 50000 velas alcanzado.")
                break
        if not klines_data:
            logger.error(f"MOCK: No se generaron klines para {symbol} con los parámetros dados.")
        else:
            logger.info(f"MOCK: Generadas {len(klines_data)} velas de ejemplo para {symbol}.")
        return klines_data

class StrategySimulatorRunner:
    def __init__(self, db_session: Session, use_mock_client=False, strategy=None):
        self.logger = logger
        self.use_mock_client = use_mock_client
        self.db_session = db_session

        if self.use_mock_client:
            self.client = BinanceAPIMockClient()
            self.logger.info("Usando BinanceAPIMockClient para pruebas.")
        else:
            self.client = BinanceClient(api_key=settings.API_KEY, api_secret=settings.API_SECRET)
            self.logger.info("Usando BinanceClient real.")  

        # Pasar db_session al instanciar la estrategia
        self.strategy = ContextStrategy.get_strategy(
            strategy=strategy,
            binance_client=self.client,
            db_session=self.db_session,
            logger=logger
        )

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

        if not trades_df.empty:
            capital_series = pd.concat([pd.Series([initial_capital]), trades_df['capital_after_trade']]).reset_index(drop=True)
        else:
            capital_series = pd.Series([initial_capital])
            
        if len(capital_series) > 1 :
            peak = capital_series.expanding(min_periods=1).max()
            drawdown = (capital_series - peak) / peak
            max_drawdown_percent = abs(drawdown.min() * 100) if not drawdown.empty and drawdown.min() < 0 else 0
        else:
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

    def simular(self, symbol: str, interval: str,
                start_date: Optional[str] = None, end_date: Optional[str] = None,
                period_days: Optional[int] = None,
                config_params_obj: Optional[StrategyConfigParams] = None) -> Dict[str, Any]:
        
        self.logger.info(f"Iniciando simulación para {symbol} ({interval}) con mock={self.use_mock_client}")

        if config_params_obj is None:
            self.logger.error("StrategyConfigParams no fue proporcionado a StrategySimulatorRunner.simular()")
            return {"success": False, "error": "Parámetros de configuración no proporcionados.", "trades": [], "metrics": {}, "config_params": {}}
        

        current_config_dict = config_params_obj.model_dump()

        try:
            if start_date and end_date: # Rango de fechas explícito
                self.logger.info(f"Obteniendo historial por rango: {start_date} a {end_date}")
                df_historical = self.strategy.obtener_historial_inicial_con_rango(
                    symbol=symbol, interval=interval, startDate=start_date, endDate=end_date
                )
            elif period_days: # Período en días hacia atrás
                self.logger.info(f"Obteniendo historial por período: {period_days} días.")
                df_historical = self.strategy.obtener_historial_inicial_con_periodo(
                    symbol=symbol, interval=interval, period_days=period_days
                )
            else: # Caso por defecto (ni rango ni período especificado)
                default_days = getattr(settings, 'DEFAULT_PERIOD_DAYS_HISTORICAL', 30)
                self.logger.info(f"Usando período por defecto: {default_days} días.")
                df_historical = self.strategy.obtener_historial_inicial_con_periodo(
                    symbol=symbol, interval=interval, period_days=default_days
                )

            if df_historical.empty:
                self.logger.warning(f"No se obtuvieron datos históricos para {symbol} con los parámetros dados.")
                return {"success": False, "error": "No se obtuvieron datos históricos.", "trades": [], "metrics": {}, "config_params": self._get_current_config(current_config_dict)}
            
            self.logger.info(f"Datos históricos obtenidos para {symbol}: {len(df_historical)} filas.")

            df_with_indicators = self.strategy.calcular_indicadores(df_historical.copy(), params=current_config_dict)
            if df_with_indicators.empty and not df_historical.empty:
                self.logger.warning(f"El DataFrame quedó vacío después de calcular indicadores para {symbol}. Puede que no haya suficientes datos para los periodos de los indicadores.")

            trades_list, final_capital = self.strategy.check_entry(df_with_indicators, params=current_config_dict)

            trades_df = pd.DataFrame(trades_list)

            if not trades_df.empty:
                if 'entry_time' in trades_df.columns:
                    trades_df['entry_time'] = trades_df['entry_time'].astype(str)
                if 'exit_time' in trades_df.columns:
                    trades_df['exit_time'] = trades_df['exit_time'].astype(str)
                for col in trades_df.columns:
                    trades_df[col] = trades_df[col].apply(convertir_a_tipo_nativo)
                trades_output = trades_df.to_dict(orient='records')
            else:
                trades_output = []
            
            initial_balance_for_metrics = current_config_dict.get('INITIAL_BALANCE', settings.INITIAL_BALANCE)
            metrics = self._calculate_metrics(trades_df, initial_balance_for_metrics, final_capital)

            self.logger.info(f"Simulación completada para {symbol}. Capital Final: {final_capital:.2f}. Trades: {len(trades_list)}")
            
            return {
                "success": True,
                "data": {
                	"symbol": symbol,
                	"interval": interval,
                    "data_range_start": convertir_a_tipo_nativo(df_historical.index.min()) if not df_historical.empty else "N/A",
                    "data_range_end": convertir_a_tipo_nativo(df_historical.index.max()) if not df_historical.empty else "N/A",
                    "initial_capital": convertir_a_tipo_nativo(initial_balance_for_metrics),
                    "final_capital": convertir_a_tipo_nativo(round(final_capital, 2)),
                    "trades": trades_output,
                	"metrics": metrics,
                    "config_params": self._get_current_config(current_config_dict)
                }
            }
        except Exception as e:
            self.logger.error(f"Error durante la simulación para {symbol}: {e}", exc_info=True)
            return {"success": False, "error": str(e), "trades": [], "metrics": {}, "config_params": self._get_current_config(current_config_dict if current_config_dict else {})}

    def _get_current_config(self, params_used_for_simulation: dict) -> dict:
        """Devuelve los parámetros de configuración que se usaron para esta simulación."""
        # Simplemente convierte los valores del diccionario de parámetros proporcionado.
        # Este diccionario debe ser el que se utilizó realmente en la simulación.
        if not params_used_for_simulation: # Si por alguna razón está vacío
            return {"info": "No configuration parameters were available for this simulation report."}
        return {k: convertir_a_tipo_nativo(v) for k, v in params_used_for_simulation.items()}