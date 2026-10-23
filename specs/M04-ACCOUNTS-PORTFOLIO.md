# Módulo 4 — Accounts & Portfolio (Cuentas y Portafolio) ✅ COMPLETO

← [Índice de módulos](_ROOT.md)

## Ficha

| Campo | Valor |
|---|---|
| Estado | ✅ Completo |
| Avance (alcance original) | 100 % — 8/8 entregables (+ 1 de 2026-10-23: billetera única de la plataforma) |
| Madurez (estimada) | 81 % — ver [Avance](#avance) |
| Tablas | `accounts`, `account_balances`, `platform_wallet`, `wallet_snapshots` (R/W); `exchanges` (R) |
| Depende de | [M1](M01-AUTH.md), [M2](M02-MARKET-DATA.md) (exchange de la cuenta) |
| Lo usan | [M6](M06-AI-AGENT.md) (capital disponible), [M7](M07-BOTS-SIGNALS.md) (cuenta del bot), [M8](M08-ORDERS-EXECUTION.md) (credenciales del `LiveExecutor`), [M10](M10-BILLING.md) (cuenta administrada) |
| Prefijo API | `/api/accounts` (la página del front es `/#/portfolio`), `/api/wallet` |
| Frontend | `frontend/src/modules/accounts` |
| Última revisión | 2026-10-23 |

## Descripción

**En palabras simples:** Es la billetera. Guarda información sobre tu dinero: cuánto tienes, en qué exchanges, y cómo ha evolucionado tu capital en el tiempo.

**Qué hace:**
- Registra tus **cuentas de trading** (puedes tener varias, en distintos exchanges)
- Cada cuenta puede ser **paper** (simulada, sin dinero real) o **live** (dinero real)
- Guarda los **balances**: cuánto tienes de cada moneda (USDT, BTC, ETH, etc.) — snapshots inmutables
- Las credenciales de API (api_key/api_secret) se cifran con Fernet antes de guardarlas en la BD
- Equity curve vía time series de `account_balances`
- **Billetera de la plataforma (fondo común, 2026-10-23):** toda la plataforma usa una sola cuenta de exchange como billetera. Su saldo se lee solo del exchange cada pocos minutos (Spot + Funding en Binance y Bybit), se valora en USDT y queda como foto (`wallet_snapshots`): total, libre y en órdenes, con el desglose por activo. Solo la ven super admin y socio

## Páginas

Hash routing: la URL real es `/#/<ruta>`.

**Páginas — Usuario (cualquier usuario autenticado):**
- `/#/portfolio` — "Mis cuentas": lista tus cuentas, crea/edita (diálogo), y abre un panel lateral con el historial de balances donde puedes registrar uno nuevo

**Páginas — Administración (super admin y socio):**
- `/#/admin/wallet` — "Billetera" (Administración → Fondo): cuenta elegida (nombre, exchange, modo), tarjetas Saldo total / Saldo libre / En órdenes / Última lectura, aviso si la última sincronización falló (con el motivo) o si hay activos sin precio, tabla de activos (libre, en órdenes, total, precio, valor) e historial de lecturas. Solo el super admin ve **Sincronizar ahora** y **Elegir / Cambiar billetera** (diálogo con las cuentas activas con exchange y, si son live, con API key)
- `/#/admin/accounts` — "Todas las cuentas" (Administración → Supervisión): vista global de todas las cuentas del sistema (con su panel de balances), columna **Dueño** (nombre y correo) y filtro por dueño

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
- ✅ (2026-10-23) **Billetera única de la plataforma:** tablas `platform_wallet` (una fila) y `wallet_snapshots` (migración `e500b821b8ec`), `WalletGateway` + `CcxtWalletGateway`, `SyncWalletService` (en live graba también `account_balances`), paso del scheduler `sync_platform_wallet`, `GET/PUT /api/wallet`, `POST /api/wallet/sync`, `GET /api/wallet/snapshots` y página Billetera
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
| **Una sola billetera** para toda la plataforma: tabla `platform_wallet` con una fila (CHECK `id = 1`) que apunta a una cuenta existente de `accounts` | Fondo común: el dinero de propietarios, socios e inversores está en una sola cuenta; reutilizar `accounts` conserva el cifrado de credenciales y el `LiveExecutor` | Columna `is_platform_wallet` en `accounts` (difícil de garantizar una sola) · tabla de billeteras por usuario |
| **Saldo leído del exchange** cada `WALLET_SYNC_INTERVAL_SECONDS` (300 s) sumando los tipos de cuenta del exchange (`_EXTRA_BALANCE_TYPES`: Funding en Binance y Bybit); en live también se graba en `account_balances` con la misma hora para todos los activos | El P2P y los depósitos de Binance caen en Funding: sin sumarlo la conciliación del fondo daría diferencias. Grabar `account_balances` mantiene el 1 % de los agentes con el saldo real | Solo `fetch_balance()` (spot) · balances manuales |
| Un activo que tenía saldo y ya no aparece se graba en 0; la moneda base se graba siempre | Si no, su último balance quedaría viejo y el agente seguiría viendo dinero que ya no está | Grabar todos los activos en 0 del exchange (cientos en Binance) |
| **Precios por ticker público** (`fetch_tickers` de `ACTIVO/USDT`); un activo sin precio no suma y se avisa (`missing_prices`). Un fallo de precios no tumba la sincronización | Sin API key y siempre al día; el total nunca incluye un valor inventado | Velas de M2 (solo existen para los símbolos con agentes) |
| Cuenta **paper** aceptada como billetera (desarrollo): la foto se arma con los balances manuales y no se escribe `account_balances` | Probar todo el fondo sin dinero real | Exigir live siempre |
| **API key de solo lectura** recomendada (sin permiso de retiro) | Los retiros los hacen los propietarios en el exchange; una API key filtrada no puede sacar dinero | Retiros automáticos por API |
| `exchange_client.py` (helper compartido) arma el cliente ccxt con credenciales; lo usan el `LiveExecutor` y la billetera, y lanza `ExchangeClientError(code)` (subclase de `RuntimeError`) | Un solo sitio para descifrar credenciales y respetar `LIVE_USE_SANDBOX`; el `LiveExecutor` conserva sus mensajes | Copiar la lógica en la billetera |
| `portfolio_snapshots` diferida: el modelo ORM existe (`infrastructure/portfolio_snapshot_model.py`, registrado en `models_registry.py` para que Alembic gestione el esquema completo), pero no hay entidad, repositorio ni servicio que la escriba | La tabla es por bot (`bot_id`, [M7](M07-BOTS-SIGNALS.md)), no por cuenta | Snapshots por cuenta |
| Ruta REST `/api/accounts` y página en `/#/portfolio` | Desde 2026-10-08 toda la API vive bajo `/api` y la UI usa hash routing, así que ya no hay colisión; se mantuvo `/portfolio` por continuidad de URLs | Página en `/accounts` |

## Avance

| Métrica | Valor | Evidencia |
|---|---|---|
| Alcance original | **100 %** (8/8) | CRUD, balances, equity curve, cifrado, UI usuario + admin y 36 tests |
| Madurez | **≈ 81 %** | Funcionalidad 88 · Tests 75 · Seguridad 90 · Operación 70 |

- **Funcionalidad (88):** la billetera de la plataforma se sincroniza sola con el exchange (2026-10-23); las demás cuentas siguen con balances **a mano**.
- **Operación (70):** sincronización automática de la billetera con el estado del último intento visible en la UI.
- **Tests (80):** 6 suites en `tests/accounts/` (list/get/create/update de cuentas, list/record de balances).
- **Seguridad (90):** cifrado Fernet (MultiFernet con claves anteriores), control de propiedad y longitud máxima de las credenciales en los schemas.
- **Operación (60):** la clave se puede rotar (`CREDENTIALS_PREVIOUS_KEYS`), pero no hay herramienta que re-cifre las cuentas; sin validación de credenciales contra el exchange.

## Posibles mejoras

| Prioridad | Mejora | Esfuerzo |
|---|---|---|
| Media | Sincronizar también las demás cuentas live (hoy solo la billetera de la plataforma) | S |
| Media | Tests de `SyncWalletService` y `CcxtWalletGateway` (hoy verificados a mano con dobles de prueba) | S |
| Baja | Adaptador de billetera para exchanges sin ccxt (p. ej. eToro), implementando `WalletGateway` | L |
| Alta | "Probar conexión": validar API key/secret y permisos (solo lectura/trading, sin retiro) antes de guardar la cuenta | S |
| Media | Script o job que re-cifre todas las `enc_creds` con la clave nueva (`CredentialsCipher.rotate`) para poder retirar la vieja de `CREDENTIALS_PREVIOUS_KEYS` (hoy la rotación solo descifra con las claves anteriores; nada llama a `rotate`) | S |
| Media | Equity total valorada en la moneda base (conversión de activos) y gráfico de equity curve en `/#/portfolio` (hoy el panel de balances es una tabla) | M |
| Media | Usar `portfolio_snapshots` (tabla y modelo ORM creados; falta entidad, repositorio y un servicio que la escriba) para equity por bot | M |
| Baja | Borrado lógico / archivado de cuentas | S |

## Fuera de alcance y pendientes conocidos

- Sincronización automática de las cuentas que no son la billetera de la plataforma.
- eToro (no está en ccxt).
- `portfolio_snapshots`: la tabla y su modelo ORM (`PortfolioSnapshotModel`) existen, pero ningún servicio la escribe ni la lee.
- Multi-moneda con conversión a una divisa base.
- Retiros/depósitos: el sistema no mueve fondos entre cuentas.

## Detalle técnico

> Generado desde el código el 2026-10-07: el antiguo `MODULES_MAP.md` no tenía sección para M4.

### Tablas en BD
| Tabla | Acción | Nota |
|-------|--------|------|
| `accounts` | WRITE | `mode` paper/live, `status` active/suspended, `credentials_ref`, `meta` JSON (`enc_creds`) |
| `account_balances` | WRITE | Snapshots por `asset` con `free`/`locked`; UNIQUE `(account_id, asset, ts)`, CASCADE al borrar la cuenta. Desde 2026-10-23 también los escribe la sincronización de la billetera (live) |
| `platform_wallet` | WRITE | Una sola fila (CHECK `id = 1`): `account_id` (UNIQUE, FK `accounts`), `base_asset` (USDT), `last_synced_at`, `last_sync_error` (código del último fallo), `updated_by_user_id` |
| `wallet_snapshots` | WRITE | Fotos del saldo: `total_value` / `free_value` / `locked_value` (DECIMAL 30,12, en `base_asset`), `source` (`exchange` \| `manual`), `assets` JSON (`[{asset, free, locked, price, value}]`, decimales como texto), `missing_prices` JSON, `ts`; índice `(account_id, ts)` |
| `exchanges` | READ | Valida `exchange_id` al crear la cuenta |

### Modelos ORM (`app/modules/accounts/infrastructure/`)
| Archivo | Clase | Tabla |
|---------|-------|-------|
| `account_model.py` | `AccountModel` | `accounts` |
| `account_balance_model.py` | `AccountBalanceModel` | `account_balances` |
| `platform_wallet_model.py` | `PlatformWalletModel`, `WalletSnapshotModel` | `platform_wallet`, `wallet_snapshots` |
| `portfolio_snapshot_model.py` | `PortfolioSnapshotModel` | `portfolio_snapshots` (por bot: `equity`, `cash`, `unrealized_pnl`, `realized_pnl`; sin repositorio ni servicio) |

### Dominio y repositorios
| Domain | Infrastructure |
|--------|----------------|
| `domain/account_entity.py` → `Account` (`VALID_MODES`, `belongs_to()`) | — |
| `domain/account_balance_entity.py` → `AccountBalance` | — |
| `domain/account_repository.py` (ABC) | `infrastructure/account_repository_impl.py` → `SqlAlchemyAccountRepository` |
| `domain/account_balance_repository.py` (ABC; desde 2026-10-23 `list_latest_by_account` y `record` respeta `balance.ts`) | `infrastructure/account_balance_repository_impl.py` → `SqlAlchemyAccountBalanceRepository` |
| `domain/platform_wallet_entity.py` → `PlatformWallet` (`mark_synced`, `mark_sync_failed`) · `domain/wallet_snapshot_entity.py` → `AssetBalance`, `WalletAssetLine`, `WalletSnapshot`, `value_wallet()` (valoración pura) | — |
| `domain/platform_wallet_repository.py` → `PlatformWalletRepository`, `WalletSnapshotRepository` | `infrastructure/platform_wallet_repository_impl.py` → `SqlAlchemyPlatformWalletRepository`, `SqlAlchemyWalletSnapshotRepository` |
| `domain/wallet_gateway.py` → `WalletGateway` (Protocol: `fetch_balances`, `fetch_prices`), `WalletGatewayError(code)` | `infrastructure/ccxt_wallet_gateway.py` → `CcxtWalletGateway`; `infrastructure/exchange_client.py` → `build_authenticated_client`, `build_public_client`, `ExchangeClientError` |

### Servicios (`app/modules/accounts/services/`)
| Subdir | Servicios |
|--------|-----------|
| `accounts/` | `list_accounts_service.py`, `get_account_service.py`, `create_account_service.py`, `update_account_service.py` |
| `balances/` | `list_balances_service.py`, `record_balance_service.py` |
| `wallet/` | `get_wallet_service.py` (`GetWalletService.get()` → `WalletOverview`, `list_snapshots`), `set_platform_wallet_service.py`, `sync_wallet_service.py` |

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
| POST | `/api/accounts/{id}/balances` | super admin | Registra un snapshot de balance |
| GET | `/api/wallet` | staff | `{configured, wallet, account, latest_snapshot}`; `wallet.last_sync_error_msg` ya en español |
| PUT | `/api/wallet` | super admin | `{account_id}` (404 `WALLET_ACCOUNT_NOT_FOUND`, 409 `WALLET_ACCOUNT_INACTIVE`, 422 `WALLET_ACCOUNT_NO_EXCHANGE` / `WALLET_ACCOUNT_NO_CREDENTIALS`) |
| POST | `/api/wallet/sync` | super admin | Lee el saldo ahora (404 `WALLET_NOT_CONFIGURED`; 422 configuración; 502 `WALLET_EXCHANGE_AUTH_FAILED` / `WALLET_SYNC_FAILED`; 503 `WALLET_EXCHANGE_UNAVAILABLE`) |
| GET | `/api/wallet/snapshots` | staff | `limit` 1–500, de la más reciente a la más antigua |

Routers registrados en `app/app_factory.py` (dentro de `api_routers`, con `prefix=settings.API_PREFIX`):
```python
from app.modules.accounts.rest import accounts_router, balances_router, wallet_router
```

Settings: `WALLET_BASE_ASSET` (USDT), `WALLET_SYNC_INTERVAL_SECONDS` (300, mínimo 60). Scheduler: `sync_platform_wallet()` en `scheduler_service.py`, llamado por `scheduler_runner.py` antes del ciclo de ejecución.

### Frontend (`frontend/src/modules/accounts/`)
| Ruta | Archivo de ruta | Página / componentes |
|-----|----------|----|
| `/#/portfolio` | `routes/_app/portfolio.lazy.tsx` | `pages/portfolio.tsx` (`PortfolioPage`) + `components/account-form-dialog.tsx` + `components/account-balances-sheet.tsx` + `components/record-balance-dialog.tsx` |
| `/#/admin/accounts` | `routes/_app/admin/accounts.lazy.tsx` | `pages/admin-accounts.tsx` + `components/account-balances-sheet.tsx` |
| `/#/admin/wallet` | `routes/_app/admin/wallet.lazy.tsx` | `pages/admin-wallet.tsx` + `components/wallet-account-dialog.tsx`; `api/wallet.api.ts`, `hooks/use-wallet-queries.ts` (relee cada 60 s), `hooks/use-wallet-mutations.ts`, `WALLET_SOURCE_LABELS` |

- API: `api/accounts.api.ts`; hooks `use-accounts-queries.ts` (`useAccountsQuery`, reutilizado por dashboard, agent, bots y billing) y `use-accounts-mutations.ts`; etiquetas `lib/accounts-labels.ts`; badges `components/account-badges.tsx`.

### Seed
- `database/seeds/accounts.py` — cuentas paper de ejemplo (Binance y Bybit) con balances en USDT para **cada** usuario demo (Andrés y Dayron), idempotente por (usuario, nombre). El usuario que no exista se omite.
- `account_balances` es una serie temporal (UNIQUE incluye `ts`): el balance inicial solo se inserta si el activo no tiene ninguna foto. Con `get_or_create` el seed fallaba (`MultipleResultsFound`) en cuanto alguien registraba un segundo balance.

## Gotchas críticos

- **`CREDENTIALS_SECRET_KEY` es obligatoria** fuera de `development`/`testing` (settings falla al arrancar sin ella). Perderla deja las `enc_creds` ilegibles; para **cambiarla**, poner la nueva en `CREDENTIALS_SECRET_KEY` y la vieja en `CREDENTIALS_PREVIOUS_KEYS` hasta re-cifrar las cuentas (si se quita la vieja antes, las cuentas cifradas con ella dejan de descifrarse).
- Las cuentas `live` guardan credenciales reales: nunca registrarlas en logs ni devolverlas en las respuestas.
- Los balances son inmutables: para "corregir" uno se registra un snapshot nuevo.
- **Billetera sin migración:** sin `e500b821b8ec` las rutas `/api/wallet` fallan (tablas inexistentes) y el paso del scheduler deja un error por ciclo en el log.
- **Saldo de Binance incompleto:** la API key necesita permiso de lectura de la wallet Funding; si falta, la sincronización sigue con Spot y deja un aviso en el log (`[Wallet] No se pudo leer el saldo 'funding'…`), y el total sale menor que el real.
- **Comisiones en BNB:** si la billetera paga comisiones con BNB, ese saldo baja con cada operación; se valora como cualquier activo (precio `BNB/USDT`).

## Tests

- `tests/accounts/` — 36 tests unitarios: `test_list_accounts_service.py`, `test_get_account_service.py`, `test_create_account_service.py`, `test_update_account_service.py`, `test_list_balances_service.py`, `test_record_balance_service.py`.
- **Huecos:** rutas REST, `CredentialsCipher` (cifrado/descifrado y clave inválida) y la billetera (`SyncWalletService`, `CcxtWalletGateway`, `value_wallet`): verificadas a mano con dobles de prueba, sin archivo de test.

## Riesgos

- Fuga o pérdida de `CREDENTIALS_SECRET_KEY`: compromete o inutiliza todas las credenciales.
- Balances manuales que no coinciden con el exchange pueden llevar a [M6](M06-AI-AGENT.md) a dimensionar mal las posiciones.

## Historial

- **2026-03** — Módulo completado (CRUD cuentas, balances, cifrado Fernet, UI `/portfolio` y `/admin/accounts`, 36 tests).
- **Posterior** — Es la base de las cuentas administradas de [M10](M10-BILLING.md).
- **2026-10-08** — API headless (/api), páginas migradas a React (frontend/).
- **2026-10-10** — Seed `accounts`: cuentas para Dayron y fix del re-run con varias fotos de balance.
- **2026-10-19** — Auditoría de seguridad: `api_key` ≤ 512 y `api_secret` ≤ 1024 en los schemas; `CredentialsCipher.from_settings()` con MultiFernet y `CREDENTIALS_PREVIOUS_KEYS` (rotación de clave sin perder las cuentas). Spec corregida: `portfolio_snapshots` sí tiene modelo ORM (`portfolio_snapshot_model.py`, registrado), aunque nadie la escribe.
- **2026-10-20** — Todas las cuentas: columna **Dueño** (nombre y correo) y filtro por dueño (antes "Usuario #id").
- **2026-10-23** — **Billetera única de la plataforma (fondo común, F2):** `platform_wallet` + `wallet_snapshots` (migración `e500b821b8ec`), `WalletGateway`/`CcxtWalletGateway` (Spot + Funding, precios por ticker), `SyncWalletService` (live graba `account_balances`; paper usa los manuales), paso del scheduler cada `WALLET_SYNC_INTERVAL_SECONDS`, `/api/wallet` (staff; elegir y sincronizar solo super admin), página Administración → Fondo → Billetera. `exchange_client.py` compartido con el `LiveExecutor`.
