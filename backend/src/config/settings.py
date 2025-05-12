# src/config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
SYMBOL = os.getenv("SYMBOL", "BTCUSDT").upper()
INTERVAL = "1m"

# Configuracion del Capital
INITIAL_BALANCE = 10000
RISK_PERCENTAGE = 0.015
RISK_PERCENT_PER_TRADE = 0.02
SL_DOLLAR = 0.10
TP_DOLLAR = 0.65

# Parámetros de indicadores
EMA_SHORT_LEN = 9
EMA_LONG_LEN = 26
EMA_TREND_LEN = 50 # EMA50 del script original (M15)
RSI_LEN = 12
VOL_SMA_LEN = 20
EMA_DAILY_LEN = 20 # EMA para el filtro diario
EMA_TREND_FILTER_LEN = 200

# Control de frecuencia
MIN_BARS_ENTRE_TRADES = 3 # (bar_index - ultima_entrada) > 1 significa que si entramos en i, la prox es i+2

MAX_RETRIES = 5
RETRY_DELAY = 5  # seconds
ATR_LEN = 14
ATR_MULTIPLIER_SL = 1.5
RR_FACTOR_TP = 2.0

# Variable to connect to database
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

# Variable to use JWT
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRATION_TIME", 30))


# Valores por defecto para la simulación
DEFAULT_SYMBOL = "BTCUSDT"
DEFAULT_INTERVAL = "15m"
DEFAULT_PERIOD_DAYS_HISTORICAL = 90 # Para obtener_historial_inicial_con_periodo
MIN_POSITION_SIZE = 0.001