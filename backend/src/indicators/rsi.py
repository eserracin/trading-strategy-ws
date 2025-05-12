# src/indicators/rsi.py
import pandas_ta as ta
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
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    # Una implementación más directa usando ewm (alpha = 1/period)
    # Nota: pandas ewm con adjust=False se acerca a Wilder's
    avg_gain = gain.ewm(alpha=1/period, adjust=False, min_periods=0).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False, min_periods=0).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    rsi.iloc[:period] = pd.NA

    return rsi

def rsi_ta(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate the Relative Strength Index (RSI) using the pandas_ta library.

    Parameters:
    series (pd.Series): The input time series data.
    period (int): The number of periods to use for the RSI calculation.

    Returns:
    pd.Series: The calculated RSI values.
    """
    return ta.rsi(series, length=period)