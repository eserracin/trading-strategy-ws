from fastapi import APIRouter, Query
from src.models.strategy import StrategyEntity
from src.services.strategy_service import (
    execute_strategy, 
    get_available_strategies,
    get_symbols,
    get_market_data,
    stop_strategy,
    )

router = APIRouter()

@router.get("/estrategias")
async def listar_estrategias():
    resultado = await get_available_strategies()
    return resultado

# Ejecutar la estrategia y devolver el resultado
@router.post("/ejecutar-estrategia")
async def ejecutar_estrategia(req: StrategyEntity):
    resultado = await execute_strategy(req.symbol, req.strategy, req.test)
    return resultado

 # Detener la estrategia y devolver el resultado
@router.post("/detener-estrategia")
async def detener_estrategia(req: StrategyEntity):
    resultado = await stop_strategy(req.symbol, req.strategy)
    return resultado

# @router.get("/operaciones")
# def obtener_operaciones():
#     operaciones = get_operations()
#     return {"operaciones": operaciones}

@router.get("/symbols")
async def obtener_simbolos(q: str = Query(None, min_length=1)):
    resultado = await get_symbols(q)
    return resultado


@router.get("/market-data/{symbol}")
async def obtener_data_mercado(symbol: str):
    resultado = await get_market_data(symbol)
    return resultado