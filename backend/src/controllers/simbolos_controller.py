# src/controllers/simbolos_controller.py
from fastapi import APIRouter
from src.models.strategy import StrategyEntity
from src.services.symbol_service import create_active_symbol, delete_active_symbol

router = APIRouter()

@router.post("/crear-simbolo-activo")
async def crear_estrategia(req: StrategyEntity):
    """
    Crea una nueva estrategia en la base de datos.
    """
    resultado = await create_active_symbol(req.symbol, req.strategy)
    return resultado


@router.post("/eliminar-simbolo-activo")
async def eliminar_estrategia(req: StrategyEntity):
    """
    Elimina una estrategia de la base de datos.
    """
    resultado = await delete_active_symbol(req.symbol, req.strategy)
    return resultado