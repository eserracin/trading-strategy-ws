# src/database/models.py
from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from .database import Base

class EstrategiaActiva(Base):
    __tablename__ = "estrategias_activas"

    id = Column(Integer, primary_key=True, index=True)
    keySymbolActive = Column(String(50), unique=True, index=True)
    symbol = Column(String(20), nullable=False)
    strategyName = Column(String(100), nullable=False)
    timeframe = Column(String(20), nullable=False)  # M1, M5, H1, D1, etc.
    estado = Column(String(20), default="activa")
    fecha_inicio = Column(DateTime(timezone=True), server_default=func.now())
    fecha_cierre = Column(DateTime(timezone=True))

    # Relaciones
    ordenes = relationship("Orden", back_populates="estrategia", cascade="all, delete-orphan")
    transacciones = relationship("Transaccion", back_populates="estrategia", cascade="all, delete-orphan")


class Orden(Base):
    __tablename__ = "ordenes"

    id = Column(Integer, primary_key=True, index=True)
    estrategia_id = Column(Integer, ForeignKey("estrategias_activas.id"))
    tipo = Column(String(20))  # Entrada, TakeProfit, StopLoss
    precio_entrada = Column(Numeric)
    precio_salida = Column(Numeric)
    resultado = Column(Numeric)
    estado = Column(String(20), default="abierta")
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())

    estrategia = relationship("EstrategiaActiva", back_populates="ordenes")


class Transaccion(Base):
    __tablename__ = "transacciones"

    id = Column(Integer, primary_key=True, index=True)
    estrategia_id = Column(Integer, ForeignKey("estrategias_activas.id"))
    tipo = Column(String(20))  # Compra/Venta/StopOut
    monto = Column(Numeric)
    fecha_transaccion = Column(DateTime(timezone=True), server_default=func.now())

    estrategia = relationship("EstrategiaActiva", back_populates="transacciones")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
