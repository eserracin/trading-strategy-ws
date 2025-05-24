from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Union

class StrategyConfigParamsBase(BaseModel):
    ATR_LEN: Optional[int] = 10
    ATR_MULTIPLIER_SL: Optional[float] = 3.5
    BREAKOUT_WINDOW: Optional[int] = 7
    EMA_DAILY_LEN: Optional[int] = 20
    EMA_LONG_LEN: Optional[int] = 51
    EMA_SHORT_LEN: Optional[int] = 14
    EMA_TREND_FILTER_LEN: Optional[int] = 275
    INITIAL_BALANCE: Optional[float] = 1000.0
    MIN_BARS_ENTRE_TRADES: Optional[int] = 5
    MIN_POSITION_SIZE: Optional[float] = 0.001
    RISK_PERCENT_PER_TRADE: Optional[float] = 0.1
    RR_FACTOR_TP: Optional[float] = 4.0
    RSI_LEN: Optional[int] = 16
    VOL_SMA_LEN: Optional[int] = 11

class StrategyConfigBase(BaseModel):
    symbol: str = Field(..., example="SOLUSDT")
    strategy: str = Field(..., example="scalping-lp-v2") # Renamed from strategy_type_name for consistency with frontend
    timeframe: str = Field(..., example="15m")
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    period: Optional[int] = Field(default=120, example=120)
    test: Optional[bool] = Field(default=True)
    config_params: StrategyConfigParamsBase = Field(default_factory=StrategyConfigParamsBase)

class StrategyConfigCreate(BaseModel):
    # The key will be the strategy instance name, e.g., "simulacion_btc_15m_test"
    # The value will be the StrategyConfigBase
    root: Dict[str, StrategyConfigBase] = Field(..., alias='__root__')


class StrategyConfigDB(StrategyConfigBase):
    id: int
    strategy_instance_name: str # To store the dynamic key from the request
    user_id: Optional[int] = None # Assuming strategies might be linked to users

    class Config:
        orm_mode = True

# Schema for response
class StrategyConfigResponse(BaseModel):
    message: str
    strategy_instance_name: str
    config: StrategyConfigDB
