# src/controllers/estrategias_controller.py
# Controlador para manejar las rutas relacionadas con las estrategias de trading
from fastapi import APIRouter, Depends
from src.models.strategy import StrategyEntity
from src.models.strategy_config import StrategyBatchRequest, StrategyConfigEntity
from src.services.strategy_service import execute_strategy, get_available_strategies, stop_strategy, simulate_strategy, create_new_strategy_config
from src.utils.jwt_utils import JWTBearer, get_current_user_id
from typing import Dict, List
from src.database.deps import get_db
from sqlalchemy.orm import Session
from src.database import schemas

router = APIRouter(dependencies=[Depends(JWTBearer())])

# Ejecutar la estrategia y devolver el resultado
@router.post("/ejecutar-estrategia")
async def ejecutar_estrategia(req: StrategyBatchRequest, db: Session = Depends(get_db)):
    resultados_ejecucion = {}
    for name, strategy_config_entity in req.root.items():
        try:
            resultado = await execute_strategy(
                                    strategy_config_entity.symbol, 
                                    strategy_config_entity.strategy, 
                                    strategy_config_entity.timeframe,
                                    strategy_config_entity.start_date,
                                    strategy_config_entity.end_date,
                                    strategy_config_entity.period,
                                    strategy_config_entity.test,
                                    strategy_config_entity.config_params,
                                    db=db
                                )
            resultados_ejecucion[name] = resultado
        except Exception as e:
            # Manejar errores por estrategia si es necesario, o dejar que el error general lo capture
            resultados_ejecucion[name] = {"success": False, "error": str(e)}
    return resultados_ejecucion

@router.post("/simular-estrategia")
async def simular_estrategia(req: StrategyBatchRequest, db: Session = Depends(get_db)):

    resultado_final = None # Para almacenar el resultado de la última simulación
    for name, strategy_config_entity in req.root.items(): # Acceder con req.root para RootModel
        resultado_final = await simulate_strategy(
                                strategy_config_entity.symbol,
                                strategy_config_entity.strategy,
                                strategy_config_entity.timeframe,
                                strategy_config_entity.start_date,
                                strategy_config_entity.end_date,
                                strategy_config_entity.period,
                                strategy_config_entity.test,
                                strategy_config_entity.config_params,
                                db=db
                            )
    return resultado_final # Devuelve el resultado de la última simulación en el batch

@router.get("/listar-estrategias")
async def listar_estrategias():
    resultado = await get_available_strategies()
    return resultado

@router.post("/detener-estrategia")
async def detener_estrategia(req: StrategyEntity):
    resultado = await stop_strategy(req.symbol, req.strategy, req.timeframe)
    return resultado

@router.post("/crear-estrategia", response_model=List[schemas.StrategyConfigResponse])
async def crear_estrategia_config(
    strategy_data: schemas.StrategyConfigCreate, 
    db: Session = Depends(get_db),
    # current_user_id: int = Depends(get_current_user_id) # Optional: if you want to associate with user
):
    # For now, user_id is None. Implement get_current_user_id if needed.
    # user_id = await get_current_user_id() # This would be an async dependency
    user_id = None 
    
    created_db_strategies = await create_new_strategy_config(db=db, strategy_data=strategy_data, user_id=user_id)
    
    response_data = []
    for db_strategy in created_db_strategies:
        response_data.append(
            schemas.StrategyConfigResponse(
                message="Strategy configuration created successfully",
                strategy_instance_name=db_strategy.strategy_instance_name,
                config=db_strategy
            )
        )
    return response_data