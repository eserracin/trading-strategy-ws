# src/indicators/ema.py
import pandas as pd

def ema(series: pd.Series, period: int):
    """
    Calculates the Exponential Moving Average (EMA) for a given series of values.

    Args:
        series (pd.Series): A pandas Series containing the values for which the EMA needs to be calculated.
        period (int): The period over which the EMA should be calculated.

    Returns:
        pd.Series: A pandas Series containing the calculated EMA values.
    """
    if not isinstance(series, pd.Series):
        series = pd.Series(series)


    # Calculate the multiplier for the EMA formula
    multiplier = 2 / (period + 1)

    # Initialize the EMA series with the first value of the input series
    ema = [series.iloc[0]]

    # Calculate the EMA values for the remaining periods
    for i in range(len(series) - 1):
        ema.append((series.iloc[i + 1] * multiplier) + (ema[i] * (1 - multiplier)))

    # Return the EMA series as a pandas Series
    return pd.Series(ema, index=series.index)

def ema_gpt(series: pd.Series, period: int):
    return series.ewm(span=period, adjust=False).mean()