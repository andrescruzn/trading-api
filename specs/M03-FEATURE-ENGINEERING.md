# Módulo 3 — Feature Engineering (Indicadores Técnicos) ✅ COMPLETO

← [Índice de módulos](_ROOT.md)

## Ficha

| Campo | Valor |
|---|---|
| Estado | ✅ Completo |
| Avance (alcance original) | 100 % — 10/10 entregables |
| Madurez (estimada) | 82 % — ver [Avance](#avance) |
| Tablas | `candle_features`, `feature_sets` (R/W); `candles`, `symbols`, `timeframes` (R) |
| Depende de | [M2](M02-MARKET-DATA.md) (velas) |
| Lo usan | [M6](M06-AI-AGENT.md) (Prompt Maestro), [M7](M07-BOTS-SIGNALS.md) (feature set por bot), scheduler de [M2](M02-MARKET-DATA.md) |
| Prefijo API | `/api/feature-sets`, `/api/candle-features` |
| Frontend | `frontend/src/modules/features` |
| Última revisión | 2026-10-19 |

## Descripción

**En palabras simples:** Es el analista técnico. Toma los precios históricos y calcula indicadores que ayudan a entender si el mercado está subiendo, bajando o moviéndose de lado.

**Qué hace:**
- Calcula indicadores populares como:
  - **RSI** — Si el activo está "sobrecomprado" o "sobrevendido"
  - **EMA** — Promedio móvil del precio (tendencia general)
  - **MACD** — Fuerza y dirección del movimiento del precio
  - **ATR** — Cuánto se mueve el precio en promedio (volatilidad)
  - **Bollinger Bands** — Rango normal de movimiento del precio
  - **Volumen relativo** — Si el volumen actual es mayor o menor al promedio reciente
- Detecta el **régimen del mercado**: ¿Está el precio haciendo máximos más altos (tendencia alcista)? ¿O está moviéndose en un rango lateral?
- Permite crear **conjuntos de indicadores** (feature sets) nombrados y versionados. Cada agente usa uno, y **el conjunto decide qué indicadores se calculan y cuáles lee la IA**.
- Trae 3 conjuntos sembrados, uno por enfoque: **Completo** (todos), **Tendencia** (EMA, MACD, RSI, ATR, volumen) y **Rango** (RSI, Bollinger, MACD, ATR, volumen).

**Por qué importa:** las reglas de cada estrategia están escritas sobre indicadores ("RSI < 30", "EMA 20 > EMA 50") y la IA los lee para decidir. Sin ellos, un agente no tiene con qué evaluar el mercado. El usuario no los configura a mano: el asistente de creación de agentes le ofrece solo los conjuntos compatibles con su estrategia.

## Páginas

Hash routing: la URL real es `/#/<ruta>`.

**Páginas — Usuario (cualquier usuario autenticado):**
- Los indicadores de cada agente se ven en su pestaña **Mercado** (`/#/agents/:id` → Indicadores, [M7](M07-BOTS-SIGNALS.md)), con la explicación de qué mide cada uno. Solo se calculan para agentes activos, así que no hay visor suelto para el usuario: `/#/features` redirige al inicio (`/#/dashboard`).

**Páginas — Administrador (solo admin):**
- `/#/admin/feature-sets` — "Conjuntos de indicadores": lista con enfoque e indicadores y crear nuevos (spec `{focus, indicators}`). El cálculo ya no se lanza desde aquí: se hace por agente (scheduler mientras está activo, o "Actualizar datos" en su pestaña Mercado). `POST /api/candle-features/calculate` sigue disponible para el admin solo por API

## Entregables

Tablas: `candle_features`, `feature_sets`

Entregables:
- ✅ CRUD feature sets (nombre, versión, spec JSON)
- ✅ Cálculo de: RSI(14), ATR(14), EMA(20/50/200), MACD(12,26,9), Bollinger Bands(20,2), volumen relativo
- ✅ Detección de régimen de mercado: trend_up / trend_down / sideways (HH/HL swing analysis)
- ✅ `POST /api/candle-features/calculate` (admin) — bulk upsert
- ✅ `GET /api/candle-features` — consulta con filtros
- ✅ Web UI: pestaña Mercado del agente (ver y recalcular) + `/#/admin/feature-sets` (gestión) — en React desde 2026-10-08; visor y cálculo movidos al agente el 2026-10-19
- ✅ TA library: pandas-ta 0.4.71b0
- ✅ Test unitarios (18 tests)
- ✅ **El cálculo y la IA respetan el `spec`** (`indicator_catalog`): solo se guardan y se envían al LLM los indicadores del conjunto
- ✅ **Seed `feature_sets`** con Completo / Tendencia / Rango

## Decisiones de diseño

| Decisión | Motivo | Alternativa descartada |
|---|---|---|
| Librería TA `pandas-ta 0.4.71b0` + `pandas 3.0.1` | Cubre RSI/EMA/MACD/ATR/Bollinger sin reimplementarlos | Implementar los indicadores a mano / TA-Lib (requiere compilar) |
| `_MIN_CANDLES = 220` | La EMA(200) necesita historia para ser fiable; con menos velas el cálculo se rechaza con `required`/`available` en `meta` | Calcular con pocas velas y devolver `NaN` |
| Las features de cada vela se guardan como **un JSON** en `candle_features.features` | Añadir indicadores no exige migraciones; `uq_candle_features` evita duplicados | Una columna por indicador |
| Cálculo con **bulk upsert** por `(symbol, timeframe, ts, feature_set)` | Recalcular es idempotente | Borrar y reinsertar |
| Régimen de mercado por análisis de swings (HH/HL, LH/LL), mínimo 10 velas | Regla simple y explicable que luego usa [M5](M05-STRATEGIES.md)/[M6](M06-AI-AGENT.md) como filtro de fase 1 | Clasificador ML |
| `spec = {focus, indicators}` con **grupos** fijos (`rsi`, `ema`, `macd`, `atr`, `bbands`, `vol_rel`) y periodos fijos | Las reglas de las estrategias usan claves fijas (`rsi_14`, `ema_20`): cambiar periodos por conjunto obligaría a reescribirlas | Conjuntos por velocidad (RSI 7, EMA 9/21…) |
| Un `spec` sin `indicators` equivale a todos los grupos | Los sets creados antes siguen funcionando igual | Migrar los specs existentes |
| `regime` se guarda siempre | El filtro de régimen es regla de negocio de toda estrategia | Hacerlo opcional |
| La respuesta de `GET /feature-sets` incluye `focus`, `indicators` y `outputs` derivados | El front filtra compatibilidad con las reglas sin duplicar el catálogo | Que el front interprete el spec |
| `feature_sets` con `(name, version)` único | Versionar conjuntos y poder reproducir qué indicadores usó una señal | Un único conjunto global |
| `feature_set_id` opcional en repositorio y servicio de `candle_features` (commit `ddc4336`) | Consultar features sin fijar un feature set (inferido del historial de git) | Obligatorio siempre |
| Repos de velas, símbolos y timeframes **prestados** de [M2](M02-MARKET-DATA.md) en `FeatureServiceFactory` | Evita duplicar acceso a datos de mercado | Repos propios |

## Avance

| Métrica | Valor | Evidencia |
|---|---|---|
| Alcance original | **100 %** (8/8) | Todos los entregables del roadmap implementados |
| Madurez | **≈ 82 %** | Funcionalidad 90 · Tests 75 · Seguridad 80 · Operación 85 |

- **Funcionalidad (90):** el `spec` decide qué indicadores se guardan y cuáles lee la IA; los periodos siguen fijos.
- **Tests (75):** 4 suites en `tests/features/` (18 tests según el roadmap).
- **Operación (85):** el scheduler de [M2](M02-MARKET-DATA.md) recalcula features para los agentes activos, también cuando van atrasadas respecto a la última vela; 3 conjuntos sembrados.

## Posibles mejoras

| Prioridad | Mejora | Esfuerzo |
|---|---|---|
| Media | Parámetros por conjunto (periodos de RSI/EMA…) junto con reglas de estrategia que referencien claves parametrizadas | L |
| Baja | Calcular con pandas-ta solo los grupos del conjunto (hoy calcula todos y filtra al guardar) | S |
| Media | Más indicadores (ADX, Stochastic, OBV, VWAP, SuperTrend) y multi-timeframe (p. ej. régimen en 4h para operar en 1h) | M |
| Media | Cálculo incremental: recalcular solo las velas nuevas en lugar de toda la ventana en cada ciclo del scheduler | M |
| Media | Tests de regresión del detector de régimen con series conocidas (tendencia, rango, falsos quiebres) | S |
| Baja | Preview del cálculo antes de lanzar el bulk | S |

## Fuera de alcance y pendientes conocidos

- Indicadores personalizados definidos por el usuario.
- Features de otras fuentes (sentimiento, on-chain, funding rate).
- Entrenamiento de modelos con estas features (tablas `models` / `model_runs` en [M6](M06-AI-AGENT.md)).

## Detalle técnico

### Tablas en BD
| Tabla | Acción | Nota |
|-------|--------|------|
| `candle_features` | WRITE | Features calculadas por vela + feature_set |
| `feature_sets` | WRITE | Definición de conjuntos de indicadores |
| `candles` | READ | Fuente de datos para calcular indicadores |
| `symbols` | READ | Para validar symbol_id |
| `timeframes` | READ | Para validar timeframe_id |

### Tablas que NO debe tocar
- `exchanges`, `users`, `roles`, `http_audit_*`

### Modelos ORM (`app/modules/features/infrastructure/`)
| Archivo | Clase | Tabla |
|---------|-------|-------|
| `feature_set_model.py` | `FeatureSetModel` | `feature_sets` |
| `candle_feature_model.py` | `CandleFeatureModel` | `candle_features` |

Registrados en: `app/extensions/db/models_registry.py`

### Repositorios (`app/modules/features/`)
| Domain (interfaz) | Infrastructure (impl) |
|-------------------|-----------------------|
| `domain/feature_set_repository.py` | `infrastructure/feature_set_repository_impl.py` |
| `domain/candle_feature_repository.py` | `infrastructure/candle_feature_repository_impl.py` |

### Servicios (`app/modules/features/services/`)
| Subdir | Servicios |
|--------|-----------|
| `feature_sets/` | `list_feature_sets_service.py`, `create_feature_set_service.py` (valida grupos y `focus`: `FEATURE_SET_INVALID_INDICATORS`, `FEATURE_SET_INVALID_FOCUS`) |
| `calculations/` | `calculate_features_service.py` — RSI/EMA/MACD/ATR/BB/vol_rel + régimen; guarda solo los grupos del `spec` |

Dominio: `domain/indicator_catalog.py` — `INDICATOR_GROUPS` (grupo → claves), `groups_for`, `outputs_for`, `focus_of`, `invalid_groups`, `rule_keys`, `missing_for_rules`, `is_compatible`. Lo usan el cálculo, [M6](M06-AI-AGENT.md) (prompt y compatibilidad) y [M7](M07-BOTS-SIGNALS.md) (validación al crear).
| `candle_features/` | `list_candle_features_service.py` |

Provider: `app/modules/features/providers/feature_provider.py` → `FeatureServiceFactory`
- Borrow repos de market: `SqlAlchemyCandleRepository`, `SqlAlchemySymbolRepository`, `SqlAlchemyTimeframeRepository`
- TA library: `pandas-ta 0.4.71b0` + `pandas 3.0.1`
- `_MIN_CANDLES = 220` (para EMA200 confiable)

### Endpoints REST
| Método | Ruta | Auth | Nota |
|--------|------|------|------|
| GET | `/api/feature-sets` | token | Lista todos los conjuntos, con `focus`, `indicators` y `outputs` derivados del spec |
| POST | `/api/feature-sets` | admin | Crea feature set (spec JSON) |
| GET | `/api/candle-features` | token | Params: symbol_id, timeframe_id, feature_set_id, from_ts, to_ts, limit |
| POST | `/api/candle-features/calculate` | admin | Calcula indicadores bulk (RSI/EMA/MACD/ATR/BB/vol_rel/regime) |

Routers registrados en `app/app_factory.py` (dentro de `api_routers`, con `prefix=settings.API_PREFIX`):
```python
from app.modules.features.rest import feature_sets_router, candle_features_router
```

### Frontend (`frontend/src/modules/features/`)
| Ruta | Archivo de ruta | Página / componentes |
|-----|----------|----|
| — (pestaña Mercado de `/#/agents/:id`, [M7](M07-BOTS-SIGNALS.md)) | — | `components/candle-features-table.tsx` + `components/indicators-glossary.tsx` + `components/regime-badge.tsx` |
| `/#/features` | `routes/_app/features.tsx` | Redirección a `/dashboard` |
| `/#/admin/feature-sets` | `routes/_app/admin/feature-sets.lazy.tsx` | `pages/admin-feature-sets.tsx` + `components/feature-set-form-dialog.tsx` |

- API: `api/features.api.ts`; hooks `use-features-queries.ts` (`useCandleFeaturesQuery`, también lo usa el dashboard de [M1](M01-AUTH.md)) y `use-features-mutations.ts`; etiquetas y régimen en `lib/features-labels.ts` y `lib/regime.ts` (`regimeLabel`, `REGIME_BADGE_VARIANT`).

### Seed `feature_sets` (`database/seeds/feature_sets.py`)
| Nombre | focus | indicators |
|---|---|---|
| Completo | all | rsi, ema, macd, atr, bbands, vol_rel |
| Tendencia | trend_following | ema, macd, rsi, atr, vol_rel |
| Rango | mean_reversion | rsi, bbands, macd, atr, vol_rel |

### Campos del JSON features (candle_features.features)
Solo las claves de los grupos del conjunto, más `regime`:
```json
{
  "regime": "trend_up|trend_down|sideways",
  "rsi_14": float,
  "ema_20": float, "ema_50": float, "ema_200": float,
  "macd": float, "macd_signal": float, "macd_hist": float,
  "atr_14": float,
  "bb_upper": float, "bb_mid": float, "bb_lower": float,
  "vol_rel": float
}
```

### Detección de régimen
- `trend_up`: último swing tiene HH y HL (Higher High + Higher Low)
- `trend_down`: último swing tiene LH y LL (Lower High + Lower Low)
- `sideways`: cualquier otro patrón
- Mínimo 10 velas para detectar swings

### Columnas exactas de pandas-ta (versión 0.4.71b0)
| Indicador | Columna generada |
|---|---|
| RSI(14) | `RSI_14` |
| EMA(20) | `EMA_20` |
| EMA(50) | `EMA_50` |
| EMA(200) | `EMA_200` |
| MACD line | `MACD_12_26_9` |
| MACD signal | `MACDs_12_26_9` |
| MACD hist | `MACDh_12_26_9` |
| ATR(14) | `ATRr_14` ← OJO: tiene 'r' minúscula |
| BB Upper | `BBU_20_2.0_2.0` ← OJO: doble `_2.0` |
| BB Mid | `BBM_20_2.0_2.0` |
| BB Lower | `BBL_20_2.0_2.0` |

## Gotchas críticos

- `pandas-ta` genera `ATRr_14` (con **r** minúscula), no `ATR_14`, y las bandas de Bollinger como `BBU_20_2.0_2.0` / `BBL_20_2.0_2.0` / `BBM_20_2.0_2.0` (doble `_2.0`), no `BBU_20_2.0`. Verificar siempre los nombres reales con `df.columns` antes de usarlos en `dropna(subset=...)`: `df.ta.<indicador>(append=True); print(df.columns)`. Tabla completa de columnas [arriba](#columnas-exactas-de-pandas-ta-versión-0471b0).
- `pandas-ta 0.4.71b0` está instalado en el `.venv` (con `pandas 3.0.1`); `numba` / `llvmlite` (vía pandas-ta) no soportan Python 3.14, por eso el proyecto usa Python 3.12.
- **Filas válidas por grupo:** se descartan filas con NaN solo en las columnas de los grupos presentes (`_REQUIRED_BY_GROUP`); un conjunto sin `ema` tiene filas desde antes porque no espera a la EMA(200).
- **Features antiguas:** las filas calculadas antes del catálogo tienen todas las claves; no hace falta recalcularlas.
- Con menos de 220 velas el servicio devuelve error (`meta.required` / `meta.available`); la retención del scheduler (500 por defecto) lo cubre, pero un par con poca historia no calculará.

## Tests

- `tests/features/`: `test_list_feature_sets_service.py`, `test_create_feature_set_service.py`, `test_list_candle_features_service.py`, `test_calculate_features_service.py` — 18 tests unitarios según el roadmap.
- **Huecos:** detector de régimen en casos límite; rutas REST.

## Riesgos

- Un cambio de versión de `pandas-ta` (es una versión beta) puede renombrar columnas y romper el cálculo en silencio.
- Los indicadores alimentan decisiones de [M6](M06-AI-AGENT.md): un error aquí se propaga a señales y órdenes.

## Historial

- **2026-03** — Módulo completado: CRUD feature sets, cálculo bulk, régimen, UI `/features` y `/admin/feature-sets`.
- **Posterior** — `feature_set_id` opcional en `candle_features` (commit `ddc4336`).
- **2026-10-08** — API headless (/api), páginas migradas a React (frontend/).
- **2026-10-08** — Conjuntos por enfoque: `indicator_catalog`, el cálculo y la IA respetan el `spec`, seed Completo/Tendencia/Rango, `focus`/`indicators`/`outputs` en la API; páginas renombradas a "Conjuntos de indicadores".
- **2026-10-19** — Indicadores centrados en el agente: salen del menú del usuario y se ven en la pestaña **Mercado** del agente, que también los recalcula ("Actualizar datos"); se retira "Calcular indicadores" de Conjuntos (el endpoint queda solo por API); la tabla y el glosario se extraen a `components/`.
