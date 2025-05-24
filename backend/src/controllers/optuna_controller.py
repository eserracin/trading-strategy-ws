# src/controllers/optuna_controller.py
from fastapi import APIRouter, Depends
from src.models.optuna_request import OptunaRequest
from src.services.optuna_service import run_optuna_optimization
from src.utils.jwt_utils import JWTBearer
from src.database.deps import get_db
from sqlalchemy.orm import Session

router = APIRouter(dependencies=[Depends(JWTBearer())])

@router.post("/optimizar-estrategia")
async def optimizar_estrategia(req: OptunaRequest, db : Session = Depends(get_db)):
    return run_optuna_optimization(req.dict(), db=db)
