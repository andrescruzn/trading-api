# Módulo 5 — Strategies (Estrategias) ✅ COMPLETO

← [Índice de módulos](_ROOT.md)

## Ficha

| Campo | Valor |
|---|---|
| Estado | ✅ Completo |
| Avance (alcance original) | 100 % — 7/7 entregables (tests unitarios desde el 2026-10-20) |
| Madurez (estimada) | 78 % — ver [Avance](#avance) |
| Tablas | `strategies`, `datasets` (R/W) |
| Depende de | [M1](M01-AUTH.md); conceptualmente de [M3](M03-FEATURE-ENGINEERING.md) (los indicadores que usan las reglas) |
| Lo usan | [M6](M06-AI-AGENT.md) (Prompt Maestro), [M7](M07-BOTS-SIGNALS.md) (cada bot referencia una estrategia) |
| Prefijo API | `/api/strategies`, `/api/datasets` |
| Frontend | `frontend/src/modules/strategies` |
| Última revisión | 2026-10-20 |

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

Hash routing: la URL real es `/#/<ruta>`.

**Páginas — Usuario (cualquier usuario autenticado):**
- `/#/strategies` — Lista de estrategias con tipo, régimen, timeframe y cantidad de reglas. Click en la fila abre un panel lateral con el detalle completo.

- `/#/backtest` — "Backtesting" (Explorar): estrategia, símbolo, timeframe, historia (500–3000 velas) y capital; resultado contra comprar y mantener, % de ganadoras, R/R real, profit factor, caída máxima y operaciones simuladas. Se abre también con "Probar en el pasado" en el detalle de una estrategia (`?strategy_id=`).

**Páginas — Administrador (solo admin):**
- `/#/admin/strategies` — "Gestionar estrategias" (Administración → Configuración): crear y editar estrategias (diálogo) con editor de reglas JSON y validación de coherencia en vivo

## Entregables

Tablas: `strategies`, `datasets`

Entregables:
- ✅ CRUD estrategias con config JSON (reglas, régimen requerido, timeframe, risk_pct)
- ✅ Tipos soportados: trend_following, mean_reversion
- ✅ Validación coherencia tipo/régimen (hint en vivo en UI + validación backend)
- ✅ Web UI: `/#/strategies` (viewer) + `/#/admin/strategies` (CRUD admin) — en React desde 2026-10-08
- ✅ API: GET/POST `/api/strategies`, GET/PUT `/api/strategies/{id}`
- ✅ Seed: 9 estrategias de ejemplo (`database/seeds/strategies.py`)
- ✅ (2026-10-20) Tests unitarios: estrategias (crear/editar/ver/listar, coherencia tipo↔régimen), datasets y evaluación de reglas
- ✅ (2026-10-20) **Backtesting sin IA**: `domain/backtest.py` (`run_backtest`), `RunBacktestService`, `POST /api/backtests`, página Backtesting; reglas evaluadas con `domain/rule_evaluation.py` (la misma función que usa la IA)
- ✅ (2026-10-20) Tests: `tests/strategies/test_backtest.py` (motor, servicio con indicadores reales en memoria, historia paginada)

## Decisiones de diseño

| Decisión | Motivo | Alternativa descartada |
|---|---|---|
| Toda la configuración en `strategies.parameters` (JSON): `strategy_type`, `regime_required`, `timeframe_code`, `rules`, `risk_pct` | Nuevas estrategias sin migraciones; el agente lee el JSON tal cual | Una columna por parámetro |
| Dos tipos: `trend_following` y `mean_reversion`, cada uno ligado a un régimen válido | Evita configuraciones incoherentes (seguir tendencia en un rango lateral) | Tipos libres sin validar |
| Validación tipo↔régimen en backend (`STRATEGY_INCOHERENT_REGIME`, 422) **y** hint en vivo en la UI | La UI guía, el backend garantiza | Solo validación en el frontend |
| Reglas como `{indicator, operator, value}`; `value` puede ser un número **o el nombre de otro indicador** (`ema_20 > ema_50`); operadores `lt`, `gt`, `lte`, `gte`, `eq` | Lenguaje de reglas declarativo y evaluable de forma determinista por [M6](M06-AI-AGENT.md); una regla inválida o sin dato **falla** (fail-closed) | Código Python por estrategia |
| `risk_pct` vive en la estrategia | El tamaño de posición de [M6](M06-AI-AGENT.md) (`Capital × risk_pct / \|entry − SL\|`) queda versionado con la estrategia | Riesgo global fijo |
| `(name, version)` único (`STRATEGY_DUPLICATE_NAME_VERSION`) | Versionar estrategias sin pisar las anteriores | Editar en sitio sin versión |
| Prefijo API `/api/strategies` | Originalmente para no colisionar con la página Jinja `/strategies`; desde 2026-10-08 todas las rutas REST viven bajo `/api` (`settings.API_PREFIX`) y la UI usa hash routing (`/#/strategies`), así que la colisión ya no existe | Cambiar la ruta de la página |
| Lectura para cualquier usuario autenticado, escritura solo admin | El trader ve las estrategias disponibles pero no las altera | Estrategias por usuario |
| Seed de estrategias con `get_or_create` por (name, version); una corrección es una **versión nueva** | Arranque rápido e idempotente; no cambia estrategias que ya usan agentes | Crearlas a mano / actualizar la fila existente |
| `description` limitada a **2000 caracteres** en `CreateStrategyRequest` y `UpdateStrategyRequest` (además `name` 1–120 y `version` ≤ 32) | Acota la entrada del usuario (se guarda en la BD y se muestra en la UI): evita textos enormes | Sin límite |
| **Backtest sin IA**: reglas + régimen como la IA, entrada en la apertura siguiente, SL 1,5×ATR / TP 3×ATR (2:1), riesgo de la estrategia con tope 1 %, comisión por lado; SL gana si se tocan los dos; solo largos | Mide si las reglas tienen ventaja de forma gratis, rápida y repetible; sin mirar el futuro | Llamar al LLM en cada vela (costoso, lento y no repetible) |
| **Evaluación de reglas única** (`domain/rule_evaluation.py`) para la IA y el backtest | Si cada uno evaluara a su manera, el backtest no mediría lo mismo que opera el agente | Copia del código en el backtest |
| Métricas del backtest con `orders/domain/performance.py` (`compute_performance`) | Se comparan en la misma escala con la pestaña Rendimiento de los agentes reales | Métricas propias del backtest |

## Avance

| Métrica | Valor | Evidencia |
|---|---|---|
| Alcance original | **100 %** (7/7) | CRUD, tipos, validación, UI, API, seed y tests unitarios completos |
| Madurez | **≈ 78 %** | Funcionalidad 90 · Tests 80 · Seguridad 80 · Operación 60 |

- **Funcionalidad (90):** backtesting sin IA (`POST /api/backtests`, página `/#/backtest`); `datasets` sigue siendo solo un registro de metadatos sin UI.
- **Tests (80):** 98 tests en `tests/strategies/` (servicios, entidad, reglas, backtest). Faltan las rutas (TestClient) y los repositorios con BD.
- **Operación (60):** hay seed, pero no existe forma de comparar el rendimiento real de cada estrategia.

## Posibles mejoras

| Prioridad | Mejora | Esfuerzo |
|---|---|---|
| Alta | Motor de **backtesting** que use `datasets` + `candle_features` y calcule Win Rate, R/R real, Profit Factor y Max Drawdown (el edge que pide [`_ROOT.md`](_ROOT.md) validar) | L |
| Media | Validar `rules` al guardar: indicadores existentes en el feature set, operador válido y `value` numérico o indicador conocido (hoy una regla mal escrita simplemente "falla" en [M6](M06-AI-AGENT.md)) | S |
| Media | Métricas por estrategia (señales aprobadas/rechazadas, Win Rate real) leyendo `signals` → `orders` → `fills` | M |
| Media | UI de `datasets` (la API existe, la UI no) | S |
| Baja | Nuevos tipos de estrategia (breakout, momentum) y plantillas clonables desde la UI | M |
| Baja | Archivar/deprecar estrategias en lugar de borrarlas | S |

## Fuera de alcance y pendientes conocidos

- Motor de backtesting y optimización de parámetros.
- Estrategias propias por usuario (hoy solo el admin las gestiona).

## Detalle técnico

### Backtesting (2026-10-20)
- `POST /api/backtests` (token, rate limit 3/min por usuario, `backtest_rate_limiter`): `{strategy_id, symbol_id, timeframe_id, bars (300–3000), initial_capital?, fee_pct? (≤ 0.01)}`. No guarda nada.
- `RunBacktestService` → `FetchCandleHistoryService` ([M2](M02-MARKET-DATA.md), `bars + 250` velas de calentamiento) → `compute_feature_rows` ([M3](M03-FEATURE-ENGINEERING.md)) → `run_backtest` → `compute_performance` ([M8](M08-ORDERS-EXECUTION.md)).
- Códigos: `STRATEGY_NOT_FOUND`, `BACKTEST_STRATEGY_WITHOUT_RULES`, `BACKTEST_NOT_ENOUGH_HISTORY` y los de ccxt (`rest/backtests/error_messages.py`).
- Front: `strategies/pages/backtest.tsx`, `runBacktest` / `useRunBacktestMutation`; ruta `routes/_app/backtest.tsx` (`validateSearch`: `strategy_id`).

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

Schemas (`rest/strategies/schemas.py`): `name` 1–120, `version` ≤ 32 (por defecto `1.0.0`), `description` ≤ 2000 (crear y editar), `parameters` obligatorio al crear. Una descripción más larga → 422 de validación.

El router declara `prefix="/strategies"` / `"/datasets"` (sin `/api`); el `/api` lo añade `app_factory.py` con `settings.API_PREFIX`.

Routers registrados en `app/app_factory.py` (dentro de `api_routers`):
```python
from app.modules.strategies.rest import strategies_router, datasets_router
```

### Frontend (`frontend/src/modules/strategies/`)
| Ruta | Archivo de ruta | Página / componentes |
|-----|----------|----|
| `/#/strategies` | `routes/_app/strategies.lazy.tsx` | `pages/strategies.tsx` (`StrategiesPage`) + `components/strategies-table.tsx` + `components/strategy-detail-sheet.tsx` |
| `/#/admin/strategies` | `routes/_app/admin/strategies.lazy.tsx` | `pages/admin-strategies.tsx` + `components/strategy-form-dialog.tsx` (reglas en `Textarea` JSON validado con zod; aviso de incoherencia tipo↔régimen en vivo) |

- API: `api/strategies.api.ts`; hooks `use-strategies-queries.ts` (`useStrategiesQuery`, también en dashboard, agent y bots) y `use-strategies-mutations.ts`; etiquetas `lib/strategies-labels.ts`; `components/strategy-regime-badge.tsx`.
- `datasets` sigue sin UI.

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
- `database/seeds/strategies.py` — 9 estrategias de ejemplo, idempotente por (name, version):
  - EMA Trend Follower 1.0.0 (1h) y 2.0.0 (4h), Bearish EMA Follower 1.0.0, MACD Crossover 1.0.0
  - RSI Mean Reversion 1.0.0 y Bollinger Band Reversion 1.0.0 (versiones viejas con reglas defectuosas: `bb_lower > 0` siempre se cumple; la segunda no usa bandas)
  - RSI Mean Reversion **1.1.0** (`bb_bandwidth < 3`) y Bollinger Band Reversion **1.1.0** (`1 < bb_bandwidth < 5`): las corrigen; solo las acepta el conjunto Rango o Completo
  - **Tendencia Metales 1.0.0** (trend_up, 4h, 1 %): EMAs alineadas, RSI 50–70, `macd_hist > 0`; sin `vol_rel` ni `atr_14` absoluto, para que sirva en oro, plata y demás perpetuos TradFi
- `bb_bandwidth` está en % del precio medio (pandas-ta BBB) y es comparable entre activos; `atr_14` está en unidades de precio y no (la regla `atr_14 > 0.005` de EMA Trend Follower 2.0.0 casi siempre se cumple).

## Gotchas críticos

- ~~Prefijo `/api/` obligatorio por colisión con la página web~~ — resuelto el 2026-10-08: ya no hay router web; todas las rutas REST van bajo `/api`.
- `build_list_response` retorna `{"data": [...array...]}`, no `{"data": {"items": [...]}}`. El front tipa `api.get<Strategy[]>('/strategies')` directamente sobre el array.
- `errorCode` en una respuesta exitosa es 200/201, **nunca 0**: el api-client del front detecta errores con `errorCode >= 400`.
- **Duplicado nombre+versión con espacios** (corregido el 2026-10-20): `CreateStrategyService` comprobaba el duplicado con el nombre tal cual llegaba y guardaba el nombre recortado, así que `" EMA Trend Follower"` pasaba el control y chocaba con el UNIQUE `(name, version)` de la BD (500 en lugar de 409). Ahora recorta antes de comprobar.
- Pendiente: un nombre de solo espacios pasa el schema (`min_length=1`) y se guarda vacío tras el recorte; una descripción de solo espacios se guarda como `""` (no como `None`).
- El texto original hablaba de "warning" para la incoherencia tipo↔régimen; el código actual **rechaza** con `STRATEGY_INCOHERENT_REGIME` (HTTP 422).

## Tests

Unitarios sin BD ni red (repositorios `MagicMock`). Correr: `uv run python -m pytest tests/strategies -q`.

| Archivo | Tests | Qué cubre |
|---|---:|---|
| `tests/strategies/test_strategy_services.py` | 44 | Coherencia tipo↔régimen (tabla completa, régimen nulo o desconocido), tipos válidos, accesos a `parameters`; crear (recorte de textos, 409 por duplicado también con espacios, 422 por tipo o régimen), editar (404, 409 contra otra estrategia pero no contra sí misma, revalidación de `parameters`), ver y listar; commit solo en éxito; textos de `error_messages.py` (estrategias y backtesting) |
| `tests/strategies/test_dataset_services.py` | 7 | Crear dataset (fin ≤ inicio → `DATASET_INVALID_DATE_RANGE` 422, rangos abiertos, recorte), ver (404) y listar |
| `tests/strategies/test_rule_evaluation.py` | 30 | `evaluate_rule` / `rules_pass` (la misma función de la IA y el backtest): cada operador con números concretos, tolerancia de `eq` (< 0,0001), indicador contra indicador, umbral en texto numérico, fail-closed (indicador u operador inexistente, dato nulo, NaN, umbral raro), una regla rota bloquea la entrada |
| `tests/strategies/test_backtest.py` | 17 | Motor de backtest, `RunBacktestService` con indicadores reales y tope del 1 %, historia paginada (2 casos) |

`FetchCandleHistoryService` (de [M2](M02-MARKET-DATA.md)) tiene además 15 tests en `tests/market/test_fetch_candle_history_service.py`.

**Sin cubrir:** rutas REST (TestClient, incluido el rate limit de `/api/backtests`) y los repositorios contra MySQL.

## Riesgos

- Una regla mal escrita (indicador inexistente, operador no soportado) **hace fallar siempre** la estrategia en [M6](M06-AI-AGENT.md) sin avisar al editarla.
- Sin backtesting, no hay evidencia de edge antes de pasar un bot a `live` (ver la nota de edge en [`_ROOT.md`](_ROOT.md)).

## Historial

- **2026-03** — Módulo completado: CRUD estrategias/datasets, validación de coherencia, UI `/strategies` y `/admin/strategies`, seed de 6 estrategias.
- **2026-03** — Fix de colisión de rutas: el API pasa a `/api/strategies`.
- **2026-10-08** — API headless (/api), páginas migradas a React (frontend/).
- **2026-10-10** — Seed: RSI Mean Reversion 1.1.0 y Bollinger Band Reversion 1.1.0 (reglas de bandas corregidas) y Tendencia Metales 1.0.0 para perpetuos TradFi.
- **2026-10-19** — Auditoría de seguridad (límites de entrada): `description` de la estrategia ≤ 2000 caracteres al crear y al editar.
- **2026-10-20** — "Gestionar estrategias" pasa del grupo admin Supervisión a **Configuración**.
- **2026-10-20** — Backtesting sin IA (motor puro, `POST /api/backtests`, página Backtesting, "Probar en el pasado") y evaluación de reglas compartida con la IA.
- **2026-10-20** — Tests unitarios de estrategias, datasets y evaluación de reglas (81 nuevos en `tests/strategies/`). Destaparon un bug, corregido: crear una estrategia con espacios alrededor de un nombre+versión existente daba 500 (IntegrityError) en lugar de 409.
