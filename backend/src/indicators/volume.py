import pandas as pd

def volume_sma(volume: pd.Series, period: int) -> pd.Series:
    """
    Calculate the Simple Moving Average (SMA) of volume.

    :param volume: A pandas Series representing the volume data.
    :param period: The number of periods over which to calculate the SMA.
    :return: A pandas Series containing the SMA of the volume.
    """
    return volume.rolling(window=period).mean()