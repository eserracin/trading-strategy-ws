# src/services/strategy_service.py
from src.services.strategy_realtime_runner import StrategyRealTimeRunner
from src.services.strategy_simulation_runner import StrategySimulatorRunner
from src.core import ContextStrategy
import requests
from fastapi import HTTPException

strategy_realtime = StrategyRealTimeRunner()

async def execute_strategy(symbol: str, strategy_name: str, timeframe: str, test: bool = False):
    resultado = strategy_realtime.iniciar_estrategia(symbol, strategy_name, timeframe, test)
    return {"success": True, "data": resultado}

async def simulate_strategy(symbol: str, strategy_name: str, timeframe: str, start_date: str = None, end_date: str = None, period: int = None, test: bool = False):
    strategy_simulator = StrategySimulatorRunner(use_mock_client=test, strategy=strategy_name)
    resultado = strategy_simulator.simular(symbol=symbol, interval=timeframe, start_date=start_date, end_date=end_date, period_days=period)
    return {"success": True, "data": resultado}

async def stop_strategy(symbol: str, strategy_name: str, timeframe: str):
    key = f"{symbol}_{strategy_name}"
    # print(f"Deteniendo estrategia: {strategy_realtime.task}")
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