from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from controllers.http_controller import router as http_router
from controllers.ws_controller import router as ws_router

app = FastAPI(title="Trading Bot API")

# Permitir peticiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)   

# Rutas de la API
app.include_router(http_router, prefix="/api")
app.include_router(ws_router, prefix="/ws")
