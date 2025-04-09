from pydantic import BaseModel, Field

class StrategyEntity(BaseModel):
    symbol: str = Field(..., description="Symbol for the strategy")
    strategy: str = Field(..., description="Name of the strategy")
    test: bool = Field(False, description="Test mode flag")
