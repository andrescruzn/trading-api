# Mapa de Módulos — Tablas, Archivos y Endpoints

Este archivo es la referencia definitiva de qué toca cada módulo.
**Leer ANTES de codear en cualquier módulo nuevo para no pisar lo anterior.**

---

## ✅ Módulo 1 — Auth & Web UI

### Tablas en BD
| Tabla | Uso |
|-------|-----|
| `users` | Usuarios, password_hash, OTP, JTI de sesión, lockout, last_login_at |
| `roles` | id=1→user, id=2→admin |

### Modelos ORM
- `app/modules/users/infrastructure/user_model.py` → `UserModel` (tabla `users`)
- `app/modules/users/infrastructure/role_model.py` → `RoleModel` (tabla `roles`)

### Repositorios
- `app/modules/users/domain/user_repository.py` — interfaz ABC
- `app/modules/users/infrastructure/user_repository_impl.py` — `SqlAlchemyUserRepository`

### Servicios (`app/modules/users/services/auth/`)
| Archivo | Función |
|---------|---------|
| `login_password_service.py` | Login por password (bcrypt, lockout, JTI) |
| `login_otp_service.py` | Solicitar OTP por email |
| `verify_otp_service.py` | Verificar OTP y emitir cookie |
| `logout_service.py` | Revocar cookie y limpiar JTI |
| `rotate_token_service.py` | Rotar JTI en sesión activa |
| `get_me_service.py` | Perfil del usuario autenticado |
| `change_password_service.py` | Cambiar contraseña (revoca sesión) |

### Endpoints (`/users/...`)
| Método | Ruta | Auth |
|--------|------|------|
| POST | `/users/login` | — |
| POST | `/users/login-otp` | — |
| POST | `/users/verify-otp` | — |
| POST | `/users/logout` | cookie |
| POST | `/users/rotate-token` | cookie |
| GET  | `/users/me` | cookie |
| POST | `/users/change-password` | cookie |

### Páginas web
| URL | Template | JS |
|-----|----------|----|
| `/login` | `templates/login.html` | `static/js/login.js` |
| `/dashboard` | `templates/dashboard.html` | `static/js/dashboard.js` |
| `/profile` | `templates/profile.html` | `static/js/profile.js` |

### Middleware relevante
- `app/common/security/security_headers.py` — CSP por ruta
  - **IMPORTANTE:** Al agregar nuevas rutas web hay que añadirlas a `web_prefixes` en `_is_web_route()`
  - Prefijos actuales: `/login`, `/dashboard`, `/profile`, `/static/`, `/market/`, `/admin/`
- `app/common/audit/` — AuditMiddleware, tablas `http_audit_<año>`

---

## ✅ Módulo 2 — Market Data

### Tablas en BD
| Tabla | Uso | Notas |
|-------|-----|-------|
| `exchanges` | Exchanges, brokers, data vendors | UNIQUE `name`; type: crypto_exchange/broker/data_vendor |
| `symbols` | Pares por exchange (BTC/USDT, EUR/USD, XAU/USD…) | UNIQUE (exchange_id, symbol); asset_class: crypto/metal/etf/stock/forex |
| `timeframes` | Marcos temporales | PK es `SMALLINT`; UNIQUE `code`; tiene `seconds` |
| `candles` | Velas OHLCV | UNIQUE (symbol_id, timeframe_id, ts); bulk upsert vía ON DUPLICATE KEY UPDATE |

### Seed de datos (ya ejecutado)
Archivo: `seeds/seed_market_data.sql`
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
| GET | `/exchanges` | token (cualquier user) | Filtros: is_active |
| POST | `/exchanges` | admin | Crea exchange |
| PUT | `/exchanges/{id}` | admin | Actualiza exchange |
| GET | `/symbols` | token | Filtros: exchange_id, asset_class, is_active |
| POST | `/symbols` | admin | Crea símbolo |
| PUT | `/symbols/{id}` | admin | Actualiza símbolo |
| GET | `/timeframes` | token | Lista todos |
| POST | `/timeframes` | admin | Crea timeframe |
| GET | `/candles` | token | Params: symbol_id, timeframe_id, from_ts, to_ts, limit (max 1000) |
| POST | `/candles/ingest` | admin | Bulk upsert de velas (max 5000 rows por request) |

