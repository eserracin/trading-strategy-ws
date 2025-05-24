# src/services/optuna_service.py
import optuna
# from src.services.strategy_optimization_runner import StrategyOptimizationRunner
from src.services.strategy_simulation_runner import StrategySimulatorRunner
from src.models.strategy_config import StrategyConfigParams
import logging
from sqlalchemy.orm import Session

logger = logging.getLogger("TRADING_BOT") # Definir logger si no está ya global

def run_optuna_optimization(params: dict, db: Session = None) -> dict:
    symbol = params["symbol"]
    strategy_name = params["strategy"] # Renombrado para evitar conflicto
    timeframe = params["timeframe"]
    start_date = params.get("start_date")
    end_date = params.get("end_date")
    period = params.get("period", 30)
    test = params.get("test", True)
    n_trials = params.get("n_trials", 30)
    # Obtener el initial_balance de los parámetros o usar un default
    initial_balance_for_sim = params.get("initial_balance", 10000) 
    # Asegúrate de que StrategySimulatorRunner use este initial_balance si es necesario,
    # o que lo obtenga de los params_for_trial que le pases.

    def objective(trial):
        
        # Crear un diccionario para los parámetros de ESTE trial
        params_for_trial = {}

        # === Grupo 1: Parámetros de Alto Impacto ===
        # params_for_trial["ATR_MULTIPLIER_SL"] = trial.suggest_float("ATR_MULTIPLIER_SL", 1.0, 3.5, step=0.25)
        # params_for_trial["RR_FACTOR_TP"] = trial.suggest_float("RR_FACTOR_TP", 1.5, 4.0, step=0.5)
        # params_for_trial["RSI_LEN"] = trial.suggest_int("RSI_LEN", 7, 21)
        # params_for_trial["EMA_SHORT_LEN"] = trial.suggest_int("EMA_SHORT_LEN", 5, 20)
        # params_for_trial["EMA_LONG_LEN"] = trial.suggest_int("EMA_LONG_LEN", 20, 60)
        
        # === Grupo 2: Parámetros de Impacto Medio (Descomentar si quieres optimizarlos) ===
        # params_for_trial["EMA_TREND_FILTER_LEN"] = trial.suggest_int("EMA_TREND_FILTER_LEN", 100, 300, step=25)
        # params_for_trial["ATR_LEN"] = trial.suggest_int("ATR_LEN", 7, 21)
        # params_for_trial["MIN_BARS_ENTRE_TRADES"] = trial.suggest_int("MIN_BARS_ENTRE_TRADES", 1, 10)
        # params_for_trial["BREAKOUT_WINDOW"] = trial.suggest_int("BREAKOUT_WINDOW", 3, 15)
        # params_for_trial["VOL_SMA_LEN"] = trial.suggest_int("VOL_SMA_LEN", 10, 40)

        # === Grupo 3: Parámetros de Impacto Medio (Descomentar si quieres optimizarlos) ===
        # params_for_trial["RISK_PERCENT_PER_TRADE"] = trial.suggest_float("RISK_PERCENT_PER_TRADE", 0.01, 0.10, step=0.01)
        


        # === Parámetros Fijos (Leídos una vez fuera del objective o pasados en 'params') ===
        from config import settings
        # === Grupo 1: Parámetros de Alto Impacto, Comentar cuando se van a probar los parametros del grupo 2 ===
        params_for_trial["ATR_MULTIPLIER_SL"] = getattr(settings, 'ATR_MULTIPLIER_SL', 1.25) # Tomar de settings como base
        params_for_trial["RR_FACTOR_TP"] = getattr(settings, 'RR_FACTOR_TP', 2.0) # Tomar de settings como base
        params_for_trial["RSI_LEN"] = getattr(settings, 'RSI_LEN', 19) # Tomar de settings como base
        params_for_trial["EMA_SHORT_LEN"] = getattr(settings, 'EMA_SHORT_LEN', 16) # Tomar de settings como base
        params_for_trial["EMA_LONG_LEN"] = getattr(settings, 'EMA_LONG_LEN', 21) # Tomar de settings como base

        # === Grupo 2: Parámetros de Impacto Medio (Comentar cuando se van a probar los parametros del grupo 1) ===
        params_for_trial["EMA_TREND_FILTER_LEN"] = params_for_trial.get("EMA_TREND_FILTER_LEN", getattr(settings, 'EMA_TREND_FILTER_LEN', 200))
        params_for_trial["ATR_LEN"] = params_for_trial.get("ATR_LEN", getattr(settings, 'ATR_LEN', 14))
        params_for_trial["MIN_BARS_ENTRE_TRADES"] = params_for_trial.get("MIN_BARS_ENTRE_TRADES", getattr(settings, 'MIN_BARS_ENTRE_TRADES', 3))
        params_for_trial["BREAKOUT_WINDOW"] = params_for_trial.get("BREAKOUT_WINDOW", getattr(settings, 'BREAKOUT_WINDOW', 5))
        params_for_trial["VOL_SMA_LEN"] = params_for_trial.get("VOL_SMA_LEN", getattr(settings, 'VOL_SMA_LEN', 20))

        # === Grupo 3: Parámetros de Impacto Medio (Descomentar si quieres optimizarlos) ===
        params_for_trial["RISK_PERCENT_PER_TRADE"] = getattr(settings, 'RISK_PERCENT_PER_TRADE', 0.02) # Tomar de settings como base
        params_for_trial["MIN_POSITION_SIZE"] = getattr(settings, 'MIN_POSITION_SIZE', 0.001)
        params_for_trial["INITIAL_BALANCE"] = initial_balance_for_sim # Usar el balance pasado
        params_for_trial["EMA_DAILY_LEN"] = getattr(settings, 'EMA_DAILY_LEN', 20)
    

        # Validar la condición de EMAs usando los valores del trial actual
        if params_for_trial["EMA_LONG_LEN"] <= params_for_trial["EMA_SHORT_LEN"]:
            logger.debug(f"Trial {trial.number} pruned: EMA_LONG_LEN ({params_for_trial['EMA_LONG_LEN']}) <= EMA_SHORT_LEN ({params_for_trial['EMA_SHORT_LEN']})")
            raise optuna.TrialPruned()

        try:
            config_params_pydantic_instance = StrategyConfigParams(**params_for_trial)

            sim = StrategySimulatorRunner(db_session=db, use_mock_client=test, strategy=strategy_name)
            result = sim.simular(
                symbol=symbol,
                interval=timeframe,
                start_date=start_date,
                end_date=end_date,
                period_days=period,
                config_params_obj=config_params_pydantic_instance, 
            )

            if result["success"]:
                final_capital = result["data"]["final_capital"]
                profit_factor = result["data"]["metrics"].get("profit_factor", 0) 
                if isinstance(profit_factor, str) or profit_factor <= 0.1:
                    profit_factor = 0.1
                    
                logger.debug(f"Trial {trial.number} completed. Params: {params_for_trial}. Final Capital: {final_capital}")
                return final_capital

            else:
                logger.warning(f"Trial {trial.number} failed simulation: {result.get('error', 'Unknown error')}")
                return -999999 # Penalización grande si la simulación falla

        except optuna.TrialPruned as e:
            # Si ya se hizo prune antes, solo relanzar
             raise e
        except Exception as e:
            logger.error(f"Error during trial {trial.number}: {e}", exc_info=True)
            return -999999 # Penalización por error inesperado

    # --- Fin de la función objective ---

    study = optuna.create_study(direction="maximize", pruner=optuna.pruners.MedianPruner()) # Añadir pruner es buena idea
    try:
        study.optimize(objective, n_trials=n_trials, timeout=600) # Añadir timeout (ej. 10 minutos)
    except Exception as e:
         logger.error(f"Optimization stopped due to error: {e}", exc_info=True)


    # Preparar el resultado final
    trials_data = []
    if hasattr(study, 'trials'): # Verificar si hay trials antes de acceder
        for t in study.trials:
             trials_data.append({
                 "number": t.number,
                 "value": t.value,
                 "params": t.params,
                 "state": t.state.name, # Estado del trial (COMPLETE, PRUNED, FAIL)
                 #"datetime_start": t.datetime_start, # Opcional
                 #"datetime_complete": t.datetime_complete, # Opcional
             })

    best_params_result = study.best_params if hasattr(study, 'best_params') else {}
    best_value_result = study.best_value if hasattr(study, 'best_value') else None

    return {
        "best_params": best_params_result,
        "best_value": best_value_result,
        "trials": trials_data # Devolver info de los trials
    }