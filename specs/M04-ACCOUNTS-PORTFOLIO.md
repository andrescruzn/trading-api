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
| Prefijo API | `/api/accounts` (la página del front es `/#/portfolio`) |
| Frontend | `frontend/src/modules/accounts` |
| Última revisión | 2026-10-19 |

## Descripción

**En palabras simples:** Es la billetera. Guarda información sobre tu dinero: cuánto tienes, en qué exchanges, y cómo ha evolucionado tu capital en el tiempo.

**Qué hace:**
- Registra tus **cuentas de trading** (puedes tener varias, en distintos exchanges)
- Cada cuenta puede ser **paper** (simulada, sin dinero real) o **live** (dinero real)
- Guarda los **balances**: cuánto tienes de cada moneda (USDT, BTC, ETH, etc.) — snapshots inmutables
- Las credenciales de API (api_key/api_secret) se cifran con Fernet antes de guardarlas en la BD
- Equity curve vía time series de `account_balances`

## Páginas

Hash routing: la URL real es `/#/<ruta>`.

**Páginas — Usuario (cualquier usuario autenticado):**
- `/#/portfolio` — "Mis cuentas": lista tus cuentas, crea/edita (diálogo), y abre un panel lateral con el historial de balances donde puedes registrar uno nuevo

**Páginas — Administrador (solo admin):**
- `/#/admin/accounts` — "Todas las cuentas" (Administración → Supervisión): vista global de todas las cuentas del sistema (con su panel de balances)

## Entregables

Tablas: `accounts`, `account_balances` (`portfolio_snapshots` es por bot: tiene modelo ORM aquí, pero ningún servicio la escribe)

Entregables:
- ✅ CRUD cuentas (exchange + API key/secret cifrada con Fernet → `meta['enc_creds']`)
- ✅ Registro de balances por moneda (USDT, BTC, etc.) — snapshots inmutables
- ✅ Equity curve vía time series de `account_balances`
- ✅ Endpoints: GET/POST `/api/accounts`, GET/PUT `/api/accounts/{id}`, GET/POST `/api/accounts/{id}/balances`
- ✅ Cifrado simétrico: `CredentialsCipher` (Fernet, `CREDENTIALS_SECRET_KEY`)
- ✅ Web UI: `/#/portfolio` (panel usuario) + `/#/admin/accounts` (vista admin) — en React desde 2026-10-08
- ✅ 36 tests unitarios pasando (list/get/create/update accounts + list/record balances)
- Test unitarios

> Nota: el roadmap original citaba la página `/accounts`; la ruta real del panel de usuario es **`/#/portfolio`** (`frontend/src/routes/_app/portfolio.lazy.tsx`).

## Decisiones de diseño

