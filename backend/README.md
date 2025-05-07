# 📈 Trading Backend - Automatización de Estrategias de Criptomonedas

Este proyecto es el backend de un sistema de trading automatizado que permite ejecutar estrategias en tiempo real utilizando datos de Binance Futures mediante WebSocket. El backend está desarrollado en **Python** usando **FastAPI** y sigue principios de arquitectura limpia y modular.

---

## 🚀 Características Principales

* Activación de estrategias de trading (Scalping, etc.).
* Subscripción en tiempo real a WebSocket de Binance Futures.
* Análisis técnico con indicadores (EMA, RSI, volumen).
* Ejecución de órdenes y seguimiento de posiciones.
* API REST para interactuar desde el frontend (React).
* Configuración centralizada y basada en variables de entorno.

---

## 📁 Estructura de Carpetas

```bash
.
├── .env                         # Variables de entorno
├── requirements.txt             # Dependencias del proyecto
├── log_config.py                # Configuración de logs
├── start_dev.py                 # Script de inicio en entorno local
├── src/
│   ├── main.py                 # Punto de entrada principal (FastAPI)
│   ├── config/settings.py     # Configuraciones del sistema
│   ├── controllers/           # Endpoints HTTP y WebSocket
│   ├── services/              # Lógica de negocio
│   ├── database/              # Modelos ORM y esquemas Pydantic
│   ├── core/                  # Patrón Strategy y gestión de trading
│   ├── indicators/            # Indicadores técnicos
│   ├── strategies/            # Estrategias implementadas
│   └── wsclients/             # Cliente WebSocket para Binance
└── tests/                      # Tests unitarios
```

---

## ⚙️ Requisitos

* Python 3.10+
* pip (o poetry)
* Cuenta de Binance (para acceder a la API de Futures)

---

## 🛠 Instalación y Ejecución Local

1. **Clonar el repositorio**

```bash
git clone <url-del-repositorio>
cd backend
```

2. **Crear y activar un entorno virtual**

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. **Instalar dependencias**

```bash
pip install -r requirements.txt
```

4. **Crear archivo `.env`** (ya está incluido en el proyecto, pero edítalo con tus claves)

```env
BINANCE_API_KEY=your_key
BINANCE_API_SECRET=your_secret
...
```

5. **Ejecutar el servidor en desarrollo**

```bash
python start_dev.py
```

6. **Acceder a la documentación interactiva**

Visita: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 Ejecutar pruebas (si se configuran posteriormente)

```bash
pytest tests/
```

---

## 📬 Contacto

Para soporte, mejoras o colaboraciones puedes crear un issue o hacer un pull request.

---

> Este backend está diseñado para integrarse perfectamente con un frontend en React.js usando WebSocket y REST API para activación de estrategias y visualización de eventos en tiempo real.
