# src/models/optuna_request.py
from pydantic import BaseModel
from typing import Optional

class OptunaRequest(BaseModel):
    symbol: str
    strategy: str
    timeframe: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    period: Optional[int] = 30
    test: Optional[bool] = True
    n_trials: Optional[int] = 30
    initial_balance: Optional[float] = 10000
