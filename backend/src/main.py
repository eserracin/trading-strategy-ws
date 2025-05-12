# src/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from controllers.ws_controller import router as ws_router
from controllers.simbolos_controller import router as simbolos_router
from controllers.estrategias_controller import router as estrategias_router
from controllers.auth_controller import router as auth_router
from src.database.init_db import init_db
import signal
import logging
import sys
import os

app = FastAPI(title="Trading Bot API")

def setup_logger():
    logger = logging.getLogger("TRADING_BOT") 
    logger.setLevel(logging.INFO)

    # Evitar duplicar handler si el logger ya esta configurado
    if  not logger.hasHandlers():
        # Configurar el handler de consola
        handler = logging.StreamHandler()

        # Formatear los mensajes de log
        formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(name)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)

        # Agregar el handler al logger
        logger.addHandler(handler)

    return logger

# Inicializar el logger
logger = setup_logger()

# Funcion que gestionara las señaes SIGINT y SIGTERM
def signal_handler(signum, frame):
    logger.info(f"🚩 Señal recibida ({signum}). Cerrando estrategias activas...")
    try:
        from src.services.strategy_realtime_runner import strategy_runner
        strategy_runner.detener_todas()
        logger.info("✅ Todas las estrategias fueron detenidas correctamente.")
    except Exception as e:
        logger.error(f"❌ Error al detener las estrategias: {e}")
    finally:
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

# Configurar la respuesta a las señales SIGINT y SIGTERM
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Permitir peticiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)   

# Rutas de la API
app.include_router(simbolos_router, prefix="/api/symbol")
app.include_router(estrategias_router, prefix="/api/strategy")
app.include_router(auth_router, prefix="/api/auth")
# Rutas de WebSocket
app.include_router(ws_router, prefix="/ws")

# 🚀 Inicializar base de datos en el arranque
@app.on_event("startup")
async def startup_event():
    init_db()
    logger.info("🚀 Base de datos inicializada correctamente.")
