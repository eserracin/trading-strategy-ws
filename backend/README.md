# 📈 Binance Futures Scalping Bot

Este proyecto implementa una estrategia automatizada de scalping basada en WebSockets, ejecutando órdenes en el mercado de Binance Futures utilizando Python.

---

## 🚀 Características

- Estrategia de scalping con filtro de tendencia diario (EMA 20).
- Gestión automática de órdenes de entrada, Stop Loss (SL) y Take Profit (TP).
- Diseño modular siguiendo principios SOLID y patrones Strategy.
- Ejecución mediante WebSocket para datos en tiempo real.

---

## 🛠️ Requisitos

- Python 3.8 o superior.
- Cuenta en Binance Futures (recomendable probar primero en Testnet).

---

## 📂 Estructura del Proyecto backend

```
backend/
├── src/
│   ├── api/                   # NUEVO: Rutas y controladores FastAPI
│   │   ├── routes.py
│   │   └── websocket.py
│   ├── core/                  # Tus estrategias base y contexto
│   ├── trading_strategies/    # Tus estrategias concretas (como scalping-lp)
│   ├── trade_manager/
│   ├── indicators/
│   ├── wsclient/
│   ├── runner.py              # NUEVO: Ejecuta las estrategias
│   ├── main.py                # Punto de entrada FastAPI
│   └── config.py
├── requirements.txt
```

---

## ⚙️ Instalación

### 1. Clona el repositorio

```bash
git clone <url-repositorio>
cd trading-strategy-ws
```

### 2. Crea un entorno virtual

```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
```

### 3. Instala dependencias

```bash
pip install -r requirements.txt
```

---

## 🔑 Configuración

Crea un archivo `.env` en la raíz del proyecto con tus credenciales de Binance:

```env
BINANCE_API_KEY=tu_api_key
BINANCE_API_SECRET=tu_secret_key
```

**Nota**: Puedes obtener estas claves en tu cuenta Binance Futures. Recomendable utilizar primero la Testnet para realizar pruebas seguras.

---

## 🚨 Ejecución del Bot

Ejecuta el bot desde consola especificando el símbolo que deseas operar:

```bash
cd backend
python start_dev.py
```

Reemplaza `BTCUSDT` con cualquier otro par disponible en Binance Futures.

---

## 📖 Logs y Monitoreo

Por defecto, el bot mostrará en consola información sobre las órdenes ejecutadas y posibles errores. Los logs pueden configurarse o extenderse fácilmente mediante el módulo `logging`.

---

## 🧪 Pruebas (Testnet)

Se recomienda probar el bot primero en Binance Futures Testnet:

- URL Binance Futures Testnet: [https://testnet.binancefuture.com](https://testnet.binancefuture.com)
- Crea claves API específicas para Testnet.
- Configura esas claves en el archivo `.env`.

---

## 📌 Recomendaciones Finales

- Verifica siempre las reglas específicas del símbolo en Binance Futures.
- Supervisa constantemente el bot cuando esté operando en producción.
- Mantén siempre actualizado el código y las dependencias.

---

🚧 **Advertencia**: Utiliza esta estrategia bajo tu propio riesgo. El trading de futuros implica alto riesgo financiero. Asegúrate de entender completamente su funcionamiento antes de operar con dinero real.

