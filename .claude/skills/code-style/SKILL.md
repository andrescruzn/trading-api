---
name: code-style
description: Estilo de código Python de Trading AI API. Usar antes de escribir o editar cualquier archivo .py. Cubre cabecera de archivo, imports absolutos, type hints modernos, nomenclatura, docstrings y comentarios en español, banners de sección, Pydantic v2 y FastAPI.
---

# Estilo de código Python

## Cabecera de cada archivo

```python
# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/strategies/services/strategies/create_strategy_service.py
#
# PROPÓSITO / ENDPOINTS / NOTAS: (lo que un lector necesita saber)
# ======================================================================

from __future__ import annotations
```

- `# -*- coding: utf-8 -*-` siempre en la primera línea.
- Bloque de cabecera con la ruta del archivo y su propósito.
- `from __future__ import annotations` en archivos con type hints.

## Imports

- **Siempre absolutos desde `app.*`** (`from app.common.http import send`). Relativos solo dentro del mismo paquete REST (`from .schemas import ...`).
- Orden: stdlib → terceros → `app.*`, separados por línea en blanco.
- Importar desde el barrel del paquete cuando exista (`from app.modules.strategies.providers import StrategyServiceFactory`).

## Type hints

- Sintaxis moderna en código nuevo: `int | None`, `list[str]`, `dict[str, Any]`.
- El código existente usa a veces `Optional[...]`/`Dict[...]`; no reescribirlo solo por estilo.
- Todo método público lleva tipos de entrada y salida; los servicios devuelven `ServiceResult[T]`.

## Nomenclatura

| Elemento | Convención | Ejemplo |
|---|---|---|
| Clases | PascalCase | `CreateStrategyService`, `SqlAlchemyBotRepository` |
| Funciones, variables | snake_case | `list_strategies`, `risk_pct` |
| Constantes | UPPER_SNAKE | `STRATEGY_ERROR_MESSAGES`, `VALID_TYPES` |
| Privados | `_prefijo` | `self._repo`, `_strategy_to_dict()` |
| Archivos de servicio | `<verbo>_<recurso>_service.py` | `update_bot_status_service.py` |
| Códigos de error | `<RECURSO>_<MOTIVO>` | `BOT_NOT_FOUND` |

## Comentarios y docstrings (en español)

- Docstring de clase con propósito y **reglas de negocio** que aplica.
- Comentar el **porqué** (decisión, regla de trading, gotcha), no el qué.
- Banners para separar secciones largas:

```python
# ======================================================================
# GET /api/strategies
# ======================================================================
```

## Utilidades obligatorias

- Fechas: `utc_now()` de `app.common.utils`; para mostrar en hora local, `utc_to_bogota()`.
- Inputs de texto: `clean_str()` / `clean_email()` de `app.common.utils`.
- Configuración: `from app.common.config import settings`; nunca `os.getenv` fuera de `settings.py`.

## Pydantic v2 (schemas en `rest/<recurso>/schemas.py`)

```python
class CreateStrategyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    version: str = Field(default="1.0.0", max_length=32)
    description: str | None = Field(default=None)
    parameters: dict[str, Any] = Field(..., description="JSON de la estrategia…")
```

- Validar longitudes y rangos con `Field` (coinciden con las columnas de la BD).
- `model_config = ConfigDict(from_attributes=True)` solo si se construye desde objetos.

## FastAPI

- Rutas síncronas (`def`, no `async def`): la sesión de SQLAlchemy es síncrona.
- Dependencias con `Depends(...)` (estilo actual del repo). `Annotated[...]` es aceptable en código nuevo si se usa en todo el archivo.

## Formato

- 4 espacios, comillas dobles, ~100 caracteres por línea.
- No hay ruff ni mypy configurados en `pyproject.toml`; no ejecutar formateadores masivos sobre archivos existentes (genera diffs enormes).
