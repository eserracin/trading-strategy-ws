# src/models/strategy_config.py
from pydantic import BaseModel, Field, model_validator, RootModel
from typing import Optional, Dict


class StrategyConfigParams(BaseModel):
    ATR_LEN: int
    ATR_MULTIPLIER_SL: float
    BREAKOUT_WINDOW: int
    EMA_DAILY_LEN: int
    EMA_LONG_LEN: int
    EMA_SHORT_LEN: int
    EMA_TREND_FILTER_LEN: int
    INITIAL_BALANCE: float
    MIN_BARS_ENTRE_TRADES: int
    MIN_POSITION_SIZE: float
    RISK_PERCENT_PER_TRADE: float
    RR_FACTOR_TP: float
    RSI_LEN: int
    VOL_SMA_LEN: int



class StrategyConfigEntity(BaseModel):
    symbol: str = Field(..., description="Symbol for the strategy")
    strategy: str = Field(..., description="Name of the strategy")
    timeframe: str = Field("1m", description="Timeframe for the strategy")
    start_date: Optional[str] = Field(None, description="Start date for the strategy")
    end_date: Optional[str] = Field(None, description="End date for the strategy")
    period: Optional[int] = Field(None, description="Period for the strategy")
    test: bool = Field(False, description="Test mode flag")
    config_params: StrategyConfigParams

    @model_validator(mode='after')
    def validate_fields(cls, values):
        start_date = values.start_date
        end_date = values.end_date
        period = values.period

        has_date = start_date is not None and end_date is not None
        has_only_one_date = (start_date is not None and end_date is None) or \
                            (start_date is None and end_date is not None)
        has_period = period is not None

        if has_only_one_date:
            raise ValueError("Debe proporcionar tanto la fecha de inicio como la fecha de fin o ninguna de las dos")
        if has_date and has_period:
            raise ValueError("No se puede proporcionar tanto el periodo como las fechas de inicio y fin. Elija uno.")

        return values
    
# Este modelo se usa como entrada principal para el request
class StrategyBatchRequest(RootModel[Dict[str, StrategyConfigEntity]]):
    pass
