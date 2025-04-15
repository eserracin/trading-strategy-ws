import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
SYMBOL = os.getenv("SYMBOL", "BTCUSDT").upper()
INTERVAL = "1m"

INITIAL_BALANCE = 100
RISK_PERCENTAGE = 0.025
SL_DOLLAR = 0.10
TP_DOLLAR = 0.

MAX_RETRIES = 5
RETRY_DELAY = 5  # seconds