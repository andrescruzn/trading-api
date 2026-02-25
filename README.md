# TRADING FAST API

Backend del proyecto **Trading AI**, construido con **FastAPI** sobre **Python 3.12**, orientado a trading algorítmico, IA y backtesting, usando **MySQL 8.x** como base de datos principal.

El proyecto está diseñado para escalar, mantener claridad arquitectónica y permitir evolución hacia MLOps, bots y ejecución en vivo.

---

## Estado del proyecto

| Módulo | Estado | Descripción |
|--------|--------|-------------|
| M1 — Auth & Web UI | ✅ Completo | Login password/OTP, sesiones JWT, roles, dashboard |
| M2 — Market Data | ✅ Completo | Exchanges, símbolos, timeframes, velas OHLCV via ccxt |
| M3 — Feature Engineering | 📌 Siguiente | RSI, ATR, EMA, MACD, Bollinger Bands, régimen de mercado |
| M4 — Accounts & Portfolio | ⬜ Pendiente | Cuentas de exchange, balances, snapshots |
| M5 — Strategies | ⬜ Pendiente | Reglas de entrada/salida, datasets de backtesting |
| M6 — AI Agent / Models | ⬜ Pendiente | Integración Ollama local, predicciones |
| M7 — Bots & Signals | ⬜ Pendiente | Bots automáticos, señales BUY/SELL/HOLD |
| M8 — Orders & Execution | ⬜ Pendiente | Envío de órdenes al exchange, fills, posiciones |
| M9 — Alerts | ⬜ Pendiente | Reglas de alerta, notificaciones email/webhook |

Ver hoja de ruta completa en `.claude/memory/roadmap.md`

---

## Stack tecnológico

- **Lenguaje:** Python 3.12
- **Framework API:** FastAPI 0.128
- **ASGI Server:** Uvicorn (standard)
- **ORM:** SQLAlchemy 2.x (async-ready)
- **Driver MySQL:** PyMySQL
- **Base de datos:** MySQL 8.x — `trading_ai`
- **Auth:** JWT HS256 en cookies HTTP-only
- **IA:** Ollama local (`gemma3:4b`) — sin API externa
- **Exchanges:** ccxt 4.5.40 (Binance, Bybit, Kraken, Coinbase, Bitget, OKX)
- **Arquitectura:** Screaming Architecture (módulos por dominio)

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

### Congelar dependencias

pip freeze > requirements.txt

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

---

## Contexto para Claude Code (colaboradores)

El proyecto usa **Claude Code** con contexto compartido en `.claude/memory/`.
Estos archivos se cargan automáticamente via `CLAUDE.md`:

- `.claude/memory/roadmap.md` — hoja de ruta con los 9 módulos
- `.claude/memory/modules_map.md` — tablas, archivos y endpoints por módulo
- `.claude/main_instructions.md` — arquitectura, convenciones y reglas
- `.claude/skills/` — guías de código para Claude

### Para configurar el contexto de sesión (una sola vez)

Después de clonar el repo, copia el `MEMORY.md` a tu carpeta local de Claude:

```bash
# Reemplaza la ruta con la ruta ABSOLUTA donde clonaste el repo en tu máquina
# Ejemplo: /Users/tu-nombre/projects/trading-api -> -Users-tu-nombre-projects-trading-api

PROYECTO_PATH=$(pwd | sed 's|/|-|g' | sed 's|^-||')
mkdir -p ~/.claude/projects/${PROYECTO_PATH}/memory/
cp .claude/memory/MEMORY.md ~/.claude/projects/${PROYECTO_PATH}/memory/MEMORY.md
```

Esto hace que Claude Code cargue el mismo contexto de sesión (bugs conocidos, convenciones, estado) que el resto del equipo.
