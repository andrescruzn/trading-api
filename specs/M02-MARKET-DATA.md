# Módulo 2 — Market Data (Datos de Mercado) ✅ COMPLETO

← [Índice de módulos](_ROOT.md)

## Ficha

| Campo | Valor |
|---|---|
| Estado | ✅ Completo (tests de services pendientes) |
| Avance (alcance original) | 86 % — 6/7 entregables (falta "Tests unitarios de los services") |
| Madurez (estimada) | 67 % — ver [Avance](#avance) |
| Tablas | `exchanges`, `symbols`, `timeframes`, `candles` (R/W) |
| Depende de | [M1](M01-AUTH.md) (auth y roles) |
| Lo usan | [M3](M03-FEATURE-ENGINEERING.md), [M5](M05-STRATEGIES.md), [M6](M06-AI-AGENT.md), [M7](M07-BOTS-SIGNALS.md), [M8](M08-ORDERS-EXECUTION.md) y el scheduler (que además corre el ciclo de ejecución de [M7](M07-BOTS-SIGNALS.md)/[M8](M08-ORDERS-EXECUTION.md)) |
| Prefijo API | `/api/exchanges`, `/api/symbols`, `/api/timeframes`, `/api/candles`, `/api/explorer` |
| Frontend | `frontend/src/modules/market` |
| Última revisión | 2026-10-19 |

## Descripción

**En palabras simples:** Es la bodega de datos. Guarda toda la información de los precios de los activos financieros a lo largo del tiempo.

**Qué hace:**
- Registra los **exchanges** (plataformas de trading) como Binance, Bybit, Kraken, etc.
- Registra los **símbolos** como BTC/USDT o ETH/USDT, y también **perpetuos TradFi** de Binance/Bybit que siguen el precio del oro, la plata, el petróleo, el gas, el cobre, ETFs (SPY, QQQ) y acciones (NVDA, TSLA, AAPL): `XAU/USDT:USDT`.
- Registra los **timeframes** (marcos de tiempo) como 1 minuto, 5 minutos, 1 hora, 1 día, etc.
- Almacena **velas OHLCV**: cada vela es un resumen del precio en un período de tiempo (precio de apertura, precio más alto, precio más bajo, precio de cierre y volumen negociado)
- **Explorador de tendencia:** ordena los mercados por la fuerza de su tendencia en velas diarias para elegir dónde crear agentes.

**Por qué importa:** sin este módulo no hay datos para analizar. Además mantiene las velas al día de forma automática para los bots activos (ver [Scheduler](#scheduler-ingesta-automática)).

## Páginas

Hash routing: la URL real es `/#/<ruta>`.

**Usuario (todos los roles):**
- `/#/market/explorer` — "Explorar mercados": ranking por fuerza de tendencia (velas 1d) con filtro por clase de activo y "Crear agente" (abre el asistente con el símbolo elegido). Los admin ven además "Actualizar datos"
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
- ✅ Perpetuos TradFi (metales, materias primas, ETFs, acciones) vía ccxt en Binance/Bybit; clases de activo `commodity` e `index` (2026-10-10)
- ✅ Explorador de tendencia: `GET /api/explorer`, `POST /api/explorer/refresh` y página `/#/market/explorer` (2026-10-10)

## Decisiones de diseño

| Decisión | Motivo | Alternativa descartada |
|---|---|---|
| Precios y volúmenes como `DECIMAL(30,12)` y `Decimal(str(valor))` al leer | Evita errores de coma flotante en datos financieros | `float` |
| `bulk_upsert` con `INSERT … ON DUPLICATE KEY UPDATE` sobre `uq_candles_symbol_tf_ts` | La ingesta es idempotente: reintentar o solapar rangos no duplica velas | Insertar y capturar errores de clave duplicada |
| Cada vela se valida con `candle.is_valid_ohlcv()` antes del upsert | Rechaza datos corruptos (high < low, negativos) antes de llegar a la BD | Confiar solo en los `CHECK` de MySQL |
| El exchange de ccxt se resuelve desde `symbol.exchange_id` → nombre en minúsculas (`_CCXT_EXCHANGE_MAP`) | Un único símbolo en BD determina el origen del dato | Parámetro `exchange` libre en cada request |
| `exchanges` admite `crypto_exchange` / `broker` / `data_vendor` | Mismo modelo para cripto, metales y forex | Una tabla por tipo de activo |
| Metales, materias primas, ETFs y acciones como **perpetuos TradFi** de Binance/Bybit (`XAU/USDT:USDT`) | Datos y ejecución en el mismo sitio, 24/7, con el mismo código ccxt: ccxt elige el mercado por el símbolo unificado | Proveedor de datos aparte (yfinance, Twelve Data) + bróker: más código, horarios de mercado y sin ejecución |
| Perpetuos solo en **paper** (`is_perpetual()` en `domain/ccxt_exchanges.py`) | En live ccxt interpreta `amount` como contratos y harían falta apalancamiento, margen y cortos | Habilitar live con la lógica spot (tamaños de posición erróneos) |
| Explorador calculado al vuelo desde `candles` (1d), sin tabla nueva | ~40 símbolos × 250 velas: barato y siempre coherente con las velas | Tabla de métricas precalculadas |
| `strength` = min(ADX/50, 1) × eficiencia de Kaufman (30 d); ADX < 20 → lateral | Exige fuerza y limpieza del movimiento a la vez; comparable entre activos de precios muy distintos | Solo rendimiento %: premia saltos puntuales |
| `timeframes` guarda `seconds` y usa PK `SMALLINT` | El scheduler decide si una vela "venció" comparando segundos | Calcular segundos desde el código del timeframe |
| Datetimes de MySQL se normalizan a UTC con `_as_utc_aware()` | MySQL devuelve datetimes naive | Trabajar con naive y asumir UTC |
| Ingesta manual (`/api/candles/ingest`, máx. 5000 filas) + descarga ccxt (`/api/candles/fetch`) + scheduler | Cubre cargas históricas, uso puntual y mantenimiento automático | Solo scheduler |
| Scheduler deriva el trabajo de los bots activos, **sin tabla nueva** ("Opción B") | Menos esquema; solo se actualizan pares que alguien usa | Tabla de suscripciones por símbolo |
| **Elección de líder con `GET_LOCK` de MySQL** (`SchedulerLock`, lock `trading-app-scheduler`): con varios workers solo el que tiene el lock corre los ciclos; el resto lo reintenta cada `SCHEDULER_INTERVAL_SECONDS` | Cada worker arranca su hilo en el *lifespan*; sin lock se descargarían velas y —con la ejecución automática— se generarían señales y órdenes duplicadas. MySQL libera el lock si el proceso o la conexión mueren | Proceso aparte (sigue recomendado) · lock en Redis (otra dependencia) |
| El scheduler corre el **ciclo de ejecución** (`run_execution_cycle`) después de velas e indicadores | Las señales automáticas necesitan las velas y features de ese mismo ciclo | Un segundo hilo con su propio intervalo |
| Rutas REST bajo `/api` (`settings.API_PREFIX`), como el resto de módulos | La API es headless desde el 2026-10-08; antes iban sin prefijo porque las páginas Jinja vivían en `/market/` y `/admin/` | Prefijo distinto por módulo |
| Paginación en el cliente (`DataTable`) en las tablas de exchanges, symbols, timeframes y market/symbols | Simplicidad; los catálogos son pequeños | Paginación en servidor |

## Avance

| Métrica | Valor | Evidencia |
|---|---|---|
| Alcance original | **86 %** (6/7) | CRUD de exchanges/symbols/timeframes, ingesta manual y automática, `GET /api/candles` y UI completos; **no hay tests** en `tests/` para este módulo |
| Madurez | **≈ 67 %** | Funcionalidad 100 · Tests 0 · Seguridad 80 · Operación 88 |

- **Operación (88):** el scheduler automatiza fetch + features + retención y corre en un solo proceso aunque haya varios workers (lock de MySQL); hay seed (`database/seeds/market_data.py`). Sigue siendo un hilo dentro del proceso web.
- **Seguridad (80):** escritura solo admin, validación OHLCV; sin rate limit propio.

## Posibles mejoras

| Prioridad | Mejora | Esfuerzo |
|---|---|---|
| Alta | Tests de `ingest_candles`, `fetch_candles` (ccxt mockeado) y del scheduler (`_should_fetch`, `_cleanup_candles`) | M |
| Baja | UI para la carga manual `POST /api/candles/ingest` (hoy solo por API; la página "Descargar velas" usa `/api/candles/fetch`) | S |
| Media | Ejecutar el scheduler en un proceso/worker dedicado: el *lock* ya evita que corra varias veces (2026-10-19), pero sigue siendo un hilo dentro del proceso web y comparte su CPU con las peticiones | M |
| Media | Tests de `SchedulerLock` (con BD) y de `execution_cycle` | S |
| Media | Detección y relleno de huecos: el ciclo incremental pide solo 3 velas, así que una caída del servidor de más de 3 timeframes deja velas faltantes | M |
| Media | La retención por defecto (500 velas) limita el histórico disponible para datasets/backtesting de [M5](M05-STRATEGIES.md); separar retención operativa de histórico | M |
| Media | Proveedor de datos no-ccxt (yfinance / Twelve Data) para forex e índices reales: capa de proveedores en `FetchCandlesService`, horario de mercado en el scheduler y `vol_rel` con volumen 0 | L |
| Media | Live de perpetuos: cortos (`positions.qty >= 0`), apalancamiento, `contractSize` y redondeo a `lot_size` | L |
| Baja | Tests de `trend_metrics.compute_trend_metrics` (función pura) | S |
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
| `symbols` | Pares por exchange (BTC/USDT, XAU/USDT:USDT…) | UNIQUE (exchange_id, symbol); asset_class: crypto/metal/commodity/index/etf/stock/forex (revisión `m02 asset_class commodity index`) |
| `timeframes` | Marcos temporales | PK es `SMALLINT`; UNIQUE `code`; tiene `seconds` |
| `candles` | Velas OHLCV | UNIQUE (symbol_id, timeframe_id, ts); bulk upsert vía ON DUPLICATE KEY UPDATE |

### Seed de datos
Archivo: `database/seeds/market_data.py` (`uv run python -m database.seeds market_data`)
- 7 exchanges: Binance, Bybit, Kraken, Coinbase, Bitget, OKX, TradingView (sin símbolos)
- 14 timeframes: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w
- 37 símbolos:
  - Binance: 18 cripto spot (BTC, ETH, BNB, SOL, XRP, ADA, DOGE, AVAX, LINK, DOT, POL, UNI, ATOM, LTC, BCH, TRX, NEAR, SUI), `PAXG/USDT` (oro tokenizado, spot) y 12 perpetuos `X/USDT:USDT`: XAU, XAG, XPT, XPD (metal), CL, NATGAS, COPPER (commodity), SPY, QQQ (etf), NVDA, TSLA, AAPL (stock)
  - Bybit: 4 cripto spot (BTC, ETH, SOL, XRP) y perpetuos XAU y XAG
- La migración m02 desactiva los 5 símbolos viejos de TradingView (sin descarga) y `MATIC/USDT` (renombrado a POL).

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
| `candles/` | `list_candles_service.py`, `ingest_candles_service.py`, `fetch_candles_service.py` (acepta `client_cache` para reutilizar el cliente ccxt en lotes) |
| `explorer/` | `trend_metrics.py` (función pura: ADX, eficiencia, ATR %, rendimientos, dirección, fuerza), `list_trend_explorer_service.py`, `refresh_explorer_candles_service.py` |

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
| GET | `/api/explorer` | token | Ranking por tendencia (velas 1d). Filtro: asset_class. Solo símbolos activos con `supports_auto_fetch` |
| POST | `/api/explorer/refresh` | admin | Descarga velas 1d de todos esos símbolos (incluida la del día en curso) |

Routers registrados en `app/app_factory.py` (dentro de `api_routers`, montados con `prefix=settings.API_PREFIX`):
```python
from app.modules.market.rest import exchanges_router, symbols_router, timeframes_router, candles_router, explorer_router
```

### Frontend (`frontend/src/modules/market/`)
| Ruta | Archivo de ruta | Página |
|-----|----------|----|
| `/#/market/explorer` | `routes/_app/market/explorer.lazy.tsx` | `pages/explorer.tsx` (`useTrendExplorerQuery`, `useRefreshExplorerMutation`) |
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
- Soporta: binance, bybit, kraken, coinbase, bitget, okx (`CCXT_EXCHANGE_MAP` en `domain/ccxt_exchanges.py`, compartido con `live_executor.py`)
- Perpetuos: el símbolo unificado (`XAU/USDT:USDT`) basta para que ccxt use el mercado de futuros; no hace falta `defaultType`.

### Scheduler (ingesta automática)

> Añadido el 2026-10-07 a partir del código (`app/modules/scheduler/`); no figuraba en el antiguo MODULES_MAP.

| Archivo | Qué hace |
|---|---|
| `scheduler_runner.py` | Hilo `trading-scheduler` (`daemon=True`) con `threading.Event` de parada; `start()` / `stop()` se enganchan al *lifespan* de FastAPI en `app_factory.py`. En cada vuelta: `lock.acquire()` → (si es líder) `refresh_explorer()` cada 24 h → `run_cycle()` → `run_execution_cycle()`; al parar, `lock.release()` |
| `scheduler_service.py` | `run_cycle()`: un ciclo completo de actualización · `refresh_explorer()`: velas 1d del explorador |
| `scheduler_lock.py` | `SchedulerLock`: `GET_LOCK('trading-app-scheduler', 0)` en una conexión propia que se mantiene abierta mientras el proceso sea líder; cada ciclo confirma `IS_USED_LOCK(...) = CONNECTION_ID()` (además mantiene viva la conexión); si falla la verificación, se omite el ciclo |
| `execution_cycle.py` | `run_execution_cycle()`: señales automáticas por vela cerrada, caducidad de pendientes, protección SL/TP y polling de Telegram. Detalle en [M7](M07-BOTS-SIGNALS.md#ciclo-de-ejecución-del-scheduler-appmodulesschedulerexecution_cyclepy) |

Ciclo (`run_cycle`):
1. Lee bots con `status IN ('running','paused')`; si no hay ninguno, omite el ciclo. Por eso **iniciar un agente es lo que pone a andar la descarga de datos** de su símbolo.
2. Agrupa pares únicos `(symbol_id, timeframe_id)` y decide si hace falta fetch: sin velas → carga inicial de **500**; última vela vencida (`ahora − ts ≥ seconds`) → incremental de **3**; vigente → nada.
3. Descarga con `MarketServiceFactory(session).fetch_candles()` (una sesión por operación; un fallo no detiene los demás).
4. Limpia velas más antiguas que la retención con `CandleRepository.delete_beyond_retention()` (`DELETE` con subconsulta doble por la restricción de MySQL).
5. Para cada tripla `(symbol_id, timeframe_id, feature_set_id)` con velas nuevas **o con features atrasadas** (la última feature de esa tripla es anterior a la última vela, o no hay ninguna), recalcula features con `FeatureServiceFactory(...).calculate_features()` ([M3](M03-FEATURE-ENGINEERING.md)) y limpia `candle_features` más allá de la retención. Así un agente nuevo sobre un par que ya estaba al día (o con otro conjunto de indicadores) tiene datos en ≤ 1 ciclo, sin esperar a la siguiente vela.
6. Si no hubo nada que descargar ni features atrasadas, el ciclo termina sin más trabajo.

Settings (`app/common/config/settings.py`):
```
SCHEDULER_ENABLED=true              # false para tests / entorno manual (default: true)
SCHEDULER_INTERVAL_SECONDS=60       # segundos entre ciclos (default: 60)
SCHEDULER_RETENTION_CANDLES=500     # velas a conservar por par (default: 500)
```
Explorador: `scheduler_runner` llama a `refresh_explorer()` al arrancar y luego cada 24 h (`time.monotonic`), aparte de `run_cycle()` porque necesita datos de todos los símbolos aunque no haya agentes. Sin `force` solo descarga los símbolos cuya última vela 1d tiene un día o más.

Desde 2026-10-19, después de `run_cycle()` el scheduler corre `run_execution_cycle()`: **genera señales** para los agentes en modo Con aprobación / Automático, ejecuta las automáticas, caduca las pendientes y cierra posiciones por stop loss / take profit ([M7](M07-BOTS-SIGNALS.md), [M8](M08-ORDERS-EXECUTION.md)). Los agentes en modo Manual siguen como antes: el scheduler solo les mantiene velas y features.

## Gotchas críticos

- **ccxt:** versión fijada en `pyproject.toml` (`ccxt==4.4.96`).
- **Scheduler que "no hace nada" con varios workers:** es lo esperado en los que no son líder (solo uno tiene el lock). Si **ninguno** trabaja, buscar en el log `[Scheduler] No se pudo verificar el lock` (conexión a MySQL) y comprobar que nadie más tenga `trading-app-scheduler` (`SELECT IS_USED_LOCK('trading-app-scheduler')`).
- **Dos entornos sobre la misma BD** (p. ej. dos máquinas de desarrollo) comparten el lock: solo uno de los dos corre el scheduler.
- **Símbolos sin descarga automática:** solo los exchanges de `domain/ccxt_exchanges.py` (`CCXT_EXCHANGE_MAP`: binance, bybit, kraken, coinbase, bitget, okx) se descargan solos. `GET /api/symbols` devuelve `supports_auto_fetch` y el asistente de agentes ([M7](M07-BOTS-SIGNALS.md)) solo ofrece esos símbolos. Los de TradingView (`data_vendor`) nunca reciben velas: por eso el seed ya no los crea y la migración m02 los desactiva.
- **`SPX/USDT:USDT` no es el S&P 500:** en Binance y Bybit es la memecoin SPX6900. Para el índice usar `SPY` (o `US500`/`SP500` en otros exchanges).
- **`MATIC/USDT` ya no existe** (renombrado a `POL/USDT`): ccxt responde `BadSymbol`.
- **Perpetuos y volumen:** los perpetuos TradFi traen volumen real, así que `vol_rel` funciona; un proveedor de forex sin volumen lo dejaría en `NaN`.
- **Perpetuos en live:** bloqueados en `CreateBotService`, `UpdateBotService` (`BOT_PERPETUAL_LIVE_NOT_SUPPORTED`) y `LiveExecutor`; el asistente oculta las cuentas live si el símbolo es perpetuo.
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
- Scheduler dentro del proceso web: trabajo bloqueante en el mismo proceso (la duplicación con varios workers se resolvió con el lock). Si el líder cae, otro worker lo releva en su siguiente ciclo; mientras tanto no hay protección SL/TP ([M8](M08-ORDERS-EXECUTION.md)).

## Historial

- **2026-01** — Seed inicial: 7 exchanges, 14 timeframes y 24 símbolos (`seeds/seed_market_data.sql`).
- **2026-03** — `POST /candles/fetch` con ccxt; paginación cliente en tablas; fix de CSP para `/market/` y `/admin/`.
- **Posterior** — Scheduler de ingesta automática con retención de velas.
- **2026-10-07** — El scheduler deja de usar SQL crudo y modelos ORM: usa `BotRepository.list_by_statuses`, `CandleRepository.get_latest_ts` / `delete_beyond_retention` y `CandleFeatureRepository.delete_beyond_retention`; el commit lo hace el repositorio.
- **2026-10-08** — API headless (/api), páginas migradas a React (frontend/).
- **2026-10-10** — Perpetuos TradFi (oro, plata, platino, paladio, petróleo, gas, cobre, SPY, QQQ, NVDA, TSLA, AAPL) en el seed; clases `commodity` e `index` (migración m02, que además desactiva TradingView y MATIC); `MATIC`→`POL` + TRX, NEAR, SUI, PAXG; explorador de tendencia (`/api/explorer`, página Explorar mercados, refresco diario en el scheduler); perpetuos bloqueados en live; mapa ccxt único (sin copia en `live_executor.py`).
- **2026-10-19** — Scheduler con elección de líder por `GET_LOCK` de MySQL (`scheduler_lock.py`): corre una sola vez aunque haya varios workers. Tras cada ciclo de velas corre el ciclo de ejecución (`execution_cycle.py`: señales automáticas, caducidad, SL/TP, Telegram).
- **2026-10-08** — Scheduler: recalcula features atrasadas aunque no haya velas nuevas. `CCXT_EXCHANGE_MAP` movido al dominio (`ccxt_exchanges.py`) y `supports_auto_fetch` en la respuesta de símbolos. Páginas de usuario movidas a la sección "Explorar" del menú.