Routers registrados en `app/app_factory.py`:
```python
from app.modules.market.rest import exchanges_router, symbols_router, timeframes_router, candles_router
```

### Páginas web
| URL | Template | JS |
|-----|----------|----|
| `/market/symbols` | `templates/market/symbols.html` | `static/js/market/symbols.js` |
| `/market/candles` | `templates/market/candles.html` | `static/js/market/candles.js` |
| `/admin/exchanges` | `templates/admin/exchanges.html` | `static/js/admin/exchanges.js` |
| `/admin/symbols` | `templates/admin/symbols.html` | `static/js/admin/symbols.js` |
| `/admin/timeframes` | `templates/admin/timeframes.html` | `static/js/admin/timeframes.js` |
| `/admin/candles/ingest` | `templates/admin/candles_ingest.html` | `static/js/admin/candles_ingest.js` |

Rutas web en: `app/modules/web/routes.py`
- Admin pages verifican `role_id == AUTH_ADMIN_ROLE_ID` desde la cookie JWT
- Si no es admin → redirect a `/dashboard` (NO 403)

### Gotcha crítico — JWT subject
El JWT debe incluir `role_id` para que las páginas admin funcionen:
```python
subject={"user_id": user.id, "role_id": user.role_id}
```
Servicios que crean tokens (los 3 deben tener `role_id`):
- `login_password_service.py`
- `verify_otp_service.py`
- `rotate_token_service.py`

Sin `role_id` en el JWT, `_get_identity_from_cookie()` retorna `role_id=0` y todas las páginas admin redirigen silenciosamente al dashboard.

### Nuevo endpoint M2
- `POST /candles/fetch` → `FetchCandlesService` → usa ccxt para descargar OHLCV del exchange real
- Exchange se resuelve desde `symbol.exchange_id` → busca en DB → mapea a ccxt id (lowercase)
- Schema: `FetchCandlesRequest(symbol_id, timeframe_id, limit)`
- Soporta: binance, bybit, kraken, coinbase, bitget, okx (mapa en `_CCXT_EXCHANGE_MAP`)

### Patrones clave M2
- `Decimal(str(model.tick_size))` — para convertir NUMERIC a Decimal sin errores float
- `bulk_upsert` en candles usa `sqlalchemy.text()` con `INSERT ... ON DUPLICATE KEY UPDATE`
- `_as_utc_aware()` en candle repo para normalizar datetimes de MySQL (naive → UTC aware)
- Ingestión: valida cada vela con `candle.is_valid_ohlcv()` antes del upsert

---

## ✅ Módulo 3 — Feature Engineering (COMPLETO)

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

---

## ✅ Módulo 5 — Strategies (COMPLETO)

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
- `seeds/seed_strategies.sql` — 6 estrategias de ejemplo con `INSERT IGNORE`

### Cache-busting JS (global, aplica a todos los módulos)
- `templates.env.globals["sv"] = str(int(time.time()))` en `app/modules/web/routes.py`
- Todos los `<script src="...">` usan `?v={{ sv }}` — fuerza recarga tras reinicio del servidor
- Aplica a TODOS los templates (base_app.html incluido)

---

---

## ✅ Módulo 6 — AI Agent / Models (COMPLETO)

### Tablas en BD
| Tabla | Acción | Nota |
|-------|--------|------|
| `models` | WRITE | Modelos ML registrados (xgboost/lightgbm/sklearn/nn) |
| `model_runs` | WRITE | Ejecuciones de entrenamiento con métricas y params |
| `strategies` | READ | Para resolver estrategia en Prompt Maestro |
| `accounts` | READ | Para obtener capital disponible |
| `account_balances` | READ | Balance más reciente (base_currency) |
| `candles` | READ | Última vela del símbolo/timeframe |
| `candle_features` | READ | Últimas features calculadas del feature_set |
| `symbols` | READ | Para validar symbol_id |
| `timeframes` | READ | Para validar timeframe_id |

