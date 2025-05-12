# src/core/strategy_pattern/base.py
from abc import ABC, abstractmethod
import pandas as pd

class BaseStrategy(ABC):

    @abstractmethod
    def obtener_historial_inicial_con_periodo(self, symbol, interval='15m', period=50):
        pass

    @abstractmethod
    def obtener_historial_inicial_con_rango(self, symbol, interval='15m', startDate=None, endDate=None):
        pass

    @abstractmethod
    def calcular_indicadores(self, df: pd.DataFrame) -> pd.DataFrame:
        pass    

    @abstractmethod
    def check_entry(self, data: dict):
        pass

    @abstractmethod
    def calculate_position_size(self, entry_price: float, sl_price: float) -> float:
        pass