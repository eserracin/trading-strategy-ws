# src/controllers/estrategias_controller.py
from fastapi import APIRouter, Depends
from src.database.deps import get_db
from sqlalchemy.orm import Session
from src.models.auth import AuthenticationEntity
from src.services.auth_service import register_user, login_user

router = APIRouter()

# Ejecutar la estrategia y devolver el resultado
@router.post("/registrar-usuario")
async def registrar_usuario(req: AuthenticationEntity, db: Session = Depends(get_db)):
    resultado = await register_user(req.username, req.email, req.password, req.test, db=db)
    return resultado

@router.post("/iniciar-sesion")
async def autenticar_usuario(req: AuthenticationEntity, db: Session = Depends(get_db)):
    resultado = await login_user(req.username, req.email, req.password, req.test, db=db)
    return resultado