| Decisión | Motivo | Alternativa descartada |
|---|---|---|
| API key/secret cifradas con **Fernet** (`CredentialsCipher`, clave `CREDENTIALS_SECRET_KEY`) y guardadas en `meta['enc_creds']` | Nunca se persisten credenciales en claro; la clave vive fuera de la BD | Guardar en claro / en una tabla aparte sin cifrar |
| `CredentialsCipher.from_settings()` arma un **MultiFernet**: cifra con `CREDENTIALS_SECRET_KEY` y descifra con ella o con cualquiera de `CREDENTIALS_PREVIOUS_KEYS` (lista separada por comas); `rotate(token)` re-cifra con la clave actual | Permite rotar la clave sin dejar ilegibles las cuentas existentes | Una sola clave Fernet (cambiarla rompía todas las `enc_creds`) |
| `api_key` ≤ 512 y `api_secret` ≤ 1024 caracteres en los schemas de crear/editar | Acota la entrada antes de cifrar y guardar en el JSON `meta` | Sin límite |
| Balances como **snapshots inmutables** (`UNIQUE (account_id, asset, ts)`) | La equity curve se obtiene como serie temporal sin recalcular ni mutar histórico | Un saldo único actualizable por activo |
| Cuenta `paper` o `live` (`accounts.mode`) y `status` `active`/`suspended` | Mismo modelo para simulación y dinero real; el modo del bot decide el *executor* en [M8](M08-ORDERS-EXECUTION.md) | Tablas separadas por modo |
| Propiedad: un usuario solo ve/edita sus cuentas; el admin ve todas (`belongs_to` + `is_admin`) | Aislamiento entre usuarios | Filtrar solo en la UI |
| La cuenta valida el exchange (`EXCHANGE_NOT_FOUND`) y el modo (`ACCOUNT_INVALID_MODE`) al crear | Errores claros con códigos estables | Dejar que fallen los `CHECK` de MySQL |
| `portfolio_snapshots` diferida: el modelo ORM existe (`infrastructure/portfolio_snapshot_model.py`, registrado en `models_registry.py` para que Alembic gestione el esquema completo), pero no hay entidad, repositorio ni servicio que la escriba | La tabla es por bot (`bot_id`, [M7](M07-BOTS-SIGNALS.md)), no por cuenta | Snapshots por cuenta |
| Ruta REST `/api/accounts` y página en `/#/portfolio` | Desde 2026-10-08 toda la API vive bajo `/api` y la UI usa hash routing, así que ya no hay colisión; se mantuvo `/portfolio` por continuidad de URLs | Página en `/accounts` |

## Avance

| Métrica | Valor | Evidencia |
|---|---|---|
| Alcance original | **100 %** (8/8) | CRUD, balances, equity curve, cifrado, UI usuario + admin y 36 tests |
| Madurez | **≈ 79 %** | Funcionalidad 85 · Tests 80 · Seguridad 90 · Operación 60 |

- **Funcionalidad (85):** los balances se registran **a mano** (`POST /api/accounts/{id}/balances`); no se sincronizan desde el exchange.
- **Tests (80):** 6 suites en `tests/accounts/` (list/get/create/update de cuentas, list/record de balances).
- **Seguridad (90):** cifrado Fernet (MultiFernet con claves anteriores), control de propiedad y longitud máxima de las credenciales en los schemas.
- **Operación (60):** la clave se puede rotar (`CREDENTIALS_PREVIOUS_KEYS`), pero no hay herramienta que re-cifre las cuentas; sin validación de credenciales contra el exchange.

## Posibles mejoras

| Prioridad | Mejora | Esfuerzo |
|---|---|---|
| Alta | Sincronizar balances desde el exchange con ccxt `fetch_balance` (hoy son manuales) — además alimentaría la `closing_equity` de [M10](M10-BILLING.md) | M |
| Alta | "Probar conexión": validar API key/secret y permisos (solo lectura/trading, sin retiro) antes de guardar la cuenta | S |
| Media | Script o job que re-cifre todas las `enc_creds` con la clave nueva (`CredentialsCipher.rotate`) para poder retirar la vieja de `CREDENTIALS_PREVIOUS_KEYS` (hoy la rotación solo descifra con las claves anteriores; nada llama a `rotate`) | S |
| Media | Equity total valorada en la moneda base (conversión de activos) y gráfico de equity curve en `/#/portfolio` (hoy el panel de balances es una tabla) | M |
| Media | Usar `portfolio_snapshots` (tabla y modelo ORM creados; falta entidad, repositorio y un servicio que la escriba) para equity por bot | M |
| Baja | Borrado lógico / archivado de cuentas | S |

## Fuera de alcance y pendientes conocidos

- Sincronización automática de balances con el exchange.
- `portfolio_snapshots`: la tabla y su modelo ORM (`PortfolioSnapshotModel`) existen, pero ningún servicio la escribe ni la lee.
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
| `portfolio_snapshot_model.py` | `PortfolioSnapshotModel` | `portfolio_snapshots` (por bot: `equity`, `cash`, `unrealized_pnl`, `realized_pnl`; sin repositorio ni servicio) |

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

Provider: `app/modules/accounts/providers/account_provider.py` → `AccountServiceFactory` + `get_account_factory(session)`; construye el cifrado con `CredentialsCipher.from_settings()` (clave actual + `CREDENTIALS_PREVIOUS_KEYS`).

