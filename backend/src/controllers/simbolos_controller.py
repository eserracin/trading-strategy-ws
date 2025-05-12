# src/controllers/simbolos_controller.py
from fastapi import APIRouter, Query, Depends
from src.models.symbol_active import SymbolActiveEntity
from src.services.symbol_service import create_active_symbol, delete_active_symbol, get_symbols, get_all_active_symbols
from src.database.deps import get_db
from sqlalchemy.orm import Session

router = APIRouter()

@router.post("/crear-simbolo-activo")
async def crear_simbolo_activo(req: SymbolActiveEntity,  db: Session = Depends(get_db)):
    """
    Crea una nueva estrategia en la base de datos.
    """
    resultado = await create_active_symbol(req.keySymbolActive, req.symbol, req.strategy, req.timeframe, db=db)
    return {"success": True, "data": resultado}


# @router.post("/eliminar-simbolo-activo")
# async def eliminar_estrategia(req: StrategyEntity):
#     """
#     Elimina una estrategia de la base de datos.
#     """
#     resultado = await delete_active_symbol(req.symbol, req.strategy)
#     return resultado

@router.post("/obteber-estrategias-activas")
async def obtener_estrategias_activas(db: Session = Depends(get_db)):
    """
    Obtiene todas las estrategias activas de la base de datos.
    """
    resultado = await get_all_active_symbols(db=db)
    return {"success": True, "data": resultado}

@router.get("/obtener-simbolos")
async def obtener_simbolos(q: str = Query(None, min_length=1)):
    resultado = await get_symbols(q)
    return resultado