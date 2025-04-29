from pydantic import BaseModel, Field

class StrategyEntity(BaseModel):
    symbol: str = Field(..., description="Symbol for the strategy")
    strategy: str = Field(..., description="Name of the strategy")
    timeframe: str = Field('1m', description="Timeframe for the strategy")
    test: bool = Field(False, description="Test mode flag")
