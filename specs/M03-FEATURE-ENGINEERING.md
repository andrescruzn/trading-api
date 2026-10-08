# Módulo 3 — Feature Engineering (Indicadores Técnicos) ✅ COMPLETO

← [Índice de módulos](_ROOT.md)

## Ficha

| Campo | Valor |
|---|---|
| Estado | ✅ Completo |
| Avance (alcance original) | 100 % — 8/8 entregables |
| Madurez (estimada) | 79 % — ver [Avance](#avance) |
| Tablas | `candle_features`, `feature_sets` (R/W); `candles`, `symbols`, `timeframes` (R) |
| Depende de | [M2](M02-MARKET-DATA.md) (velas) |
| Lo usan | [M6](M06-AI-AGENT.md) (Prompt Maestro), [M7](M07-BOTS-SIGNALS.md) (feature set por bot), scheduler de [M2](M02-MARKET-DATA.md) |
| Prefijo API | `/feature-sets`, `/candle-features` (sin `/api/`) |
| Última revisión | 2026-10-07 |

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
- Permite crear **Feature Sets**: conjuntos de indicadores nombrados y versionados que se reutilizan entre estrategias

**Por qué importa:** El agente de IA necesita estos indicadores para tomar decisiones. Sin ellos, el agente no tiene información suficiente para operar.

## Páginas

**Páginas — Usuario (cualquier usuario autenticado):**
- `/features` — Ver los indicadores calculados de un símbolo: filtra por símbolo, timeframe y feature set, y muestra la tabla con todos los valores (RSI, EMAs, MACD, ATR, Bollinger, régimen)

**Páginas — Administrador (solo admin):**
- `/admin/feature-sets` — Gestionar feature sets (crear nuevos con su spec JSON) y lanzar el cálculo de indicadores sobre cualquier símbolo y timeframe

## Entregables

Tablas: `candle_features`, `feature_sets`

Entregables:
- ✅ CRUD feature sets (nombre, versión, spec JSON)
- ✅ Cálculo de: RSI(14), ATR(14), EMA(20/50/200), MACD(12,26,9), Bollinger Bands(20,2), volumen relativo
- ✅ Detección de régimen de mercado: trend_up / trend_down / sideways (HH/HL swing analysis)
- ✅ POST /candle-features/calculate (admin) — bulk upsert
- ✅ GET /candle-features — consulta con filtros
- ✅ Web UI: /features (viewer) + /admin/feature-sets (gestión + calcular)
- ✅ TA library: pandas-ta 0.4.71b0
- ✅ Test unitarios (18 tests)

## Decisiones de diseño

| Decisión | Motivo | Alternativa descartada |
|---|---|---|
| Librería TA `pandas-ta 0.4.71b0` + `pandas 3.0.1` | Cubre RSI/EMA/MACD/ATR/Bollinger sin reimplementarlos | Implementar los indicadores a mano / TA-Lib (requiere compilar) |
| `_MIN_CANDLES = 220` | La EMA(200) necesita historia para ser fiable; con menos velas el cálculo se rechaza con `required`/`available` en `meta` | Calcular con pocas velas y devolver `NaN` |
| Las features de cada vela se guardan como **un JSON** en `candle_features.features` | Añadir indicadores no exige migraciones; `uq_candle_features` evita duplicados | Una columna por indicador |
| Cálculo con **bulk upsert** por `(symbol, timeframe, ts, feature_set)` | Recalcular es idempotente | Borrar y reinsertar |
| Régimen de mercado por análisis de swings (HH/HL, LH/LL), mínimo 10 velas | Regla simple y explicable que luego usa [M5](M05-STRATEGIES.md)/[M6](M06-AI-AGENT.md) como filtro de fase 1 | Clasificador ML |
| `feature_sets` con `(name, version)` único | Versionar conjuntos y poder reproducir qué indicadores usó una señal | Un único conjunto global |
| `feature_set_id` opcional en repositorio y servicio de `candle_features` (commit `ddc4336`) | Consultar features sin fijar un feature set (inferido del historial de git) | Obligatorio siempre |
| Repos de velas, símbolos y timeframes **prestados** de [M2](M02-MARKET-DATA.md) en `FeatureServiceFactory` | Evita duplicar acceso a datos de mercado | Repos propios |

## Avance

| Métrica | Valor | Evidencia |
|---|---|---|
| Alcance original | **100 %** (8/8) | Todos los entregables del roadmap implementados |
| Madurez | **≈ 79 %** | Funcionalidad 85 · Tests 75 · Seguridad 80 · Operación 75 |

- **Funcionalidad (85):** `calculate_features_service` calcula siempre el mismo conjunto fijo de indicadores; **no lee el `spec` JSON** del feature set (solo comprueba que el feature set exista). El `spec` es hoy descriptivo.
- **Tests (75):** 4 suites en `tests/features/` (18 tests según el roadmap).
- **Operación (75):** el scheduler de [M2](M02-MARKET-DATA.md) recalcula features para los bots activos.

## Posibles mejoras

| Prioridad | Mejora | Esfuerzo |
|---|---|---|
| Alta | Que `calculate_features_service` respete el `spec` del feature set (qué indicadores y con qué parámetros); hoy el `spec` no cambia el resultado | M |
| Media | Más indicadores (ADX, Stochastic, OBV, VWAP, SuperTrend) y multi-timeframe (p. ej. régimen en 4h para operar en 1h) | M |
| Media | Cálculo incremental: recalcular solo las velas nuevas en lugar de toda la ventana en cada ciclo del scheduler | M |
| Media | Tests de regresión del detector de régimen con series conocidas (tendencia, rango, falsos quiebres) | S |
| Baja | Exponer en la UI el `spec` y un preview del cálculo antes de lanzar el bulk | S |

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
| `feature_sets/` | `list_feature_sets_service.py`, `create_feature_set_service.py` |
| `calculations/` | `calculate_features_service.py` — RSI/EMA/MACD/ATR/BB/vol_rel + régimen |
| `candle_features/` | `list_candle_features_service.py` |

Provider: `app/modules/features/providers/feature_provider.py` → `FeatureServiceFactory`
- Borrow repos de market: `SqlAlchemyCandleRepository`, `SqlAlchemySymbolRepository`, `SqlAlchemyTimeframeRepository`
- TA library: `pandas-ta 0.4.71b0` + `pandas 3.0.1`
- `_MIN_CANDLES = 220` (para EMA200 confiable)

### Endpoints REST
| Método | Ruta | Auth | Nota |
|--------|------|------|------|
| GET | `/feature-sets` | token | Lista todos los feature sets |
| POST | `/feature-sets` | admin | Crea feature set (spec JSON) |
| GET | `/candle-features` | token | Params: symbol_id, timeframe_id, feature_set_id, from_ts, to_ts, limit |
| POST | `/candle-features/calculate` | admin | Calcula indicadores bulk (RSI/EMA/MACD/ATR/BB/vol_rel/regime) |

Routers registrados en `app/app_factory.py`:
```python
from app.modules.features.rest import feature_sets_router, candle_features_router
```

### Páginas web
| URL | Template | JS |
|-----|----------|----|
| `/features` | `templates/features/index.html` | `static/js/features/index.js` |
| `/admin/feature-sets` | `templates/admin/feature_sets.html` | `static/js/admin/feature_sets.js` |

### Campos del JSON features (candle_features.features)
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
