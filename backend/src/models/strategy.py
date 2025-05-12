# src/models/strategy.py
from pydantic import BaseModel, Field, model_validator, validator
from typing import Optional

class StrategyEntity(BaseModel):
    symbol: str = Field(..., description="Symbol for the strategy")
    strategy: str = Field(..., description="Name of the strategy")
    timeframe: str = Field('1m', description="Timeframe for the strategy")
    start_date: Optional[str] = Field(None, description="Start date for the strategy")
    end_date: Optional[str] = Field(None, description="End date for the strategy")
    period: Optional[int] = Field(None, description="Period for the strategy")
    test: bool = Field(False, description="Test mode flag")

    # Validador de campos
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
            raise ValueError("Nose puede proporcionar tanto el periodo como las fechas de inicio y fin, Elija uno")
    
        return values