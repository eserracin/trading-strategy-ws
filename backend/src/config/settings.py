import os
from dotenv import load_dotenv

load_dotenv()

# === API de Binance ===
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

# === Parámetros de simulación por defecto ===
SYMBOL = os.getenv("SYMBOL", "BTCUSDT").upper()
INTERVAL = "1m"
DEFAULT_SYMBOL = "BTCUSDT"
DEFAULT_INTERVAL = "15m"
DEFAULT_PERIOD_DAYS_HISTORICAL = 90  # Historial en días para pruebas

# === Capital y gestión de riesgo ===
INITIAL_BALANCE = 10000                # Capital inicial de la simulación
RISK_PERCENT_PER_TRADE = 0.09999999999999999          # Porcentaje del capital en riesgo por trade
MIN_POSITION_SIZE = 0.001              # Tamaño mínimo de posición

# === Parámetros técnicos de indicadores ===
EMA_SHORT_LEN = 14                     # EMA rápida para cruce
EMA_LONG_LEN = 51                      # EMA lenta para cruce
RSI_LEN = 16                           # Longitud del RSI
VOL_SMA_LEN = 11                       # SMA para volumen (filtro de volumen)
EMA_DAILY_LEN = 20                     # EMA diaria para filtro de tendencia
EMA_TREND_FILTER_LEN = 275             # EMA para filtro de tendencia adicional
ATR_LEN = 10                           # Longitud del ATR
ATR_MULTIPLIER_SL = 3.50               # Multiplicador del ATR para calcular SL
RR_FACTOR_TP = 4.0                     # Relación riesgo-beneficio para calcular TP

# === Control de entradas ===
MIN_BARS_ENTRE_TRADES = 5              # Espaciado mínimo entre trades (en velas)
BREAKOUT_WINDOW = 7                    # Ventana para detectar breakout (si implementas)
MIN_REQUIRED_CANDLES = 200

# === Configuración de reintentos de red (solo si conectas a Binance real) ===
MAX_RETRIES = 5
RETRY_DELAY = 5  # segundos

# === Base de datos ===
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "host.docker.internal") # Modificado para Docker
DB_PORT = os.getenv("DB_PORT")

# === JWT / Seguridad de API ===
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRATION_TIME", 30))
