# src/services/symbol_service.py
from fastapi import Depends
from sqlalchemy.orm import Session
from src.database.deps import get_db
from src.database.models import EstrategiaActiva
from src.services.strategy_realtime_runner import StrategyRealTimeRunner
from fastapi import HTTPException

strategy_runner = StrategyRealTimeRunner()

async def create_active_symbol(key: str, symbol: str, strategy_name: str, timeframe: str,  db: Session = None):
    """
    Crea una nueva estrategia en la base de datos.
    """
    estrategia = EstrategiaActiva(
        keySymbolActive=key,
        symbol=symbol,
        strategyName=strategy_name,
        timeframe=timeframe,
        estado="activa",
    )

    db.add(estrategia)
    db.commit()
    db.refresh(estrategia)
    return estrategia

async def delete_active_symbol(symbol: str, strategy_name: str, db: Session = Depends(get_db)):
    """
    Elimina una estrategia de la base de datos.
    """
    estrategia = db.query(EstrategiaActiva).filter(
        EstrategiaActiva.symbol == symbol,
        EstrategiaActiva.nombre_estrategia == strategy_name
    ).first()

    if not estrategia:
        raise HTTPException(status_code=404, detail="Estrategia no encontrada")

    db.delete(estrategia)
    db.commit()
    return {"message": "Estrategia eliminada con éxito"}

async def get_all_active_symbols(db: Session = Depends(get_db)):
    """
    Obtiene todas las estrategias activas de la base de datos.
    """
    estrategias = db.query(EstrategiaActiva).filter(
        EstrategiaActiva.estado == "activa"
    ).all()

    if not estrategias:
        raise HTTPException(status_code=404, detail="No hay estrategias activas")

    return estrategias


async def get_symbols(q: str = None):
    all_symbols = strategy_runner.get_symbols()
    if not q:
        return {"success": True, "data": all_symbols}
    symbols = [symbol for symbol in all_symbols if q.lower() in symbol.lower()]
    return {"success": True, "data": symbols}