### Tablas que NO toca
- `predictions` (requiere bot_id de Módulo 7, diferida a ese módulo)
- `bots`, `signals`, `orders`, `users`, `roles`

### Modelos ORM (`app/modules/agent/infrastructure/`)
| Archivo | Clase ORM | Tabla |
|---------|-----------|-------|
| `ml_model_model.py` | `MLModelORM` | `models` |
| `model_run_model.py` | `ModelRunORM` | `model_runs` |

Registrados en: `app/extensions/db/models_registry.py`

### Dominio (`app/modules/agent/domain/`)
| Archivo | Contenido |
|---------|-----------|
| `analysis_result.py` | `AnalysisResult` + `RuleCheckDetail` — valor de retorno del Prompt Maestro |
| `ml_model_entity.py` | `MLModel` entity (types: xgboost/lightgbm/sklearn/nn) |
| `model_run_entity.py` | `ModelRun` entity (statuses: running/success/failed) |
| `ml_model_repository.py` | ABC interface `MLModelRepository` |
| `model_run_repository.py` | ABC interface `ModelRunRepository` |

### Repositorios
| Domain (interfaz) | Infrastructure (impl) |
|-------------------|-----------------------|
| `domain/ml_model_repository.py` | `infrastructure/ml_model_repository_impl.py` |
| `domain/model_run_repository.py` | `infrastructure/model_run_repository_impl.py` |

### LLM Clients (`app/modules/agent/llm/`)
| Archivo | Clase | Cubre |
|---------|-------|-------|
| `llm_client.py` | `LLMClient` (ABC) | Interfaz: `complete(system, user) -> str` |
| `openai_compatible_client.py` | `OpenAICompatibleClient` | openai, xai (Grok), deepseek, gemini, ollama |
| `anthropic_client.py` | `AnthropicLLMClient` | anthropic (Claude) |
| `llm_factory.py` | `LLMClientFactory` | Crea el cliente según `LLM_PROVIDER` en settings |

**Tabla de base_url por provider:**
- openai → `None` (usa default de la librería)
- xai → `https://api.x.ai/v1`
- deepseek → `https://api.deepseek.com`
- gemini → `https://generativelanguage.googleapis.com/v1beta/openai/`
- ollama → `http://localhost:11434/v1` (api_key="ollama")

### Servicios (`app/modules/agent/services/`)
| Subdir | Servicios |
|--------|-----------|
| `agent/` | `analyze_service.py` — Prompt Maestro (4 fases) |
| `models/` | `list_models_service.py`, `get_model_service.py`, `create_model_service.py`, `update_model_service.py` |
| `model_runs/` | `list_model_runs_service.py`, `create_model_run_service.py`, `finish_model_run_service.py` |

### Prompt Maestro — 4 fases (`AnalyzeService.analyze`)
1. **Fase 1 — Régimen:** `strategy.parameters.regime_required` vs `features.regime`. Si no coincide → RECHAZADA. `None` = acepta cualquier régimen.
2. **Fase 2 — Reglas:** evalúa cada `{indicator, operator, value}` contra features. Si ALGUNA falla → RECHAZADA.
3. **Fase 3 — LLM:** genera entry/SL/TP. Python calcula `position_size = (capital × risk_pct) / |entry − SL|`.
4. **Fase 4 — R/R:** `(TP − entry) / (entry − SL) >= AGENT_MIN_RR_RATIO` (default 2.0). Si no → RECHAZADA.

### Provider (`app/modules/agent/providers/agent_provider.py`)
- `AgentServiceFactory` — instancia repos propios + borrowed de strategies, accounts, features, market
- `LLMClientFactory.create(settings)` se llama por request (respeta cambios de config en runtime)

