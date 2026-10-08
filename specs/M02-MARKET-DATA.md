# Módulo 2 — Market Data (Datos de Mercado) ✅ COMPLETO

← [Índice de módulos](_ROOT.md)

## Ficha

| Campo | Valor |
|---|---|
| Estado | ✅ Completo (tests de services pendientes) |
| Avance (alcance original) | 86 % — 6/7 entregables (falta "Tests unitarios de los services") |
| Madurez (estimada) | 65 % — ver [Avance](#avance) |
| Tablas | `exchanges`, `symbols`, `timeframes`, `candles` (R/W) |
| Depende de | [M1](M01-AUTH.md) (auth y roles) |
| Lo usan | [M3](M03-FEATURE-ENGINEERING.md), [M5](M05-STRATEGIES.md), [M6](M06-AI-AGENT.md), [M7](M07-BOTS-SIGNALS.md), [M8](M08-ORDERS-EXECUTION.md) y el scheduler |
| Prefijo API | `/api/exchanges`, `/api/symbols`, `/api/timeframes`, `/api/candles` |
| Frontend | `frontend/src/modules/market` |
| Última revisión | 2026-10-08 |

## Descripción

**En palabras simples:** Es la bodega de datos. Guarda toda la información de los precios de los activos financieros a lo largo del tiempo.

**Qué hace:**
- Registra los **exchanges** (plataformas de trading) como Binance, Bybit, Kraken, etc.
- Registra los **símbolos** (pares de trading) como BTC/USDT, ETH/USDT, EUR/USD, XAU/USD, etc.
- Registra los **timeframes** (marcos de tiempo) como 1 minuto, 5 minutos, 1 hora, 1 día, etc.
- Almacena **velas OHLCV**: cada vela es un resumen del precio en un período de tiempo (precio de apertura, precio más alto, precio más bajo, precio de cierre y volumen negociado)

**Por qué importa:** sin este módulo no hay datos para analizar. Además mantiene las velas al día de forma automática para los bots activos (ver [Scheduler](#scheduler-ingesta-automática)).

## Páginas

Hash routing: la URL real es `/#/<ruta>`.

**Usuario (todos los roles):**
- `/#/market/symbols` — Lista de todos los símbolos disponibles, con filtros y acceso "Ver velas"
- `/#/market/candles` — Ver las velas/precios de un símbolo (acepta `?symbol_id=&timeframe_id=`)

**Admin:**
- `/#/admin/exchanges` — Gestionar exchanges
- `/#/admin/symbols` — Gestionar símbolos
- `/#/admin/timeframes` — Gestionar timeframes
- `/#/admin/candles/ingest` — "Descargar velas": trae velas del exchange real con ccxt (`POST /api/candles/fetch`)

## Entregables

Tablas: `exchanges`, `symbols`, `timeframes`, `candles`

Entregables:
- CRUD exchanges (Binance, Bybit, Kraken, etc.)
- CRUD symbols (BTC/USDT, ETH/USDT, etc.) asociados a un exchange
- CRUD timeframes (1m, 5m, 15m, 1h, 4h, 1d)
- Ingestión de velas OHLCV: manual (endpoint) y/o automática (scheduler)
- Endpoint: `GET /api/candles?symbol_id=…&timeframe_id=…&from_ts=…&to_ts=…`
- Web UI: lista de símbolos, últimas velas en tabla (desde 2026-10-08 en React, `frontend/src/modules/market`)
- Tests unitarios de los services

## Decisiones de diseño

| Decisión | Motivo | Alternativa descartada |
|---|---|---|
| Precios y volúmenes como `DECIMAL(30,12)` y `Decimal(str(valor))` al leer | Evita errores de coma flotante en datos financieros | `float` |
| `bulk_upsert` con `INSERT … ON DUPLICATE KEY UPDATE` sobre `uq_candles_symbol_tf_ts` | La ingesta es idempotente: reintentar o solapar rangos no duplica velas | Insertar y capturar errores de clave duplicada |
| Cada vela se valida con `candle.is_valid_ohlcv()` antes del upsert | Rechaza datos corruptos (high < low, negativos) antes de llegar a la BD | Confiar solo en los `CHECK` de MySQL |
| El exchange de ccxt se resuelve desde `symbol.exchange_id` → nombre en minúsculas (`_CCXT_EXCHANGE_MAP`) | Un único símbolo en BD determina el origen del dato | Parámetro `exchange` libre en cada request |
| `exchanges` admite `crypto_exchange` / `broker` / `data_vendor` (p. ej. TradingView para metales y forex) | Mismo modelo para cripto, metales y forex | Una tabla por tipo de activo |
| `timeframes` guarda `seconds` y usa PK `SMALLINT` | El scheduler decide si una vela "venció" comparando segundos | Calcular segundos desde el código del timeframe |
| Datetimes de MySQL se normalizan a UTC con `_as_utc_aware()` | MySQL devuelve datetimes naive | Trabajar con naive y asumir UTC |
| Ingesta manual (`/api/candles/ingest`, máx. 5000 filas) + descarga ccxt (`/api/candles/fetch`) + scheduler | Cubre cargas históricas, uso puntual y mantenimiento automático | Solo scheduler |
| Scheduler deriva el trabajo de los bots activos, **sin tabla nueva** ("Opción B") | Menos esquema; solo se actualizan pares que alguien usa | Tabla de suscripciones por símbolo |
| Rutas REST bajo `/api` (`settings.API_PREFIX`), como el resto de módulos | La API es headless desde el 2026-10-08; antes iban sin prefijo porque las páginas Jinja vivían en `/market/` y `/admin/` | Prefijo distinto por módulo |
| Paginación en el cliente (`DataTable`) en las tablas de exchanges, symbols, timeframes y market/symbols | Simplicidad; los catálogos son pequeños | Paginación en servidor |

## Avance

| Métrica | Valor | Evidencia |
|---|---|---|
| Alcance original | **86 %** (6/7) | CRUD de exchanges/symbols/timeframes, ingesta manual y automática, `GET /api/candles` y UI completos; **no hay tests** en `tests/` para este módulo |
| Madurez | **≈ 65 %** | Funcionalidad 100 · Tests 0 · Seguridad 80 · Operación 80 |

- **Operación (80):** el scheduler automatiza fetch + features + retención; hay seed (`database/seeds/market_data.py`).
- **Seguridad (80):** escritura solo admin, validación OHLCV; sin rate limit propio.

## Posibles mejoras

| Prioridad | Mejora | Esfuerzo |
|---|---|---|
| Alta | Tests de `ingest_candles`, `fetch_candles` (ccxt mockeado) y del scheduler (`_should_fetch`, `_cleanup_candles`) | M |
| Baja | UI para la carga manual `POST /api/candles/ingest` (hoy solo por API; la página "Descargar velas" usa `/api/candles/fetch`) | S |
| Alta | Ejecutar el scheduler en un proceso/worker dedicado o con *lock*: hoy es un hilo daemon dentro de la app, y con varios workers de uvicorn se ejecutaría varias veces | M |
| Media | Detección y relleno de huecos: el ciclo incremental pide solo 3 velas, así que una caída del servidor de más de 3 timeframes deja velas faltantes | M |
| Media | La retención por defecto (500 velas) limita el histórico disponible para datasets/backtesting de [M5](M05-STRATEGIES.md); separar retención operativa de histórico | M |
| Media | Fetch automático para `broker`/`data_vendor` (forex y metales de TradingView): hoy `_CCXT_EXCHANGE_MAP` solo cubre exchanges cripto, esos símbolos solo se cargan manualmente | L |
| Baja | Paginación y filtros en servidor para catálogos grandes | S |

## Fuera de alcance y pendientes conocidos

- Datos en tiempo real por WebSocket (solo velas por polling).
- Order book, trades y ticks (solo OHLCV).
- Tests unitarios de services (entregable del roadmap sin cumplir).

## Detalle técnico

### Tablas en BD
| Tabla | Uso | Notas |
|-------|-----|-------|
| `exchanges` | Exchanges, brokers, data vendors | UNIQUE `name`; type: crypto_exchange/broker/data_vendor |
| `symbols` | Pares por exchange (BTC/USDT, EUR/USD, XAU/USD…) | UNIQUE (exchange_id, symbol); asset_class: crypto/metal/etf/stock/forex |
| `timeframes` | Marcos temporales | PK es `SMALLINT`; UNIQUE `code`; tiene `seconds` |
| `candles` | Velas OHLCV | UNIQUE (symbol_id, timeframe_id, ts); bulk upsert vía ON DUPLICATE KEY UPDATE |

### Seed de datos (ya ejecutado)
Archivo: `database/seeds/market_data.py` (`uv run python -m database.seeds market_data`)
- 7 exchanges: Binance, Bybit, Kraken, Coinbase, Bitget, OKX, TradingView
- 14 timeframes: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w
- 24 símbolos: 15 Binance crypto + 4 Bybit crypto + 2 TradingView metals + 3 TradingView forex

### Modelos ORM (`app/modules/market/infrastructure/`)
| Archivo | Clase | Tabla |
|---------|-------|-------|
| `exchange_model.py` | `ExchangeModel` | `exchanges` |
| `symbol_model.py` | `SymbolModel` | `symbols` |
| `timeframe_model.py` | `TimeframeModel` | `timeframes` |
| `candle_model.py` | `CandleModel` | `candles` |

Registrados en: `app/extensions/db/models_registry.py`

### Repositorios (`app/modules/market/`)
| Domain (interfaz) | Infrastructure (impl) |
|-------------------|-----------------------|
| `domain/exchange_repository.py` | `infrastructure/exchange_repository_impl.py` |
| `domain/symbol_repository.py` | `infrastructure/symbol_repository_impl.py` |
| `domain/timeframe_repository.py` | `infrastructure/timeframe_repository_impl.py` |
| `domain/candle_repository.py` | `infrastructure/candle_repository_impl.py` |

### Servicios (`app/modules/market/services/`)
| Subdir | Servicios |
|--------|-----------|
| `exchanges/` | `list_exchanges_service.py`, `create_exchange_service.py`, `update_exchange_service.py` |
| `symbols/` | `list_symbols_service.py`, `create_symbol_service.py`, `update_symbol_service.py` |
| `timeframes/` | `list_timeframes_service.py`, `create_timeframe_service.py` |
| `candles/` | `list_candles_service.py`, `ingest_candles_service.py` |

Provider: `app/modules/market/providers/market_provider.py` → `MarketServiceFactory`

### Endpoints REST
| Método | Ruta | Auth | Nota |
|--------|------|------|------|
| GET | `/api/exchanges` | token (cualquier user) | Filtros: is_active |
| POST | `/api/exchanges` | admin | Crea exchange |
| PUT | `/api/exchanges/{id}` | admin | Actualiza exchange |
| GET | `/api/symbols` | token | Filtros: exchange_id, asset_class, is_active |
| POST | `/api/symbols` | admin | Crea símbolo |
| PUT | `/api/symbols/{id}` | admin | Actualiza símbolo |
| GET | `/api/timeframes` | token | Lista todos |
| POST | `/api/timeframes` | admin | Crea timeframe |
| GET | `/api/candles` | token | Params: symbol_id, timeframe_id, from_ts, to_ts, limit (max 1000) |
| POST | `/api/candles/ingest` | admin | Bulk upsert de velas (max 5000 rows por request) |
| POST | `/api/candles/fetch` | admin | Descarga OHLCV del exchange con ccxt |

Routers registrados en `app/app_factory.py` (dentro de `api_routers`, montados con `prefix=settings.API_PREFIX`):
```python
from app.modules.market.rest import exchanges_router, symbols_router, timeframes_router, candles_router
```

### Frontend (`frontend/src/modules/market/`)
| Ruta | Archivo de ruta | Página |
|-----|----------|----|
| `/#/market/symbols` | `routes/_app/market/symbols.lazy.tsx` | `pages/symbols.tsx` |
| `/#/market/candles` | `routes/_app/market/candles.tsx` (`validateSearch`: `symbol_id`, `timeframe_id`) + `candles.lazy.tsx` | `pages/candles.tsx` |
| `/#/admin/exchanges` | `routes/_app/admin/exchanges.lazy.tsx` | `pages/admin-exchanges.tsx` + `components/exchange-form-dialog.tsx` |
| `/#/admin/symbols` | `routes/_app/admin/symbols.lazy.tsx` | `pages/admin-symbols.tsx` + `components/symbol-form-dialog.tsx` |
| `/#/admin/timeframes` | `routes/_app/admin/timeframes.lazy.tsx` | `pages/admin-timeframes.tsx` |
| `/#/admin/candles/ingest` | `routes/_app/admin/candles/ingest.lazy.tsx` | `pages/admin-candles-ingest.tsx` (usa `useFetchCandlesMutation` → `/api/candles/fetch`) |

- API: `api/market.api.ts`; queries `hooks/use-market-queries.ts` (`useExchangesQuery`, `useSymbolsQuery`, `useTimeframesQuery`, `useCandlesQuery`, reutilizadas por dashboard, features, bots, orders…); mutations `hooks/use-market-mutations.ts`; etiquetas `lib/market-labels.ts`.
- Las páginas admin están bajo `_app/admin.tsx` (`AdminGuardLayout`: sin rol admin → `/dashboard`); la API responde 403 a quien no es admin.

### Endpoint de descarga ccxt
- `POST /api/candles/fetch` → `FetchCandlesService` → usa ccxt para descargar OHLCV del exchange real
- Exchange se resuelve desde `symbol.exchange_id` → busca en DB → mapea a ccxt id (lowercase)
- Schema: `FetchCandlesRequest(symbol_id, timeframe_id, limit)`
- Soporta: binance, bybit, kraken, coinbase, bitget, okx (mapa en `_CCXT_EXCHANGE_MAP`)

### Scheduler (ingesta automática)

> Añadido el 2026-10-07 a partir del código (`app/modules/scheduler/`); no figuraba en el antiguo MODULES_MAP.

| Archivo | Qué hace |
|---|---|
| `scheduler_runner.py` | Hilo `trading-scheduler` (`daemon=True`) con `threading.Event` de parada; `start()` / `stop()` se enganchan al *lifespan* de FastAPI en `app_factory.py` |
| `scheduler_service.py` | `run_cycle()`: un ciclo completo de actualización |

Ciclo (`run_cycle`):
1. Lee bots con `status IN ('running','paused')`; si no hay ninguno, omite el ciclo.
2. Agrupa pares únicos `(symbol_id, timeframe_id)` y decide si hace falta fetch: sin velas → carga inicial de **500**; última vela vencida (`ahora − ts ≥ seconds`) → incremental de **3**; vigente → nada.
3. Descarga con `MarketServiceFactory(session).fetch_candles()` (una sesión por operación; un fallo no detiene los demás).
4. Limpia velas más antiguas que la retención con `CandleRepository.delete_beyond_retention()` (`DELETE` con subconsulta doble por la restricción de MySQL).
5. Para cada tripla `(symbol_id, timeframe_id, feature_set_id)` con velas nuevas, recalcula features con `FeatureServiceFactory(...).calculate_features()` ([M3](M03-FEATURE-ENGINEERING.md)) y limpia `candle_features` más allá de la retención.

Settings (`app/common/config/settings.py`):
```
SCHEDULER_ENABLED=true              # false para tests / entorno manual (default: true)
SCHEDULER_INTERVAL_SECONDS=60       # segundos entre ciclos (default: 60)
SCHEDULER_RETENTION_CANDLES=500     # velas a conservar por par (default: 500)
```
El scheduler **no genera señales ni órdenes**: solo mantiene velas y features al día para los bots ([M7](M07-BOTS-SIGNALS.md)).

## Gotchas críticos

- **ccxt:** versión fijada en `pyproject.toml` (`ccxt==4.4.96`).
- **Dropdowns de símbolos duplicados** (BTC/USDT ×2 en Binance y Bybit): la entidad `Symbol` incluye `exchange_name` vía JOIN → el front muestra `BTC/USDT (Binance)`.
- Resueltos con la migración a React (2026-10-08): CSP por prefijo web (`_is_web_route`), clases `.page-header`/`.pagination` de `app.css` y el redirect admin por `role_id` de la cookie ya no aplican (ver [M1](M01-AUTH.md)).

### Patrones clave M2
- `Decimal(str(model.tick_size))` — para convertir NUMERIC a Decimal sin errores float
- `bulk_upsert` en candles usa `sqlalchemy.text()` con `INSERT ... ON DUPLICATE KEY UPDATE`
- `_as_utc_aware()` en candle repo para normalizar datetimes de MySQL (naive → UTC aware)
- Ingestión: valida cada vela con `candle.is_valid_ohlcv()` antes del upsert

## Tests

- **No hay tests** para este módulo en `tests/` (el roadmap lo listaba como entregable).
- Primer objetivo recomendado: `ingest_candles_service` (validación OHLCV + límite 5000), `fetch_candles_service` con ccxt mockeado y `scheduler_service._should_fetch`.

## Riesgos

- Datos de exchange incorrectos o incompletos alimentan a [M3](M03-FEATURE-ENGINEERING.md), [M6](M06-AI-AGENT.md) y [M8](M08-ORDERS-EXECUTION.md) (el `PaperExecutor` usa la última vela como precio de ejecución).
- Límites de peticiones de los exchanges (ccxt) si hay muchos bots activos en pares distintos.
- Scheduler dentro del proceso web: duplicación con varios workers y trabajo bloqueante en el mismo proceso.

## Historial

- **2026-01** — Seed inicial: 7 exchanges, 14 timeframes y 24 símbolos (`seeds/seed_market_data.sql`).
- **2026-03** — `POST /candles/fetch` con ccxt; paginación cliente en tablas; fix de CSP para `/market/` y `/admin/`.
- **Posterior** — Scheduler de ingesta automática con retención de velas.
- **2026-10-07** — El scheduler deja de usar SQL crudo y modelos ORM: usa `BotRepository.list_by_statuses`, `CandleRepository.get_latest_ts` / `delete_beyond_retention` y `CandleFeatureRepository.delete_beyond_retention`; el commit lo hace el repositorio.
- **2026-10-08** — API headless (/api), páginas migradas a React (frontend/).
