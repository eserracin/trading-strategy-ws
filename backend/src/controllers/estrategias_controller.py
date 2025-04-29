from fastapi import APIRouter
from src.models.strategy import StrategyEntity
from src.services.strategy_service import execute_strategy, get_available_strategies, stop_strategy

router = APIRouter()

# Ejecutar la estrategia y devolver el resultado
@router.post("/ejecutar-estrategia")
async def ejecutar_estrategia(req: StrategyEntity):
    resultado = await execute_strategy(req.symbol, req.strategy, req.timeframe, req.test)
    return resultado

@router.get("/listar-estrategias")
async def listar_estrategias():
    resultado = await get_available_strategies()
    return resultado

 # Detener la estrategia y devolver el resultado
@router.post("/detener-estrategia")
async def detener_estrategia(req: StrategyEntity):
    resultado = await stop_strategy(req.symbol, req.strategy)
    return resultado