Cifrado: `app/common/security/credentials_cipher.py` → `CredentialsCipher` (MultiFernet: `encrypt`, `decrypt`, `rotate`). Lo reutilizan [M8](M08-ORDERS-EXECUTION.md) (`LiveExecutor`, `OrderServiceFactory`, también con `from_settings()`).

Schemas (`rest/accounts/schemas.py`): `api_key` `max_length=512`, `api_secret` `max_length=1024` (crear y editar); `name` 1–120, `base_currency` ≤ 16, `credentials_label` ≤ 255.

### Endpoints REST
| Método | Ruta | Auth | Nota |
|--------|------|------|------|
| GET | `/api/accounts` | token | Admin ve todas; usuario, las suyas |
| POST | `/api/accounts` | token | Crea cuenta (cifra credenciales si se envían) |
| GET | `/api/accounts/{id}` | token | Detalle con control de propiedad |
| PUT | `/api/accounts/{id}` | token | Actualiza cuenta |
| GET | `/api/accounts/{id}/balances` | token | Serie de balances |
| POST | `/api/accounts/{id}/balances` | token | Registra un snapshot de balance |

Routers registrados en `app/app_factory.py` (dentro de `api_routers`, con `prefix=settings.API_PREFIX`):
```python
from app.modules.accounts.rest import accounts_router, balances_router
```

### Frontend (`frontend/src/modules/accounts/`)
| Ruta | Archivo de ruta | Página / componentes |
|-----|----------|----|
| `/#/portfolio` | `routes/_app/portfolio.lazy.tsx` | `pages/portfolio.tsx` (`PortfolioPage`) + `components/account-form-dialog.tsx` + `components/account-balances-sheet.tsx` + `components/record-balance-dialog.tsx` |
| `/#/admin/accounts` | `routes/_app/admin/accounts.lazy.tsx` | `pages/admin-accounts.tsx` + `components/account-balances-sheet.tsx` |

- API: `api/accounts.api.ts`; hooks `use-accounts-queries.ts` (`useAccountsQuery`, reutilizado por dashboard, agent, bots y billing) y `use-accounts-mutations.ts`; etiquetas `lib/accounts-labels.ts`; badges `components/account-badges.tsx`.

### Seed
- `database/seeds/accounts.py` — cuentas paper de ejemplo (Binance y Bybit) con balances en USDT para **cada** usuario demo (Andrés y Dayron), idempotente por (usuario, nombre). El usuario que no exista se omite.
- `account_balances` es una serie temporal (UNIQUE incluye `ts`): el balance inicial solo se inserta si el activo no tiene ninguna foto. Con `get_or_create` el seed fallaba (`MultipleResultsFound`) en cuanto alguien registraba un segundo balance.

## Gotchas críticos

- **`CREDENTIALS_SECRET_KEY` es obligatoria** fuera de `development`/`testing` (settings falla al arrancar sin ella). Perderla deja las `enc_creds` ilegibles; para **cambiarla**, poner la nueva en `CREDENTIALS_SECRET_KEY` y la vieja en `CREDENTIALS_PREVIOUS_KEYS` hasta re-cifrar las cuentas (si se quita la vieja antes, las cuentas cifradas con ella dejan de descifrarse).
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
- **2026-10-08** — API headless (/api), páginas migradas a React (frontend/).
- **2026-10-10** — Seed `accounts`: cuentas para Dayron y fix del re-run con varias fotos de balance.
- **2026-10-19** — Auditoría de seguridad: `api_key` ≤ 512 y `api_secret` ≤ 1024 en los schemas; `CredentialsCipher.from_settings()` con MultiFernet y `CREDENTIALS_PREVIOUS_KEYS` (rotación de clave sin perder las cuentas). Spec corregida: `portfolio_snapshots` sí tiene modelo ORM (`portfolio_snapshot_model.py`, registrado), aunque nadie la escribe.
