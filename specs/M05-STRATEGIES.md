# Módulo 5 — Strategies (Estrategias) ✅ COMPLETO

← [Índice de módulos](_ROOT.md)

## Ficha

| Campo | Valor |
|---|---|
| Estado | ✅ Completo (tests pendientes) |
| Avance (alcance original) | 86 % — 6/7 entregables (falta "Tests unitarios") |
| Madurez (estimada) | 55 % — ver [Avance](#avance) |
| Tablas | `strategies`, `datasets` (R/W) |
| Depende de | [M1](M01-AUTH.md); conceptualmente de [M3](M03-FEATURE-ENGINEERING.md) (los indicadores que usan las reglas) |
| Lo usan | [M6](M06-AI-AGENT.md) (Prompt Maestro), [M7](M07-BOTS-SIGNALS.md) (cada bot referencia una estrategia) |
| Prefijo API | `/api/strategies`, `/api/datasets` (el `/api/` es obligatorio) |
| Última revisión | 2026-10-07 |

## Descripción

**En palabras simples:** Es el libro de reglas. Define exactamente cuándo el sistema debe considerar entrar o salir de una operación.

**Qué hace:**
- Guarda estrategias de trading con sus reglas configurables (¿en qué timeframe operar? ¿qué indicadores necesita? ¿tendencia o rango lateral?)
- Dos tipos principales:
  - **Trend-following** (seguir tendencia): opera cuando el precio está haciendo máximos más altos
  - **Mean-reversion** (reversión a la media): opera cuando el precio se aleja mucho de su promedio y se espera que regrese
- Valida coherencia tipo ↔ régimen: trend_following acepta trend_up/trend_down; mean_reversion acepta sideways
- Gestiona **datasets** de backtesting (rango de velas + features para un símbolo y timeframe)

## Páginas

**Páginas — Usuario (cualquier usuario autenticado):**
- `/strategies` — Lista de estrategias con tipo, régimen, timeframe y cantidad de reglas. Click para ver detalles completos.

**Páginas — Administrador (solo admin):**
- `/admin/strategies` — Crear y editar estrategias con editor de reglas JSON y validación de coherencia en vivo

## Entregables

Tablas: `strategies`, `datasets`

Entregables:
- ✅ CRUD estrategias con config JSON (reglas, régimen requerido, timeframe, risk_pct)
- ✅ Tipos soportados: trend_following, mean_reversion
- ✅ Validación coherencia tipo/régimen (hint en vivo en UI + validación backend)
- ✅ Web UI: /strategies (viewer) + /admin/strategies (CRUD admin)
- ✅ API: GET/POST `/api/strategies`, GET/PUT `/api/strategies/{id}`
- ✅ Seed: 6 estrategias de ejemplo (`seeds/strategies.py`)
- Tests unitarios: pendientes (no solicitados)

## Decisiones de diseño

| Decisión | Motivo | Alternativa descartada |
|---|---|---|
| Toda la configuración en `strategies.parameters` (JSON): `strategy_type`, `regime_required`, `timeframe_code`, `rules`, `risk_pct` | Nuevas estrategias sin migraciones; el agente lee el JSON tal cual | Una columna por parámetro |
| Dos tipos: `trend_following` y `mean_reversion`, cada uno ligado a un régimen válido | Evita configuraciones incoherentes (seguir tendencia en un rango lateral) | Tipos libres sin validar |
| Validación tipo↔régimen en backend (`STRATEGY_INCOHERENT_REGIME`, 422) **y** hint en vivo en la UI | La UI guía, el backend garantiza | Solo validación en el frontend |
| Reglas como `{indicator, operator, value}`; `value` puede ser un número **o el nombre de otro indicador** (`ema_20 > ema_50`); operadores `lt`, `gt`, `lte`, `gte`, `eq` | Lenguaje de reglas declarativo y evaluable de forma determinista por [M6](M06-AI-AGENT.md); una regla inválida o sin dato **falla** (fail-closed) | Código Python por estrategia |
| `risk_pct` vive en la estrategia | El tamaño de posición de [M6](M06-AI-AGENT.md) (`Capital × risk_pct / \|entry − SL\|`) queda versionado con la estrategia | Riesgo global fijo |
| `(name, version)` único (`STRATEGY_DUPLICATE_NAME_VERSION`) | Versionar estrategias sin pisar las anteriores | Editar en sitio sin versión |
| Prefijo API `/api/strategies` (no `/strategies`) | La página web `/strategies` colisionaba con el router REST (devolvía JSON en vez de HTML) | Cambiar la ruta de la página |
| Lectura para cualquier usuario autenticado, escritura solo admin | El trader ve las estrategias disponibles pero no las altera | Estrategias por usuario |
| Seed de 6 estrategias de ejemplo con `INSERT IGNORE` | Arranque rápido e idempotente | Crearlas a mano |

## Avance

| Métrica | Valor | Evidencia |
|---|---|---|
| Alcance original | **86 %** (6/7) | CRUD, tipos, validación, UI, API y seed completos; los tests figuran como "pendientes (no solicitados)" |
| Madurez | **≈ 55 %** | Funcionalidad 80 · Tests 0 · Seguridad 80 · Operación 60 |

- **Funcionalidad (80):** `datasets` es solo un registro de metadatos (CRUD de `query_spec`); **no hay motor de backtesting** ni UI de datasets.
- **Operación (60):** hay seed, pero no existe forma de comparar el rendimiento real de cada estrategia.

## Posibles mejoras

| Prioridad | Mejora | Esfuerzo |
|---|---|---|
| Alta | Tests de `create_strategy_service` / `update_strategy_service` (coherencia tipo↔régimen, duplicados) y del esquema de `rules` | S |
| Alta | Motor de **backtesting** que use `datasets` + `candle_features` y calcule Win Rate, R/R real, Profit Factor y Max Drawdown (el edge que pide [`_ROOT.md`](_ROOT.md) validar) | L |
| Media | Validar `rules` al guardar: indicadores existentes en el feature set, operador válido y `value` numérico o indicador conocido (hoy una regla mal escrita simplemente "falla" en [M6](M06-AI-AGENT.md)) | S |
| Media | Métricas por estrategia (señales aprobadas/rechazadas, Win Rate real) leyendo `signals` → `orders` → `fills` | M |
| Media | UI de `datasets` (la API existe, la UI no) | S |
| Baja | Nuevos tipos de estrategia (breakout, momentum) y plantillas clonables desde la UI | M |
| Baja | Archivar/deprecar estrategias en lugar de borrarlas | S |

## Fuera de alcance y pendientes conocidos

- Tests unitarios (marcados como pendientes en el roadmap original).
- Motor de backtesting y optimización de parámetros.
- Estrategias propias por usuario (hoy solo el admin las gestiona).

## Detalle técnico

### Tablas en BD
| Tabla | Acción | Nota |
|-------|--------|------|
| `strategies` | WRITE | CRUD completo, parameters JSON |
| `datasets` | WRITE | CRUD básico (sin UI aún) |

### Modelos ORM (`app/modules/strategies/infrastructure/`)
| Archivo | Clase | Tabla |
|---------|-------|-------|
| `strategy_model.py` | `StrategyModel` | `strategies` |
| `dataset_model.py` | `DatasetModel` | `datasets` |

### Repositorios
| Domain | Infrastructure |
|--------|----------------|
| `domain/strategy_repository.py` | `infrastructure/strategy_repository_impl.py` |
| `domain/dataset_repository.py` | `infrastructure/dataset_repository_impl.py` |

### Servicios (`app/modules/strategies/services/`)
| Subdir | Servicios |
|--------|-----------|
| `strategies/` | `list_strategies_service.py`, `create_strategy_service.py`, `update_strategy_service.py` |
| `datasets/` | `list_datasets_service.py`, `create_dataset_service.py` |

Provider: `app/modules/strategies/providers/strategy_provider.py` → `StrategyServiceFactory`

### Endpoints REST
| Método | Ruta | Auth | Nota |
|--------|------|------|------|
| GET | `/api/strategies` | token | Lista todas las estrategias |
| POST | `/api/strategies` | admin | Crea estrategia |
| GET | `/api/strategies/{id}` | token | Detalle estrategia |
| PUT | `/api/strategies/{id}` | admin | Actualiza estrategia |
| GET | `/api/datasets` | token | Lista datasets |
| POST | `/api/datasets` | admin | Crea dataset |

**⚠️ IMPORTANTE:** El prefijo API es `/api/strategies` (NO `/strategies`) para evitar conflicto con la página web `/strategies`.

Routers registrados en `app/app_factory.py`:
```python
from app.modules.strategies.rest import strategies_router, datasets_router
```

### Páginas web
| URL | Template | JS |
|-----|----------|----|
| `/strategies` | `templates/strategies/index.html` | `static/js/strategies/index.js` |
| `/admin/strategies` | `templates/admin/strategies.html` | `static/js/admin/strategies.js` |

### Estructura del JSON parameters (strategies.parameters)
```json
{
  "strategy_type": "trend_following | mean_reversion",
  "regime_required": "trend_up | trend_down | sideways | null",
  "timeframe_code": "1h | 4h | ...",
  "rules": [{"indicator": "rsi_14", "operator": "lt", "value": 30}],
  "risk_pct": 0.01
}
```

### Validación coherencia tipo↔régimen
- `trend_following` solo es válido con `trend_up` o `trend_down`
- `mean_reversion` solo es válido con `sideways`
- Hint en vivo en UI + validación en backend (service devuelve warning)

### Seed
- `seeds/strategies.py` — 6 estrategias de ejemplo, idempotente por (name, version)

### Cache-busting JS (global)
- El mecanismo `templates.env.globals["sv"]` aplica a **todos** los módulos; se documenta en [`_ROOT.md`](_ROOT.md#cache-busting-js-global).

## Gotchas críticos

- **Prefijo `/api/` obligatorio:** el API de strategies es `/api/strategies` (no `/strategies`); si el router REST se registra antes que el web router, `GET /strategies` devuelve JSON en vez de HTML.
- `build_list_response` retorna `{"data": [...array...]}`, no `{"data": {"items": [...]}}`. En el JS usar: `Array.isArray(json.data) ? json.data : (json.data?.items || [])`.
- `errorCode` en una respuesta exitosa es 200/201, **nunca 0**: detectar errores con `if (json.errorCode >= 400)`.
- El texto original hablaba de "warning" para la incoherencia tipo↔régimen; el código actual **rechaza** con `STRATEGY_INCOHERENT_REGIME` (HTTP 422).

## Tests

- **No hay tests** para este módulo (el roadmap los marca "pendientes (no solicitados)").
- Recomendado: `tests/strategies/test_create_strategy_service.py` y `test_update_strategy_service.py`.

## Riesgos

- Una regla mal escrita (indicador inexistente, operador no soportado) **hace fallar siempre** la estrategia en [M6](M06-AI-AGENT.md) sin avisar al editarla.
- Sin backtesting, no hay evidencia de edge antes de pasar un bot a `live` (ver la nota de edge en [`_ROOT.md`](_ROOT.md)).

## Historial

- **2026-03** — Módulo completado: CRUD estrategias/datasets, validación de coherencia, UI `/strategies` y `/admin/strategies`, seed de 6 estrategias.
- **2026-03** — Fix de colisión de rutas: el API pasa a `/api/strategies`.
