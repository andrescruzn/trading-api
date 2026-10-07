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

## Ejecución

Con el entorno activado:

```bash
uvicorn app.main:app --reload
```

O sin activarlo, usando uv:

```bash
uv run uvicorn app.main:app --reload
```