### Endpoints REST
| Método | Ruta | Auth | Nota |
|--------|------|------|------|
| POST | `/agent/analyze` | token | Prompt Maestro — retorna 200 siempre (APPROVED o REJECTED) |
| GET | `/api/models` | token | Lista modelos ML; filtro: `?status=active` |
| POST | `/api/models` | admin | Crea modelo ML |
| GET | `/api/models/{id}` | token | Detalle de modelo |
| PUT | `/api/models/{id}` | admin | Actualiza modelo (status/artifact_uri/meta) |
| GET | `/api/model-runs` | token | Lista runs; requiere `?model_id=X` |
| POST | `/api/model-runs` | admin | Crea run (status=running) |
| POST | `/api/model-runs/{id}/finish` | admin | Finaliza run (success/failed + metrics) |

Routers registrados en `app/app_factory.py`:
```python
from app.modules.agent.rest import agent_router, models_router, model_runs_router
```

### Páginas web
| URL | Template | JS |
|-----|----------|----|
| `/agent` | `templates/agent/analyze.html` | `static/js/agent/analyze.js` |

### Settings LLM/Agent (en `app/common/config/settings.py`)
```python
LLM_PROVIDER      # openai | anthropic | xai | deepseek | gemini | ollama (default: openai)
LLM_MODEL         # nombre del modelo (default: gpt-4o)
LLM_API_KEY       # clave del provider
LLM_BASE_URL      # override base_url (opcional)
LLM_TEMPERATURE   # (default: 0.1)
LLM_MAX_TOKENS    # (default: 1024)
AGENT_MIN_RR_RATIO  # ratio R/R mínimo (default: 2.0)
AGENT_MASTER_PROMPT # prompt del sistema configurable (env var)
```

### Tests
- `tests/agent/test_analyze_service.py` — 20 tests unitarios, LLM 100% mockeado
  - `TestAnalyzeDataLoading` (6), `TestRegimeFilter` (3), `TestRulesValidation` (3)
  - `TestLLMIntegration` (4), `TestRRFilter` (2), `TestPositionSizing` (1), `TestFullApprovedPath` (1)

---

## Archivos de infraestructura críticos (nunca romper)

| Archivo | Qué hace |
|---------|---------|
| `app/extensions/db/models_registry.py` | Importa TODOS los modelos ORM (side-effect). Al crear modelo nuevo → agregar aquí |
| `app/app_factory.py` | Registra middlewares + routers. Al crear router nuevo → agregar aquí |
| `app/modules/web/routes.py` | Páginas HTML. Al crear página nueva → agregar ruta aquí |
| `app/common/security/security_headers.py` | CSP. Al crear rutas web nuevas (`/market/`, `/admin/`, etc.) → agregar prefijo a `web_prefixes` |
| `app/extensions/db/session.py` | `get_db()` dependency de FastAPI |
| `app/common/contracts/service_result.py` | `ServiceResult[T]` — contrato de todos los servicios |
| `app/common/http/response_builder.py` | `build_list_response`, `build_created_response`, etc. |

---

## Checklist al crear un módulo nuevo

1. [ ] Crear `domain/` — entidades + interfaces repositorio
2. [ ] Crear `infrastructure/` — modelos ORM + impl repositorios
3. [ ] Registrar modelos ORM en `models_registry.py`
4. [ ] Crear `services/` — lógica, retorna ServiceResult
5. [ ] Crear `providers/` — Factory + `get_<modulo>_factory()`
6. [ ] Crear `rest/` — routes, schemas, error_messages por recurso
7. [ ] Registrar router(es) en `app_factory.py`
8. [ ] Si hay páginas web: agregar en `web/routes.py`
9. [ ] Si las páginas son nuevos prefijos (ej: `/features/`): agregar a `_is_web_route()` en `security_headers.py`
10. [ ] Crear templates HTML + JS en `static/js/<modulo>/`
11. [ ] Si hay seed: `seeds/seed_<modulo>.sql` (idempotente)
