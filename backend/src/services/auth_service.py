from src.database.deps import get_db
from src.database.models import User
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException, Depends
from utils.auth_utils import verify_password, hash_password, create_access_token


async def register_user(username: str, email: str, password: str, test: bool = False, db: Session = None):
    # Lógica para registrar un usuario
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="El nombre de usuario ya está en uso")
    
    user = User(username=username, email=email, hashed_password=hash_password(password))

    db.add(user)
    db.commit()
    db.refresh(user)

    return {"success": True, "message": "Usuario registrado exitosamente"}

async def login_user(username: str = None, email: str = None, password: str = None, test: bool = False, db: Session = None):
    # Lógica para iniciar sesión
    user = db.query(User).filter(
            or_(
                User.email == email if email else None,
                User.username == username if username else None
            )
        ).first()
    
    if not user:
        raise HTTPException(status_code=400, detail="Usuario no encontrado")
    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Contraseña incorrecta") 
    
    token = create_access_token(data={"sub": user.username})
    
    return {"success": True, "access_token": token, "token_type": "bearer"}


