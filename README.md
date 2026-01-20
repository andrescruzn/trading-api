# TRADING FAST API

Backend del proyecto **Trading AI**, construido con **FastAPI** sobre **Python 3.12**, orientado a trading algorítmico, IA y backtesting, usando **MySQL 8.x** como base de datos principal.

El proyecto está diseñado para escalar, mantener claridad arquitectónica y permitir evolución hacia MLOps, bots y ejecución en vivo.

---

## Stack tecnológico

- **Lenguaje:** Python 3.12
- **Framework API:** FastAPI
- **ASGI Server:** Uvicorn (standard)
- **ORM:** SQLAlchemy
- **Driver MySQL:** PyMySQL
- **Base de datos:** MySQL 8.x
- **Arquitectura:** Modular / Screaming Architecture

---

## Requisitos

- Python **3.12+**
- MySQL **8.x**
- pip actualizado
- (Opcional) `tree` para visualizar estructura

---

## Instalación

### 1️⃣ Crear entorno virtual

python3.12 -m venv .venv
source .venv/bin/activate

### Instalar requirements

pip install -r requirements.txt

### Ejecución en desarrollo

uvicorn app.main:app --reload

### Para mostrar la estructura de las carpetas instalar

brew install tree

### Para mostrar la estructura de carpetas "Los asterisco de pycache reemplazarlos con guiones al piso"

tree -d -a -I "**pycache**|.venv|.git|node_modules"

### Si quieres que tree muestre archivos y carpetas, pero sin .pyc, **pycache** ni basura, usa este comando:

tree -a -I "**pycache**|\*.pyc|.venv|.git|node_modules"

### Recomendado

tree -a -I "**pycache**|\*.pyc|.venv|.git|.DS_Store"

### No repetirlo nunca mas

alias treeclean='tree -a -I "**pycache**|\*.pyc|.venv|.git|.DS_Store|node_modules"'

Luego solamente treeclean
