@.claude/MAIN_INSTRUCTIONS.md
@.claude/db_schema.sql
@.claude/memory/ROADMAP.md
@.claude/memory/MODULES_MAP.md

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

## Contexto para Claude Code (colaboradores)

El proyecto usa **Claude Code** con contexto compartido en `.claude/memory/`.
Estos archivos se cargan automáticamente via `CLAUDE.md`:

- [`specs/_ROOT.md`](specs/_ROOT.md) — índice de módulos; cada módulo tiene su spec en `specs/MNN-*.md` (se leen bajo demanda, no se importan)
- `.claude/memory/ROADMAP.md` — hoja de ruta con los 10 módulos
- `.claude/memory/MODULES_MAP.md` — tablas, archivos y endpoints por módulo
- `.claude/MAIN_INSTRUCTIONS.md` — arquitectura, convenciones y reglas
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
