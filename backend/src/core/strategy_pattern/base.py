# src/core/strategy_pattern/base.py
from abc import ABC, abstractmethod

class BaseStrategy(ABC):

    @abstractmethod
    def obtener_historial_inicial(self, symbol, interval='15m', period=50):
        pass

    @abstractmethod
    def check_entry(self, data: dict):
        pass

    @abstractmethod
    def calculate_position_size(self, entry_price: float, sl_price: float) -> float:
        pass