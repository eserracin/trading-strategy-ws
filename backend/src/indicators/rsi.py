# src/indicators/rsi.py
import pandas as pd

def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate the Relative Strength Index (RSI) for a given time series.

    Parameters:
    series (pd.Series): The input time series data.
    period (int): The number of periods to use for the RSI calculation.

    Returns:
    pd.Series: The calculated RSI values.
    """
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    return rsi