# src/models/open_order.py
from pydantic import BaseModel
from datetime import datetime

class OpenOrder(BaseModel):
    date: datetime
    pair: str
    type: str
    side: str
    price: float
    amount: float
    strategy: str
    status: str = 'open'