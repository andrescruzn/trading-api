# Trading AI API — Instrucciones para Claude

## Stack
- **Lenguaje:** Python 3.12
- **Framework:** FastAPI 0.128 + Uvicorn (ASGI)
- **ORM:** SQLAlchemy 2.x (async-ready, DeclarativeBase)
- **Driver:** PyMySQL 1.1
- **DB:** MySQL 8.x — base de datos `trading_ai`
- **Auth:** JWT HS256 en HTTP-only cookies
- **Validación:** Pydantic v2
- **Templates mail:** Jinja2
- **Arquitectura:** Screaming Architecture (módulos por dominio)

---

## Estructura del proyecto

```
app/
  app_factory.py          # Crea la app FastAPI (middlewares, routers, handlers)
  main.py                 # Entrypoint Uvicorn
  common/
    config/settings.py    # Settings singleton (lee .env, fail-fast en prod)
    contracts/
      service_result.py   # ServiceResult[T], ServiceError
    errors/
      errors.py           # register_error_handlers (AuthException, JwtCodecError)
      error_messages.py   # Mensajes globales (si aplica)
    http/
      http_responder.py   # send(msg, status_code, data) -> JSONResponse
      response_builder.py
    security/
      jwt/                # jwt_guard, role_guard, jwt_utils, auth_exceptions
      otp/                # otp_generator, otp_hasher
      password_hasher.py
      rate_limiter.py
      sanitization/       # html_sanitizer, input_cleaner
    logging/              # configure_logging(), LoggingMiddleware
    utils/                # datetime_utils, input_cleaner
  extensions/
    db/
      base.py             # class Base(DeclarativeBase)
      config.py           # Engine + sessionmaker
      session.py          # get_db() -> dependency FastAPI
      models_registry.py  # Importa todos los modelos ORM (side-effect)
  modules/
    health/               # GET /health
    mailer/               # SMTP service, templates Jinja2
    users/
      domain/             # UserEntity, UserRepository (interfaz)
      infrastructure/     # UserModel, RoleModel, UserRepositoryImpl
      providers/          # auth_provider (DI / wiring)
      rest/auth/          # routes.py, schemas.py, error_messages.py
      services/auth/      # login_password, login_otp, verify_otp, logout, rotate_token
```

---

## Patrón de capas (OBLIGATORIO)

```
REST (routes.py)
  └── llama Service
        └── usa Repository (interfaz)
              └── implementado por RepositoryImpl (ORM)
```

### Reglas estrictas de capas
1. **Domain** — entidades puras + interfaces de repositorio. Sin ORM, sin FastAPI.
2. **Infrastructure** — modelos SQLAlchemy + implementación de repositorios.
3. **Services** — lógica de negocio. Siempre retornan `ServiceResult[T]`. Nunca lanzan excepciones de negocio.
4. **REST** — routes FastAPI + schemas Pydantic. Convierte `ServiceResult` a `JSONResponse`. Aquí van los mensajes UI.

---

## Contrato estándar de respuesta HTTP

Toda respuesta usa `http_responder.send()`:

```python
from app.common.http import send

return send(msg="OK", status_code=200, data={"user_id": 1})
```

Envelope JSON:
```json
{
  "msg": "string",
  "errorCode": 200,
  "data": {} | []
}
```

---

## ServiceResult

```python
# Éxito
return ServiceResult.ok(data={"token": "..."})

# Error
return ServiceResult.fail(
    code="AUTH_INVALID_CREDENTIALS",
    http_status=401,
    meta={"attempts_left": 2}   # solo para control interno, no para UI
)
```

- `code` es un string estable en SCREAMING_SNAKE_CASE.
- Los mensajes de UI que corresponden a cada código se definen en `rest/<módulo>/error_messages.py`.
- El servicio **nunca** define mensajes de usuario final.

---

## Añadir un nuevo módulo

1. Crear `app/modules/<nombre>/domain/` → entidad + interfaz repositorio
2. Crear `app/modules/<nombre>/infrastructure/` → modelo ORM + impl repositorio
3. Crear `app/modules/<nombre>/services/` → lógica, retorna `ServiceResult`
4. Crear `app/modules/<nombre>/rest/` → `routes.py`, `schemas.py`, `error_messages.py`
5. Crear `app/modules/<nombre>/providers/` → wiring DI si aplica
6. Registrar modelo ORM en `app/extensions/db/models_registry.py`
7. Registrar router en `app/app_factory.py`

---

## Convenciones de código

- `# -*- coding: utf-8 -*-` al inicio de cada archivo `.py`
- Imports absolutos: siempre desde `app.*`
- Modelos ORM solo en `infrastructure/`, heredan de `Base`
- `session.commit()` solo dentro de repositorios
- Schemas Pydantic en `rest/<módulo>/schemas.py`
- Passwords: siempre bcrypt via `password_hasher.py`
- OTP: generar con `otp_generator.py`, hashear con `otp_hasher.py` antes de guardar en DB
- JWT: HS256, cookie HTTP-only, rotación de JTI en cada sesión activa

---

## Seguridad

- **Autenticación:** `jwt_guard` como dependency FastAPI
- **Autorización por rol:** `role_guard`
- **Rate limiting:** `rate_limiter.py`
- **Sanitización:** `html_sanitizer.py` + `input_cleaner.py` en entradas de usuario
- **Cookies:** `HttpOnly=True`, `Secure=True` (producción), `SameSite=Lax`
- **Lockout:** 3 intentos fallidos → bloqueo temporal en `login_locked_until`

---

## Base de datos — Resumen de tablas

