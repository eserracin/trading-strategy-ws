from src.services.strategy_runtime import StrategyRunner
import requests
from fastapi import HTTPException

async def execute_strategy(symbol: str, strategy_name: str, test: bool = False):
    strategy_runner = StrategyRunner()
    resultado = list(strategy_runner.iniciar_estrategia(symbol, strategy_name, test))
    return {"success": True, "data": resultado}

async def stop_strategy(symbol: str, strategy_name: str):
    strategy_runner = StrategyRunner()
    resultado = strategy_runner.detener_estrategia(symbol, strategy_name)
    return {"success": True, "data": resultado}

async def get_available_strategies():
    strategy_runner = StrategyRunner()
    resultado = strategy_runner.estrategias_disponibles()
    return {"success": True, "data": resultado}

async def get_symbols(q: str = None):
    strategy_runner = StrategyRunner()
    all_symbols = strategy_runner.get_symbols()
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