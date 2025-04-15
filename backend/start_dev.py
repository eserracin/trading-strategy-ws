import os
import sys
from uvicorn import run

# Obtener ruta absoluta del directorio actual
current_dir = os.path.dirname(os.path.abspath(__file__))

# Agregar la carpeta src al PYTHONPATH
sys.path.append(os.path.join(current_dir, 'src'))

# Ejecutar la app FastAPI desde src/main.py
if __name__ == "__main__":
    run("main:app", host="0.0.0.0", port=7000, reload=True, app_dir="src")