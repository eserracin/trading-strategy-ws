# src/controllers/http_controller.py
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


@router.get("/symbols")
async def obtener_simbolos(q: str = Query(None, min_length=1)):
    resultado = await get_symbols(q)
    return resultado


@router.get("/market-data/{symbol}")
async def obtener_data_mercado(symbol: str):
    resultado = await get_market_data(symbol)
    return resultado