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

## 📌 Módulo 3 — Feature Engineering (SIGUIENTE)

### Tablas que usará
| Tabla | Acción | Nota |
|-------|--------|------|
| `candle_features` | WRITE | Features calculadas por vela + feature_set |
| `feature_sets` | WRITE | Definición de conjuntos de indicadores |
| `candles` | READ | Fuente de datos para calcular indicadores |
| `symbols` | READ | Para validar symbol_id |
| `timeframes` | READ | Para validar timeframe_id |

### Tablas que NO debe tocar
- `exchanges`, `users`, `roles`, `http_audit_*`

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
