from fastapi import APIRouter, Query
from runner import strategy_runner, get_operations
from model.StrategyEntity import StrategyEntity

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