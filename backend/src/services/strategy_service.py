# src/services/strategy_service.py
from src.services.strategy_realtime_runner import StrategyRealTimeRunner
from src.services.strategy_simulation_runner import StrategySimulatorRunner
from src.core import ContextStrategy
from src.models.strategy_config import StrategyConfigParams # Importar el modelo
import requests
from fastapi import HTTPException
from typing import Optional # Para el tipo opcional
from sqlalchemy.orm import Session
from src.database import models, schemas # Import models and schemas
from datetime import datetime

strategy_realtime = StrategyRealTimeRunner()

async def execute_strategy(
        symbol: str, 
        strategy_name: str, 
        timeframe: str, 
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: Optional[int] = None,
        test: bool = False,
        config_params: Optional[StrategyConfigParams] = None,
        db: Session = None
        ):
    
    strategy_realtime.configure_runner(
        symbol=symbol,
        strategy_name=strategy_name,
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date,
        period_days=period,
        db_session=db,
        config_params_obj=config_params
    )

    resultado = strategy_realtime.iniciar_estrategia(test=test)
    return {"success": True, "data": resultado}

async def simulate_strategy(
    symbol: str,
    strategy_name: str,
    timeframe: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period: Optional[int] = None,
    test: bool = False,
    config_params: Optional[StrategyConfigParams] = None,
    db: Session = None
):
    strategy_simulator = StrategySimulatorRunner(db_session=db, use_mock_client=test, strategy=strategy_name)
    resultado = strategy_simulator.simular(
        symbol=symbol,
        interval=timeframe,
        start_date=start_date,
        end_date=end_date,
        period_days=period,
        config_params_obj=config_params
    )
    # El método simular ya debería devolver la estructura completa con "success" y "data" o "error"
    return resultado

async def stop_strategy(symbol: str, strategy_name: str, timeframe: str):
    key = f"{symbol}_{strategy_name}"
    if key not in strategy_realtime.task:
        raise HTTPException(status_code=404, detail="Estrategia no encontrada")

    resultado = strategy_realtime.detener_estrategia(symbol, strategy_name, timeframe)
    return {"success": True, "data": resultado}

async def get_available_strategies():
    resultado = list(ContextStrategy.STRATEGIES.keys())
    return {"success": True, "data": resultado}

async def get_symbols(q: str = None):
    all_symbols = strategy_realtime.get_symbols()
    if not q:
        return {"success": True, "data": all_symbols}
    symbols = [symbol for symbol in all_symbols if q.lower() in symbol.lower()]
    return {"success": True, "data": symbols}

async def get_market_data(symbol: str):
    url = f"https://fapi.binance.com/fapi/v1/ticker/24hr?symbol={symbol.upper()}"
    response = requests.get(url)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Error al obtener los datos del mercado")
    
    data = response.json()

    result  = {
        "symbol": data["symbol"],
        "priceChange": data["priceChange"],
        "priceChangePercent": data["priceChangePercent"],
        "weightedAvgPrice": data["weightedAvgPrice"],
        "lastPrice": data["lastPrice"],
        "lastQty": data["lastQty"],
        "openPrice": data["openPrice"],
        "highPrice": data["highPrice"],
        "lowPrice": data["lowPrice"],
        "volume": data["volume"],
        "quoteVolume": data["quoteVolume"],
        "openTime": data["openTime"],
        "closeTime": data["closeTime"],
        "firstId": data["firstId"],
        "lastId": data["lastId"],
        "count": data["count"]
    }

    return {"success": True, "data": result}

async def create_new_strategy_config(
    db: Session, 
    strategy_data: schemas.StrategyConfigCreate, 
    user_id: Optional[int] = None
) -> list[schemas.StrategyConfigDB]:
    created_strategies = []
    for instance_name, config in strategy_data.root.items():
        # Convert string dates to datetime objects if they exist
        start_date_obj = datetime.fromisoformat(config.start_date) if config.start_date else None
        end_date_obj = datetime.fromisoformat(config.end_date) if config.end_date else None

        db_strategy_config = models.StrategyConfiguration(
            strategy_instance_name=instance_name,
            symbol=config.symbol,
            strategy_type_name=config.strategy, # from schema
            timeframe=config.timeframe,
            start_date=start_date_obj,
            end_date=end_date_obj,
            period=config.period,
            test=config.test,
            config_params=config.config_params.model_dump(), # Convert Pydantic model to dict for JSONB
            user_id=user_id
        )
        db.add(db_strategy_config)
        try:
            db.commit()
            db.refresh(db_strategy_config)
            created_strategies.append(schemas.StrategyConfigDB.from_orm(db_strategy_config))
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error saving strategy {instance_name}: {str(e)}")
    return created_strategies