DB: `trading_ai` | Motor: InnoDB | Charset: utf8mb4 | Timestamps: TIMESTAMP(6)
IDs: BIGINT AUTO_INCREMENT | Precios/cantidades: DECIMAL(30,12)
Schema completo en `.claude/db_schema.sql`

### Catálogos / Referencias
| Tabla | Propósito |
|---|---|
| `roles` | Roles de usuario. id=1: `user`, id=2: `admin` |
| `exchanges` | Exchanges/brokers/data vendors disponibles |
| `symbols` | Pares y activos por exchange (crypto/metal/etf/stock/forex) |
| `timeframes` | Marcos temporales (code: `1m`, `5m`... + seconds) |
| `feature_sets` | Definición de conjuntos de features ML (spec JSON) |
| `strategies` | Estrategias de trading con parameters JSON |

### Usuarios y cuentas
| Tabla | Propósito |
|---|---|
| `users` | Usuarios con auth (OTP + password), lockout, JTI de sesión |
| `accounts` | Cuentas de trading por usuario (paper/live, ligada a exchange) |
| `account_balances` | Saldo por activo en cada cuenta (snapshots) |

### Market Data / ML
| Tabla | Propósito |
|---|---|
| `candles` | OHLCV por símbolo y timeframe |
| `candle_features` | Features calculadas por vela y feature_set |
| `datasets` | Datasets para entrenamiento (query_spec JSON) |
| `models` | Modelos ML registrados (xgboost/lightgbm/sklearn/nn) |
| `model_runs` | Ejecuciones de entrenamiento con métricas y params |

### Ejecución de Bots
| Tabla | Propósito |
|---|---|
| `bots` | Bots de trading (strategy + symbol + timeframe + account) |
| `signals` | Señales generadas por bot (buy/sell/hold + confidence) |
| `orders` | Órdenes emitidas (market/limit/stop/stop_limit) |
| `fills` | Ejecuciones (parciales o totales) de órdenes |
| `positions` | Posición abierta actual por bot y símbolo |
| `predictions` | Predicciones de modelos ML por bot |
| `portfolio_snapshots` | Snapshot periódico de equity, cash y PnL por bot |

### Alertas y Auditoría
| Tabla | Propósito |
|---|---|
| `alert_rules` | Reglas de alertas (pnl/drawdown/signal/error/price) |
| `alert_events` | Eventos disparados por reglas con delivery_status |
| `audit_logs` | Log de auditoría de acciones de usuario y bots |
| `system_events` | Eventos internos del sistema (market_data/execution/scheduler/api) |

---

## ENUMs importantes (CHECK constraints MySQL)

```
accounts.mode          : paper | live
accounts.status        : active | suspended
bots.status            : running | stopped | paused | error
bots.mode              : paper | live
orders.side            : buy | sell
orders.type            : market | limit | stop | stop_limit
orders.status          : new | sent | partially_filled | filled | canceled | rejected
signals.action         : buy | sell | hold
models.model_type      : xgboost | lightgbm | sklearn | nn
models.status          : active | deprecated | archived
symbols.asset_class    : crypto | metal | etf | stock | forex
exchanges.type         : crypto_exchange | broker | data_vendor
users.status           : active | blocked | disabled
alert_rules.rule_type  : pnl | drawdown | signal | error | price
alert_events.severity  : info | warning | critical
alert_events.delivery  : pending | sent | failed
system_events.level    : info | warning | error
system_events.component: market_data | execution | scheduler | api
model_runs.status      : running | success | failed
```

---

## Skills disponibles

Los skills viven en `.claude/skills/`. Claude debe leerlos con la herramienta Read **antes** de generar código, según la tarea:

| Skill | Ruta | Cuándo leerlo |
|---|---|---|
| Backend Core | `.claude/skills/backend-core/SKILL.md` | Antes de crear cualquier módulo o estructura |
| Architecture | `.claude/skills/architecture/SKILL.md` | Antes de decidir patrones, SOLID, sub-modularización |
| API Standards | `.claude/skills/api-standards/SKILL.md` | Antes de crear endpoints, responses, error codes |
| Code Style | `.claude/skills/code-style/SKILL.md` | Antes de escribir código Python (PEP8, type hints) |
| Testing | `.claude/skills/testing/SKILL.md` | Antes de escribir tests (pytest, mocking, coverage) |
| Security | `.claude/skills/security/SKILL.md` | Antes de implementar auth, input handling, o código sensible |
| Database | `.claude/skills/database/SKILL.md` | Antes de escribir SQL, seeds o migraciones |
| Maquetación, frontend, diseño, CSS | `.claude/skills/frontend-design/SKILL.md` | Antes de maquetar algo nuevo, mejorar maquetación, cambiar CSS y/o añadir CSS |

---

## Reglas para Claude

1. Respetar siempre la arquitectura de capas: domain → infra → service → rest.
2. Los servicios nunca definen mensajes de UI; solo códigos de error estables.
3. Usar siempre `ServiceResult` en services y `http_responder.send()` en routes.
4. Al crear un nuevo modelo ORM, registrarlo en `models_registry.py`.
5. Respetar los ENUMs de MySQL al generar código o queries.
6. Usar `TIMESTAMP(6)` y `BIGINT` para nuevas tablas.
7. Usar `DECIMAL(30,12)` para precios, cantidades y balances financieros.
8. Columnas JSON (`meta`, `spec`, `params`, `payload`, `reasons`) para datos flexibles.
9. No hacer `session.commit()` fuera de la capa repositorio.
10. No hardcodear IDs de roles; usar `settings.AUTH_ADMIN_ROLE_ID` / `settings.AUTH_USER_ROLE_ID`.
11. Leer el skill correspondiente **antes** de generar código, nunca después.
