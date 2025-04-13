from fastapi import APIRouter, Query
from runner import strategy_runner, get_operations
from model.StrategyEntity import StrategyEntity
import requests
from fastapi import HTTPException

router = APIRouter()

@router.get("/estrategias")
def listar_estrategias():
    return {"disponibles": list(strategy_runner.estrategias_disponibles())}

@router.post("/ejecutar-estrategia")
def ejecutar_estrategia(req: StrategyEntity):
    print(f"symbol: {req.symbol}, strategy: {req.strategy}, test: {req.test}")
    resultado = strategy_runner.iniciar_estrategia(req.symbol, req.strategy, req.test)
    return {"mensaje": resultado}

@router.get("/operaciones")
def obtener_operaciones():
    operaciones = get_operations()
    return {"operaciones": operaciones}

@router.get("/symbols")
async def get_symbols(q: str = Query(None, min_length=1)):
    all_symbols = strategy_runner.get_symbols()
    if q:
        symbols = [symbol for symbol in all_symbols if q.lower() in symbol.lower()]
        return {"symbols": symbols}
    return {"symbols": all_symbols}

@router.get("/market-data/{symbol}")
def get_market_data(symbol: str):
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

    print('result', result)

    return result