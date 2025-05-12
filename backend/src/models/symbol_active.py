from pydantic import BaseModel, Field

class SymbolActiveEntity(BaseModel):
    keySymbolActive: str = Field(..., description="Key symbol strategy")
    symbol: str = Field(..., description="Symbol for the strategy")
    strategy: str = Field(..., description="Name of the strategy")
    timeframe: str = Field('1m', description="Timeframe for the strategy")