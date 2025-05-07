# src/database/init_db.py
from .database import Base, engine
from .models import EstrategiaActiva, Orden, Transaccion

def init_db():
    """Create the database tables if they do not exist yet."""
    # Create all tables in the database which are defined by Base's subclasses
    Base.metadata.create_all(bind=engine)