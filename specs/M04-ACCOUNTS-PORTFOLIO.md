# Módulo 4 — Accounts & Portfolio (Cuentas y Portafolio) ✅ COMPLETO

← [Índice de módulos](_ROOT.md)

## Ficha

| Campo | Valor |
|---|---|
| Estado | ✅ Completo |
| Avance (alcance original) | 100 % — 8/8 entregables (+ 2026-10-23: billetera única de la plataforma; 2026-10-26: billetera solo de Binance con credenciales en el `.env`, sin "Mis cuentas") |
| Madurez (estimada) | 80 % — ver [Avance](#avance) |
| Tablas | `accounts`, `account_balances`, `platform_wallet`, `wallet_snapshots` (R/W); `exchanges` (R) |
| Depende de | [M1](M01-AUTH.md), [M2](M02-MARKET-DATA.md) (exchange de la cuenta) |
| Lo usan | [M6](M06-AI-AGENT.md) (capital disponible), [M7](M07-BOTS-SIGNALS.md) (billetera de los agentes reales y cuenta de práctica interna de los demo), [M8](M08-ORDERS-EXECUTION.md) (cliente del `LiveExecutor`), [M11](M11-FUND.md) (billetera única del fondo común) |
| Prefijo API | `/api/wallet` (desde el 2026-10-26 ya no existe `/api/accounts`) |
| Frontend | `frontend/src/modules/accounts` |
| Última revisión | 2026-10-26 |

## Descripción

**En palabras simples:** Es la billetera. Guarda información sobre tu dinero: cuánto tienes en Binance y cómo ha evolucionado tu capital en el tiempo.

**Qué hace:**
- **Una sola billetera: la de Binance (2026-10-26).** Nadie crea cuentas ni elige billetera: la app arma sola la cuenta "Billetera Binance" la primera vez que alguien la necesita. Sus credenciales (`BINANCE_API_KEY` / `BINANCE_API_SECRET`) viven en el `.env` del servidor, nunca en la BD.
- Su saldo se lee solo del exchange cada pocos minutos (Spot + Funding + Futuros USDⓈ-M), se valora en USDT y queda como foto (`wallet_snapshots`): total, libre y en órdenes, con el desglose por activo. Solo la ven super admin y socio.
- Guarda los **balances** como snapshots inmutables (`account_balances`): los de la billetera (leídos del exchange) y el monto inicial de cada **agente demo**.
- `accounts` queda como detalle interno: la fila de la billetera de Binance y una cuenta de práctica por agente demo ([M7](M07-BOTS-SIGNALS.md)). Ninguna se ve ni se maneja desde la app.

## Páginas

Hash routing: la URL real es `/#/<ruta>`.

**Páginas — Usuario:** ninguna. "Mis cuentas" (`/#/portfolio`) se retiró el 2026-10-26; la URL redirige a `/#/dashboard`.

**Páginas — Administración (super admin y socio):**
- `/#/admin/wallet` — "Billetera de Binance" (Administración → Fondo): nombre de la billetera, tarjetas Saldo total / Saldo libre / En órdenes / Última lectura, aviso si la última sincronización falló (con el motivo) o si hay activos sin precio, tabla de activos (libre, en órdenes, total, precio, valor) e historial de lecturas. Si faltan las credenciales en el `.env`, una tarjeta lo explica. Solo el super admin ve **Sincronizar ahora**. No hay botón para elegir billetera: es siempre la de Binance.

## Entregables

Tablas: `accounts`, `account_balances` (`portfolio_snapshots` es por bot: tiene modelo ORM aquí, pero ningún servicio la escribe)

Entregables:
- ✅ CRUD cuentas (exchange + API key/secret cifrada con Fernet → `meta['enc_creds']`)
- ✅ Registro de balances por moneda (USDT, BTC, etc.) — snapshots inmutables
- ✅ Equity curve vía time series de `account_balances`
- 🗄️ Endpoints `/api/accounts` (CRUD) y `/api/accounts/{id}/balances` — retirados el 2026-10-26 junto con sus servicios y sus 36 tests
- 🗄️ Cifrado de credenciales de cuentas (`meta['enc_creds']`) — retirado el 2026-10-26: las credenciales van en el `.env`. `CredentialsCipher` sigue en uso para los medios de pago del fondo ([M11](M11-FUND.md))
- 🗄️ Web UI `/#/portfolio` ("Mis cuentas") — retirada el 2026-10-26 (redirige al inicio)
- ✅ (2026-10-23) **Billetera única de la plataforma:** tablas `platform_wallet` (una fila) y `wallet_snapshots` (migración `e500b821b8ec`), `WalletGateway` + `CcxtWalletGateway`, `SyncWalletService`, paso del scheduler `sync_platform_wallet`, `GET /api/wallet`, `POST /api/wallet/sync`, `GET /api/wallet/snapshots` y página Billetera
- ✅ (2026-10-26) **Billetera solo de Binance:** `EnsurePlatformWalletService` la crea sola (cuenta live "Billetera Binance" a nombre del primer super admin activo + fila `platform_wallet`); credenciales `BINANCE_API_KEY` / `BINANCE_API_SECRET` en settings; fuera `PUT /api/wallet` y la rama paper de la sincronización

## Decisiones de diseño

| Decisión | Motivo | Alternativa descartada |
|---|---|---|
| API key/secret cifradas con **Fernet** (`CredentialsCipher`, clave `CREDENTIALS_SECRET_KEY`) y guardadas en `meta['enc_creds']` | Nunca se persisten credenciales en claro; la clave vive fuera de la BD | Guardar en claro / en una tabla aparte sin cifrar |
| `CredentialsCipher.from_settings()` arma un **MultiFernet**: cifra con `CREDENTIALS_SECRET_KEY` y descifra con ella o con cualquiera de `CREDENTIALS_PREVIOUS_KEYS` (lista separada por comas); `rotate(token)` re-cifra con la clave actual | Permite rotar la clave sin dejar ilegibles las cuentas existentes | Una sola clave Fernet (cambiarla rompía todas las `enc_creds`) |
| `api_key` ≤ 512 y `api_secret` ≤ 1024 caracteres en los schemas de crear/editar | Acota la entrada antes de cifrar y guardar en el JSON `meta` | Sin límite |
| Balances como **snapshots inmutables** (`UNIQUE (account_id, asset, ts)`) | La equity curve se obtiene como serie temporal sin recalcular ni mutar histórico | Un saldo único actualizable por activo |
| Cuenta `paper` o `live` (`accounts.mode`) y `status` `active`/`suspended` | Mismo modelo para simulación y dinero real; el modo del bot decide el *executor* en [M8](M08-ORDERS-EXECUTION.md) | Tablas separadas por modo |
| Propiedad: un usuario solo ve/edita sus cuentas; el admin ve todas (`belongs_to` + `is_admin`) | Aislamiento entre usuarios | Filtrar solo en la UI |
| La cuenta valida el modo (`ACCOUNT_INVALID_MODE`) al crear | Errores claros con códigos estables | Dejar que fallen los `CHECK` de MySQL |
| **Toda cuenta queda en Binance** (2026-10-26): `exchange_id` ya no se envía; `CreateAccountService` lo resuelve con `PLATFORM_EXCHANGE_NAME` (409 `PLATFORM_EXCHANGE_MISSING` si falta la fila) y no se puede cambiar. También las de práctica, que usan precios de Binance | La plataforma opera con un solo exchange ([M2](M02-MARKET-DATA.md)) | Selector de exchange (con cuentas en otros exchanges que nunca podrían operar) |
| **Una sola billetera** para toda la plataforma: tabla `platform_wallet` con una fila (CHECK `id = 1`) que apunta a una cuenta de `accounts` | Fondo común: el dinero de propietarios, socios e inversores está en una sola cuenta; reutilizar `accounts` conserva el `LiveExecutor`, los balances y la propiedad de los agentes | Columna `is_platform_wallet` en `accounts` (difícil de garantizar una sola) · tabla de billeteras por usuario |
| **La billetera no se elige** (2026-10-26): `EnsurePlatformWalletService` la crea sola si falta (página Billetera, scheduler, fondo, crear un agente real); si apuntaba a una cuenta paper de desarrollo, crea la live y re-apunta | El negocio opera solo con la billetera de Binance: elegir no tenía sentido y confundía | Botón "Elegir billetera" + diálogo (retirado) |
| **Credenciales en el `.env`** (`BINANCE_API_KEY` / `BINANCE_API_SECRET`), nunca en la BD (2026-10-26) | Hay una sola billetera y la configura quien administra el servidor; nadie las ve ni las cambia desde la app | Formulario en la página Billetera con la API key cifrada en la BD |
| **`accounts` como detalle interno** (2026-10-26): la fila de la billetera y una cuenta de práctica por agente demo | La propiedad de los agentes, el RiskGate y el 1 % ya iban por `accounts`; sin cambio de esquema | `bots.user_id` + capital en el bot (tocaba unas 25 piezas y sus tests) |
| **Saldo leído del exchange** cada `WALLET_SYNC_INTERVAL_SECONDS` (300 s) sumando los tipos de cuenta del exchange (`_EXTRA_BALANCE_TYPES`: Funding y Futuros en Binance); en live también se graba en `account_balances` con la misma hora para todos los activos | El P2P y los depósitos de Binance caen en Funding: sin sumarlo la conciliación del fondo daría diferencias. Grabar `account_balances` mantiene el 1 % de los agentes con el saldo real | Solo `fetch_balance()` (spot) · balances manuales |
| Un activo que tenía saldo y ya no aparece se graba en 0; la moneda base se graba siempre | Si no, su último balance quedaría viejo y el agente seguiría viendo dinero que ya no está | Grabar todos los activos en 0 del exchange (cientos en Binance) |
| **Precios por ticker público** (`fetch_tickers` de `ACTIVO/USDT`); un activo sin precio no suma y se avisa (`missing_prices`). Un fallo de precios no tumba la sincronización | Sin API key y siempre al día; el total nunca incluye un valor inventado | Velas de M2 (solo existen para los símbolos con agentes) |
| La billetera es **siempre live** (desde el 2026-10-26; antes se aceptaba una cuenta paper de desarrollo) | Para probar sin dinero real está la testnet (`LIVE_USE_SANDBOX=true` con claves de testnet) | Cuenta paper como billetera |
| **API key de solo lectura** recomendada (sin permiso de retiro) | Los retiros los hacen los propietarios en el exchange; una API key filtrada no puede sacar dinero | Retiros automáticos por API |
| `exchange_client.py` (helper compartido) arma el cliente ccxt con las credenciales del `.env`; lo usan el `LiveExecutor` y la billetera, y lanza `ExchangeClientError(code)` (subclase de `RuntimeError`; `EXCHANGE_CREDENTIALS_MISSING` si faltan) | Un solo sitio para leer credenciales y respetar `LIVE_USE_SANDBOX`; el `LiveExecutor` conserva sus mensajes | Copiar la lógica en la billetera |
| `portfolio_snapshots` diferida: el modelo ORM existe (`infrastructure/portfolio_snapshot_model.py`, registrado en `models_registry.py` para que Alembic gestione el esquema completo), pero no hay entidad, repositorio ni servicio que la escriba | La tabla es por bot (`bot_id`, [M7](M07-BOTS-SIGNALS.md)), no por cuenta | Snapshots por cuenta |

## Avance

| Métrica | Valor | Evidencia |
|---|---|---|
| Alcance original | **100 %** (8/8) | Entregables hechos; desde el 2026-10-26 el CRUD de cuentas y "Mis cuentas" se retiraron a propósito (una sola billetera) |
| Madurez | **≈ 80 %** | Funcionalidad 92 · Tests 55 · Seguridad 92 · Operación 80 |

- **Funcionalidad (92):** la billetera de Binance se arma y se sincroniza sola; no queda nada que registrar a mano.
- **Tests (55):** los 36 tests de cuentas y balances se fueron con sus servicios; la billetera (`EnsurePlatformWalletService`, `SyncWalletService`, `CcxtWalletGateway`) sigue sin archivo de test.
- **Seguridad (92):** credenciales solo en el `.env` (nunca en la BD ni en respuestas); sin endpoints de escritura salvo "Sincronizar ahora".
- **Operación (80):** sincronización automática con el estado del último intento visible en la UI; aviso claro si faltan las credenciales.

## Posibles mejoras

| Prioridad | Mejora | Esfuerzo |
|---|---|---|
| Media | Tests de `EnsurePlatformWalletService`, `SyncWalletService` y `CcxtWalletGateway` | S |
| Alta | Al arrancar, comprobar que la API key del `.env` no tenga permiso de retiro (Binance lo informa en `apiRestrictions`) y avisar en la página Billetera | S |
| Media | Usar `portfolio_snapshots` (tabla y modelo ORM creados; falta entidad, repositorio y un servicio que la escriba) para equity por bot | M |

## Fuera de alcance y pendientes conocidos

- Otros exchanges o varias billeteras: decisión de negocio (solo Binance).
- `portfolio_snapshots`: la tabla y su modelo ORM (`PortfolioSnapshotModel`) existen, pero ningún servicio la escribe ni la lee.
- Multi-moneda con conversión a una divisa base.
- Retiros/depósitos: el sistema no mueve fondos entre cuentas.

## Detalle técnico

> Generado desde el código el 2026-10-07: el antiguo `MODULES_MAP.md` no tenía sección para M4.

### Tablas en BD
| Tabla | Acción | Nota |
|-------|--------|------|
| `accounts` | WRITE | Interna: la billetera (`mode` live, `meta.platform_wallet`) y una cuenta paper por agente demo (`meta.demo_capital`, la crea [M7](M07-BOTS-SIGNALS.md)). `meta.enc_creds` ya no se usa |
| `account_balances` | WRITE | Snapshots por `asset` con `free`/`locked`; UNIQUE `(account_id, asset, ts)`, CASCADE al borrar la cuenta. Los escriben la sincronización de la billetera y la creación de un agente demo (monto inicial) |
| `platform_wallet` | WRITE | Una sola fila (CHECK `id = 1`): `account_id` (UNIQUE, FK `accounts`), `base_asset` (USDT), `last_synced_at`, `last_sync_error` (código del último fallo), `updated_by_user_id` |
| `wallet_snapshots` | WRITE | Fotos del saldo: `total_value` / `free_value` / `locked_value` (DECIMAL 30,12, en `base_asset`), `source` (`exchange` \| `manual`), `assets` JSON (`[{asset, free, locked, price, value}]`, decimales como texto), `missing_prices` JSON, `ts`; índice `(account_id, ts)` |
| `exchanges` | READ | Resuelve el id de Binance al crear la cuenta de la billetera |

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
| `wallet/` | `ensure_platform_wallet_service.py` (`EnsurePlatformWalletService.ensure()` → cuenta de la billetera o `None` si falta Binance o un super admin; `PLATFORM_WALLET_ACCOUNT_NAME`), `get_wallet_service.py` (`GetWalletService.get()` → `WalletOverview` con `credentials_configured`, `list_snapshots`), `sync_wallet_service.py` |

Provider: `app/modules/accounts/providers/account_provider.py` → `AccountServiceFactory` (`ensure_platform_wallet`, `get_wallet`, `sync_wallet`) + `get_account_factory(session)` + `build_platform_wallet_ensurer(session)` (lo usan bots, fondo y seeds). El dueño de la cuenta de la billetera se resuelve con el primer super admin activo (`SqlAlchemyUserRepository`, import diferido).

Credenciales: `exchange_client.platform_credentials_configured()` y `build_authenticated_client(account, exchange_repo)` leen `settings.BINANCE_API_KEY` / `BINANCE_API_SECRET`.

### Endpoints REST
| Método | Ruta | Auth | Nota |
|--------|------|------|------|
| GET | `/api/wallet` | staff | Asegura la billetera y devuelve `{configured, wallet, account, latest_snapshot}`; `configured` = hay credenciales en el `.env` y billetera; `wallet.last_sync_error_msg` ya en español |
| POST | `/api/wallet/sync` | super admin | Lee el saldo ahora (404 `WALLET_NOT_CONFIGURED` si faltan las credenciales; 422 configuración; 502 `WALLET_EXCHANGE_AUTH_FAILED` / `WALLET_SYNC_FAILED`; 503 `WALLET_EXCHANGE_UNAVAILABLE`) |
| GET | `/api/wallet/snapshots` | staff | `limit` 1–500, de la más reciente a la más antigua |

Routers registrados en `app/app_factory.py` (dentro de `api_routers`, con `prefix=settings.API_PREFIX`):
```python
from app.modules.accounts.rest import wallet_router
```

Settings: `BINANCE_API_KEY` / `BINANCE_API_SECRET` (vacías = billetera sin conectar), `WALLET_BASE_ASSET` (USDT), `WALLET_SYNC_INTERVAL_SECONDS` (300, mínimo 60), `LIVE_USE_SANDBOX` (testnet). Scheduler: `sync_platform_wallet()` en `scheduler_service.py`, llamado por `scheduler_runner.py` antes del ciclo de ejecución.

### Frontend (`frontend/src/modules/accounts/`)
| Ruta | Archivo de ruta | Página / componentes |
|-----|----------|----|
| `/#/portfolio` | `routes/_app/portfolio.tsx` | Solo redirige a `/#/dashboard` (Mis cuentas se retiró el 2026-10-26) |
| `/#/admin/wallet` | `routes/_app/admin/wallet.lazy.tsx` | `pages/admin-wallet.tsx`; `api/wallet.api.ts` (`getWallet`, `syncWallet`, `listWalletSnapshots`), `hooks/use-wallet-queries.ts` (relee cada 60 s), `hooks/use-wallet-mutations.ts` (`useSyncWalletMutation`), `lib/accounts-labels.ts` (`WALLET_SOURCE_LABELS`) |

### Seed
- `database/seeds/accounts.py` — asegura la billetera de Binance con `build_platform_wallet_ensurer` (necesita `market_data` y un super admin activo). Ya no siembra cuentas paper por usuario: cada agente demo trae la suya (seed `bots`).

## Gotchas críticos

- **Sin `BINANCE_API_KEY` / `BINANCE_API_SECRET`** la página Billetera muestra "aún no está conectada", el scheduler omite la sincronización (log en debug) y toda orden de un agente real falla con `EXCHANGE_CREDENTIALS_MISSING`. Tras ponerlas hay que reiniciar la API.
- **Sin super admin activo o sin la fila Binance en `exchanges`**, `EnsurePlatformWalletService` no puede crear la billetera (devuelve `None`): crear un agente real responde `BOT_WALLET_UNAVAILABLE` (409).
- **Datos anteriores al 2026-10-26:** las cuentas creadas en "Mis cuentas" quedan en la BD sin uso (y sus `enc_creds`, sin leer). Lo recomendado es limpiar la BD y correr los seeds.
- Los balances son inmutables: para "corregir" uno se registra un snapshot nuevo.
- **Billetera sin migración:** sin `e500b821b8ec` las rutas `/api/wallet` fallan (tablas inexistentes) y el paso del scheduler deja un error por ciclo en el log.
- **Saldo de Binance incompleto:** la API key necesita permiso de lectura de la wallet Funding; si falta, la sincronización sigue con Spot y deja un aviso en el log (`[Wallet] No se pudo leer el saldo 'funding'…`), y el total sale menor que el real.
- **Comisiones en BNB:** si la billetera paga comisiones con BNB, ese saldo baja con cada operación; se valora como cualquier activo (precio `BNB/USDT`).

## Tests

- `tests/accounts/` quedó vacío: los 36 tests de cuentas y balances se borraron con sus servicios (2026-10-26).
- **Huecos:** rutas REST y la billetera (`EnsurePlatformWalletService`, `SyncWalletService`, `CcxtWalletGateway`, `value_wallet`): sin archivo de test.

## Riesgos

- Fuga del `.env` del servidor: expone la API key de la billetera. Mitigación: API key sin permiso de retiro y con lista blanca de IP.

## Historial

- **2026-03** — Módulo completado (CRUD cuentas, balances, cifrado Fernet, UI `/portfolio` y `/admin/accounts`, 36 tests).
- **Posterior** — Fue la base de las cuentas administradas de M10 (retirado); hoy su billetera única la usa [M11](M11-FUND.md).
- **2026-10-08** — API headless (/api), páginas migradas a React (frontend/).
- **2026-10-10** — Seed `accounts`: cuentas para Dayron y fix del re-run con varias fotos de balance.
- **2026-10-19** — Auditoría de seguridad: `api_key` ≤ 512 y `api_secret` ≤ 1024 en los schemas; `CredentialsCipher.from_settings()` con MultiFernet y `CREDENTIALS_PREVIOUS_KEYS` (rotación de clave sin perder las cuentas). Spec corregida: `portfolio_snapshots` sí tiene modelo ORM (`portfolio_snapshot_model.py`, registrado), aunque nadie la escribe.
- **2026-10-20** — Todas las cuentas: columna **Dueño** (nombre y correo) y filtro por dueño (antes "Usuario #id").
- **2026-10-23** — **Billetera única de la plataforma (fondo común, F2):** `platform_wallet` + `wallet_snapshots` (migración `e500b821b8ec`), `WalletGateway`/`CcxtWalletGateway` (Spot + Funding, precios por ticker), `SyncWalletService` (live graba `account_balances`; paper usa los manuales), paso del scheduler cada `WALLET_SYNC_INTERVAL_SECONDS`, `/api/wallet` (staff; elegir y sincronizar solo super admin), página Administración → Fondo → Billetera. `exchange_client.py` compartido con el `LiveExecutor`.
- **2026-10-23** — Se retira el grupo **Supervisión** del menú: fuera la página "Todas las cuentas" (`/#/admin/accounts`, `pages/admin-accounts.tsx`). `GET /api/accounts` sigue igual.
- **2026-10-26** — **Solo Binance:** las cuentas ya no eligen exchange (sin `exchange_id` en crear/editar, sin selector ni columna Exchange en Mis cuentas); se crean siempre en Binance. La migración `9869015f140f` pasa las existentes a Binance. La billetera suma solo Funding de Binance.
- **2026-10-26** — La billetera suma también la billetera de **Futuros USDⓈ-M** (`future`): ahí está el margen de los perpetuos en live ([M8](M08-ORDERS-EXECUTION.md)); el total y la conciliación del fondo lo incluyen (a mercado: el saldo de Futuros incluye lo no realizado).
- **2026-10-26** — **Una sola billetera, la de Binance:** credenciales en el `.env` (`BINANCE_API_KEY` / `BINANCE_API_SECRET`), la billetera se arma sola (`EnsurePlatformWalletService`), fuera `PUT /api/wallet` y el botón "Elegir billetera". Se retiran "Mis cuentas" (`/#/portfolio` redirige al inicio), `/api/accounts`, los balances manuales y sus 36 tests. `accounts` queda interna: billetera + cuenta de práctica de cada agente demo ([M7](M07-BOTS-SIGNALS.md)).
