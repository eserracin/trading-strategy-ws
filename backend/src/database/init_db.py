# src/database/init_db.py
from .database import Base, engine
from .models import EstrategiaActiva, Orden, Transaccion, User, KlinesCache

def init_db():
    """Create the database tables if they do not exist yet."""
    # Create all tables in the database which are defined by Base's subclasses
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Database initialized successfully.")