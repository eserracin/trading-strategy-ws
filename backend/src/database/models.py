# src/database/models.py
from sqlalchemy import (
    Column, 
    Integer, 
    String, 
    Numeric, 
    ForeignKey, 
    DateTime, 
    UniqueConstraint,
    Index,
    func,
    Boolean)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB # For PostgreSQL JSON support
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


class StrategyConfiguration(Base):
    __tablename__ = "estrategias_configuracion"

    id = Column(Integer, primary_key=True, index=True)
    strategy_instance_name = Column(String(255), unique=True, index=True, nullable=False)
    symbol = Column(String(50), nullable=False)
    strategy_type_name = Column(String(100), nullable=False) # Corresponds to 'strategy' field from request
    timeframe = Column(String(20), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    period = Column(Integer, nullable=True)
    test = Column(Boolean, default=True)
    config_params = Column(JSONB, nullable=False) # Store config_params as JSON
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Optional link to user
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User") # Define relationship if you have a User model and want to link strategies

    __table_args__ = (
        Index('ix_estrategias_configuracion_user_id', 'user_id'),
    )

    def __repr__(self):
        return f"<StrategyConfiguration(name='{self.strategy_instance_name}', symbol='{self.symbol}', strategy='{self.strategy_type_name}')>"


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

class KlinesCache(Base):
    __tablename__ = "klines_cache"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False)
    interval = Column(String(10), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False) # Siempre almacenar en UTC
    open = Column(Numeric(precision=18, scale=8))
    high = Column(Numeric(precision=18, scale=8))
    low = Column(Numeric(precision=18, scale=8))
    close = Column(Numeric(precision=18, scale=8))
    volume = Column(Numeric(precision=24, scale=8))
    # close_time de Binance no es necesario aquí, el timestamp de apertura es suficiente para identificar la vela

    __table_args__ = (
        UniqueConstraint('symbol', 'interval', 'timestamp', name='uq_klines_cache_symbol_interval_timestamp'),
        Index('ix_klines_cache_symbol_interval_timestamp', 'symbol', 'interval', 'timestamp'),
    )

    def __repr__(self):
        return f"<KlinesCache(symbol='{self.symbol}', interval='{self.interval}', timestamp='{self.timestamp}')>"