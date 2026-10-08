# Módulo 4 — Accounts & Portfolio (Cuentas y Portafolio) ✅ COMPLETO

← [Índice de módulos](_ROOT.md)

## Ficha

| Campo | Valor |
|---|---|
| Estado | ✅ Completo |
| Avance (alcance original) | 100 % — 8/8 entregables |
| Madurez (estimada) | 79 % — ver [Avance](#avance) |
| Tablas | `accounts`, `account_balances` (R/W); `exchanges` (R) |
| Depende de | [M1](M01-AUTH.md), [M2](M02-MARKET-DATA.md) (exchange de la cuenta) |
| Lo usan | [M6](M06-AI-AGENT.md) (capital disponible), [M7](M07-BOTS-SIGNALS.md) (cuenta del bot), [M8](M08-ORDERS-EXECUTION.md) (credenciales del `LiveExecutor`), [M10](M10-BILLING.md) (cuenta administrada) |
| Prefijo API | `/accounts` (sin `/api/`; la página web es `/portfolio`) |
| Última revisión | 2026-10-07 |

## Descripción

**En palabras simples:** Es la billetera. Guarda información sobre tu dinero: cuánto tienes, en qué exchanges, y cómo ha evolucionado tu capital en el tiempo.

**Qué hace:**
- Registra tus **cuentas de trading** (puedes tener varias, en distintos exchanges)
- Cada cuenta puede ser **paper** (simulada, sin dinero real) o **live** (dinero real)
- Guarda los **balances**: cuánto tienes de cada moneda (USDT, BTC, ETH, etc.) — snapshots inmutables
- Las credenciales de API (api_key/api_secret) se cifran con Fernet antes de guardarlas en la BD
- Equity curve vía time series de `account_balances`

## Páginas

**Páginas — Usuario (cualquier usuario autenticado):**
- `/portfolio` — Panel de cuentas: lista tus cuentas, crea nuevas, consulta balances y equity curve

**Páginas — Administrador (solo admin):**
- `/admin/accounts` — Vista global de todas las cuentas del sistema

## Entregables

Tablas: `accounts`, `account_balances` (`portfolio_snapshots` → Módulo 7, requiere bot_id)

Entregables:
- ✅ CRUD cuentas (exchange + API key/secret cifrada con Fernet → `meta['enc_creds']`)
- ✅ Registro de balances por moneda (USDT, BTC, etc.) — snapshots inmutables
- ✅ Equity curve vía time series de `account_balances`
- ✅ Endpoints: GET/POST `/accounts`, GET/PUT `/accounts/{id}`, GET/POST `/accounts/{id}/balances`
- ✅ Cifrado simétrico: `CredentialsCipher` (Fernet, `CREDENTIALS_SECRET_KEY`)
- ✅ Web UI: `/accounts` (panel usuario) + `/admin/accounts` (vista admin)
- ✅ 36 tests unitarios pasando (list/get/create/update accounts + list/record balances)
- Test unitarios

> Nota: el roadmap original citaba la página `/accounts`; la ruta real del panel de usuario es **`/portfolio`** (`app/modules/web/routes.py`).

## Decisiones de diseño

| Decisión | Motivo | Alternativa descartada |
|---|---|---|
| API key/secret cifradas con **Fernet** (`CredentialsCipher`, clave `CREDENTIALS_SECRET_KEY`) y guardadas en `meta['enc_creds']` | Nunca se persisten credenciales en claro; la clave vive fuera de la BD | Guardar en claro / en una tabla aparte sin cifrar |
| Balances como **snapshots inmutables** (`UNIQUE (account_id, asset, ts)`) | La equity curve se obtiene como serie temporal sin recalcular ni mutar histórico | Un saldo único actualizable por activo |
| Cuenta `paper` o `live` (`accounts.mode`) y `status` `active`/`suspended` | Mismo modelo para simulación y dinero real; el modo del bot decide el *executor* en [M8](M08-ORDERS-EXECUTION.md) | Tablas separadas por modo |
| Propiedad: un usuario solo ve/edita sus cuentas; el admin ve todas (`belongs_to` + `is_admin`) | Aislamiento entre usuarios | Filtrar solo en la UI |
| La cuenta valida el exchange (`EXCHANGE_NOT_FOUND`) y el modo (`ACCOUNT_INVALID_MODE`) al crear | Errores claros con códigos estables | Dejar que fallen los `CHECK` de MySQL |
| `portfolio_snapshots` diferida: requiere `bot_id` ([M7](M07-BOTS-SIGNALS.md)) | La tabla es por bot, no por cuenta | Snapshots por cuenta |
| Ruta sin prefijo `/api/` (`/accounts`) y página en `/portfolio` | Evita colisión con la página web | Página en `/accounts` |

## Avance

| Métrica | Valor | Evidencia |
|---|---|---|
| Alcance original | **100 %** (8/8) | CRUD, balances, equity curve, cifrado, UI usuario + admin y 36 tests |
| Madurez | **≈ 79 %** | Funcionalidad 85 · Tests 80 · Seguridad 90 · Operación 60 |

- **Funcionalidad (85):** los balances se registran **a mano** (`POST /accounts/{id}/balances`); no se sincronizan desde el exchange.
- **Tests (80):** 6 suites en `tests/accounts/` (list/get/create/update de cuentas, list/record de balances).
- **Seguridad (90):** cifrado Fernet y control de propiedad.
- **Operación (60):** sin rotación de clave ni validación de credenciales contra el exchange.

## Posibles mejoras

| Prioridad | Mejora | Esfuerzo |
|---|---|---|
| Alta | Sincronizar balances desde el exchange con ccxt `fetch_balance` (hoy son manuales) — además alimentaría la `closing_equity` de [M10](M10-BILLING.md) | M |
| Alta | "Probar conexión": validar API key/secret y permisos (solo lectura/trading, sin retiro) antes de guardar la cuenta | S |
| Media | Rotación de `CREDENTIALS_SECRET_KEY` con re-cifrado de `enc_creds` (cambiar la clave hoy deja las cuentas sin poder descifrar) | M |
| Media | Equity total valorada en la moneda base (conversión de activos) y gráfico en `/portfolio` | M |
| Media | Usar `portfolio_snapshots` (tabla creada y sin código asociado) para equity por bot | M |
| Baja | Borrado lógico / archivado de cuentas | S |

## Fuera de alcance y pendientes conocidos

- Sincronización automática de balances con el exchange.
- `portfolio_snapshots` (la tabla existe, no hay modelo ORM ni servicio).
- Multi-moneda con conversión a una divisa base.
- Retiros/depósitos: el sistema no mueve fondos entre cuentas.

## Detalle técnico

> Generado desde el código el 2026-10-07: el antiguo `MODULES_MAP.md` no tenía sección para M4.

### Tablas en BD
| Tabla | Acción | Nota |
|-------|--------|------|
| `accounts` | WRITE | `mode` paper/live, `status` active/suspended, `credentials_ref`, `meta` JSON (`enc_creds`) |
| `account_balances` | WRITE | Snapshots por `asset` con `free`/`locked`; UNIQUE `(account_id, asset, ts)`, CASCADE al borrar la cuenta |
| `exchanges` | READ | Valida `exchange_id` al crear la cuenta |

### Modelos ORM (`app/modules/accounts/infrastructure/`)
| Archivo | Clase | Tabla |
|---------|-------|-------|
| `account_model.py` | `AccountModel` | `accounts` |
| `account_balance_model.py` | `AccountBalanceModel` | `account_balances` |

### Dominio y repositorios
| Domain | Infrastructure |
|--------|----------------|
| `domain/account_entity.py` → `Account` (`VALID_MODES`, `belongs_to()`) | — |
| `domain/account_balance_entity.py` → `AccountBalance` | — |
| `domain/account_repository.py` (ABC) | `infrastructure/account_repository_impl.py` → `SqlAlchemyAccountRepository` |
| `domain/account_balance_repository.py` (ABC) | `infrastructure/account_balance_repository_impl.py` → `SqlAlchemyAccountBalanceRepository` |

### Servicios (`app/modules/accounts/services/`)
| Subdir | Servicios |
|--------|-----------|
| `accounts/` | `list_accounts_service.py`, `get_account_service.py`, `create_account_service.py`, `update_account_service.py` |
| `balances/` | `list_balances_service.py`, `record_balance_service.py` |

Provider: `app/modules/accounts/providers/account_provider.py` → `AccountServiceFactory` + `get_account_factory(session)`

Cifrado: `app/common/security/credentials_cipher.py` → `CredentialsCipher` (Fernet). Lo reutilizan [M8](M08-ORDERS-EXECUTION.md) (`LiveExecutor`, `OrderServiceFactory`).

### Endpoints REST
| Método | Ruta | Auth | Nota |
|--------|------|------|------|
| GET | `/accounts` | token | Admin ve todas; usuario, las suyas |
| POST | `/accounts` | token | Crea cuenta (cifra credenciales si se envían) |
| GET | `/accounts/{id}` | token | Detalle con control de propiedad |
| PUT | `/accounts/{id}` | token | Actualiza cuenta |
| GET | `/accounts/{id}/balances` | token | Serie de balances |
| POST | `/accounts/{id}/balances` | token | Registra un snapshot de balance |

Routers registrados en `app/app_factory.py`:
```python
from app.modules.accounts.rest import accounts_router, balances_router
```

### Páginas web
| URL | Template | JS |
|-----|----------|----|
| `/portfolio` | `templates/accounts/index.html` | `static/js/accounts/index.js` |
| `/admin/accounts` | `templates/admin/accounts.html` | `static/js/admin/accounts.js` |

### Seed
- `database/seeds/accounts.py` — cuentas paper de ejemplo (Binance y Bybit) con balances, idempotente por (usuario, nombre). Requiere que exista el usuario demo.

## Gotchas críticos

- **`CREDENTIALS_SECRET_KEY` es obligatoria** para cifrar/descifrar credenciales (`CredentialsCipher`); perderla o cambiarla deja las `enc_creds` existentes ilegibles.
- Las cuentas `live` guardan credenciales reales: nunca registrarlas en logs ni devolverlas en las respuestas.
- Los balances son inmutables: para "corregir" uno se registra un snapshot nuevo.

## Tests

- `tests/accounts/` — 36 tests unitarios: `test_list_accounts_service.py`, `test_get_account_service.py`, `test_create_account_service.py`, `test_update_account_service.py`, `test_list_balances_service.py`, `test_record_balance_service.py`.
- **Huecos:** rutas REST y `CredentialsCipher` (cifrado/descifrado y clave inválida).

## Riesgos

- Fuga o pérdida de `CREDENTIALS_SECRET_KEY`: compromete o inutiliza todas las credenciales.
- Balances manuales que no coinciden con el exchange pueden llevar a [M6](M06-AI-AGENT.md) a dimensionar mal las posiciones.

## Historial

- **2026-03** — Módulo completado (CRUD cuentas, balances, cifrado Fernet, UI `/portfolio` y `/admin/accounts`, 36 tests).
- **Posterior** — Es la base de las cuentas administradas de [M10](M10-BILLING.md).
