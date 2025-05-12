# src/indicators/crossoverunder.py
import pandas as pd


def crossover(series1: pd.Series, series2: pd.Series) -> pd.Series:
    """
    Calculate the crossover between two moving averages.
    
    Parameters:
    - series: The price series to calculate the moving averages on.
    - short_window: The short window for the moving average.
    - long_window: The long window for the moving average.
    
    Returns:
    - A Series with 1 for a bullish crossover, -1 for a bearish crossover, and 0 for no crossover.
    """
    condicion_anterior = series1.shift(1) <= series2.shift(1)
    condicion_actual = series1 > series2

    hubo_crossover = condicion_anterior & condicion_actual
    
    return hubo_crossover

def crossunder(series1: pd.Series, series2: pd.Series) -> pd.Series:
    """
    Calculate the crossunder between two moving averages.
    
    Parameters:
    - series: The price series to calculate the moving averages on.
    - short_window: The short window for the moving average.
    - long_window: The long window for the moving average.
    
    Returns:
    - A Series with 1 for a bullish crossover, -1 for a bearish crossover, and 0 for no crossover.
    """
    condicion_anterior = series1.shift(1) >= series2.shift(1)
    condicion_actual = series1 < series2

    hubo_crossunder = condicion_anterior & condicion_actual
    
    return hubo_crossunder