# 📈 Trading Strategy Dashboard - Frontend

Este es el frontend de una plataforma de estrategias de trading en tiempo real. Utiliza **React**, **Vite**, **Tailwind CSS**, y **Zustand** para la gestión de estado, con soporte para WebSockets y múltiples idiomas (i18n con español e inglés).

## 🚀 Funcionalidades

- Visualización de **símbolos activos** y señales de entrada.
- Activación/desactivación de estrategias específicas por símbolo, estrategia y temporalidad.
- Soporte **multilenguaje** (español/inglés).
- Integración con API REST y WebSocket.
- Configuración de **temporalidades** desde archivo JSON.
- Panel principal de estrategias en tiempo real.

## 📂 Estructura del Proyecto

```bash
├── public/
│   └── locales/            # Traducciones i18n (en/es)
├── src/
│   ├── assets/             # Recursos como íconos y configuraciones
│   ├── components/         # Componentes principales de la UI
│   ├── hooks/              # Custom hooks como useCandleStream
│   ├── services/           # Servicios REST y WebSocket
│   ├── store/              # Estado global (Zustand)
│   ├── App.jsx             # Componente principal
│   └── main.jsx            # Punto de entrada
├── .env                    # Variables de entorno
├── package.json            # Dependencias y scripts
├── tailwind.config.js      # Configuración de Tailwind
└── vite.config.js          # Configuración de Vite

# 1. Clonar el repositorio (si aplica)
git clone https://github.com/tu-usuario/tu-repo.git
cd nombre-del-proyecto

# 2. Instalar dependencias
npm install

# 3. Crear archivo .env y definir variables necesarias
cp .env.example .env
# Asegúrate de definir variables como:
# VITE_API_URL=https://api.ejemplo.com
# VITE_WS_URL=wss://ws.ejemplo.com

# 4. Ejecutar en modo desarrollo
npm run dev
