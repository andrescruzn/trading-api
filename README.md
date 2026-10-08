# TRADING FAST API

Backend del proyecto **Trading AI**, construido con **FastAPI** sobre **Python 3.12**, orientado a trading algorítmico, IA y backtesting, usando **MySQL 8.x** como base de datos principal.

---

## Entorno

Crear el entorno virtual con [uv](https://docs.astral.sh/uv/):

```bash
uv venv --python 3.12
```

Activar el entorno virtual:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Windows (Git Bash)
source .venv/Scripts/activate
```

---

## Instalación

Instalar dependencias (`pyproject.toml` + `uv.lock`):

```bash
uv sync
```

Agregar / actualizar dependencias:

```bash
uv add <paquete>
uv add --dev <paquete>
uv lock --upgrade-package <paquete>
```

---

## Base de datos y migraciones

El esquema se gestiona con **Alembic** (`alembic.ini` + carpeta `alembic/`). La conexión se toma del `.env` (`DB_*`).

BD que ya existía antes de Alembic (solo una vez, no ejecuta SQL):

```bash
uv run alembic stamp 0001_baseline
```

BD nueva desde cero: cargar `.claude/db_schema.sql`, `migrations/m10_billing.sql` y los `seeds/*.sql` con el cliente de MySQL, y luego `uv run alembic stamp 0001_baseline`.

Día a día:

```bash
uv run alembic upgrade head                            # aplicar migraciones pendientes
uv run alembic revision --autogenerate -m "mNN ..."    # generar una nueva desde los modelos (revisar el archivo antes de aplicarla)
uv run alembic downgrade -1                            # deshacer la última
uv run alembic current                                 # ver en qué revisión está la BD
```

---

## Ejecución

Con el entorno activado:

```bash
uvicorn app.main:app --reload
```

O sin activarlo, usando uv:

```bash
uv run uvicorn app.main:app --reload
```
