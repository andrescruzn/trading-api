# Módulo 8 — Orders & Execution (Órdenes y Ejecución) ✅ COMPLETO

← [Índice de módulos](_ROOT.md)

## Ficha

| Campo | Valor |
|---|---|
| Estado | ✅ Completo (sin tests) |
| Avance (alcance original) | 100 % — 10/10 entregables del plan original (+ 7 nuevos de 2026-10-19) |
| Madurez (estimada) | 60 % — ver [Avance](#avance) |
| Tablas | `orders`, `fills`, `positions` (R/W); `signals` (R/W: decisión de ejecución); `bots` (R, y `status` → `error` por drawdown); `candles`, `symbols`, `exchanges`, `accounts`, `account_balances` (R) |
| Depende de | [M2](M02-MARKET-DATA.md), [M4](M04-ACCOUNTS-PORTFOLIO.md) (credenciales Fernet, saldo para el drawdown), [M7](M07-BOTS-SIGNALS.md) (bots, señales, propiedad) |
| Lo usan | [M9](M09-ALERTS.md) (hook de orden; Telegram aprueba/rechaza vía `ExecuteSignalService`), [M10](M10-BILLING.md) (historial de órdenes y fills), scheduler de [M2](M02-MARKET-DATA.md) (ejecución automática y SL/TP) |
| Prefijo API | `/api/orders`, `/api/fills`, `/api/positions`, `/api/signals/{id}/approve`, `/api/signals/{id}/reject` |
| Frontend | `frontend/src/modules/orders` (aprobar/descartar vive en `frontend/src/modules/bots`) |
| Última revisión | 2026-10-19 |

## Descripción

**En palabras simples:** Es quien aprieta el botón de comprar/vender. Cuando un agente tiene una señal aprobada, este módulo envía la orden al exchange (o la simula en paper), y después vigila la posición para cerrarla en su stop loss o su take profit.

**Qué hace:**
- Crea **órdenes** para un agente: market (precio actual), limit (precio fijo), stop y stop-limit. Solo para agentes del usuario (el admin puede todos).
- Antes de enviar, pasa toda orden por el **RiskGate**: kill switch global, live apagado por defecto, valor máximo por compra y pérdida máxima del agente.
- **Guarda la orden antes de llamar al exchange** (con un `client_order_id` propio) y luego registra lo que el exchange respondió de verdad: ejecutada, ejecutada en parte, enviada sin ejecutar, rechazada o "sin respuesta" (para revisar).
- Ejecuta según el modo del agente:
  - **Paper:** simula la ejecución total con el cierre de la última vela (fee = 0).
  - **Live:** envía la orden real con ccxt y registra precio, cantidad y comisión reales.
- **Convierte señales en órdenes** (`ExecuteSignalService`): cuando la persona aprueba una señal pendiente (app o Telegram) o cuando el agente está en modo Automático. Revalida al precio actual (R/R ≥ 2:1) y recalcula la cantidad para mantener el mismo riesgo en dinero.
- **Protege posiciones** (`ProtectPositionsService`): una posición abierta desde una señal guarda su stop loss y take profit; el scheduler la cierra a mercado cuando una vela los toca.
- Registra las **ejecuciones** (fills) y gestiona las **posiciones**: precio medio ponderado (WAP) en cada compra y P&L realizado en cada venta. En spot no hay cortos: no se vende más de lo que hay.
- Máquina de estados de la orden: `new → sent → filled / partially_filled / canceled / rejected`.

**Importante:** Las cuentas "paper" simulan las órdenes sin tocar dinero real. Las cuentas "live" operan con dinero real y, por defecto, están **desactivadas en el servidor** (`TRADING_LIVE_ENABLED=false`).

## Páginas

Hash routing: la URL real es `/#/<ruta>`.

**Páginas — Usuario (cualquier usuario autenticado):**
- `/#/orders` — Libro de órdenes: selector de agente (agentes de tus cuentas, por nombre), pestañas Órdenes / Posiciones / Ejecuciones, diálogo para crear nueva orden. Las posiciones con protección muestran "Protección automática: SL … · TP …".
- Aprobar / descartar una señal pendiente: en el detalle de la señal del agente y en la tarjeta "Señales por aprobar" del dashboard ([M7](M07-BOTS-SIGNALS.md)); llaman a `POST /api/signals/{id}/approve|reject` de este módulo.

**Páginas — Administrador (solo admin):**
- `/#/admin/orders` — Vista global de todas las órdenes del sistema con filtros por lado, estado y tipo, y diálogo con los fills de cada orden

## Entregables

Tablas: `orders`, `fills`, `positions`

Entregables:
- ✅ Domain: Order entity (state machine), Fill entity, Position entity (WAP + P&L)
- ✅ Infrastructure: ORM models + repository impls para orders, fills, positions
- ✅ Execution (Strategy Pattern): PaperExecutor (simula con última vela) + LiveExecutor (ccxt real)
- ✅ Services: list_orders, get_order, create_order, list_fills, list_positions
- ✅ CreateOrderService: valida bot, selecciona executor según bot.mode, crea order+fill+position
- ✅ Provider: OrderServiceFactory con repos propios + borrowed de M7/M2/M4
- ✅ REST: `POST /api/orders`, `GET /api/orders`, `GET /api/orders/{id}`, `GET /api/fills`, `GET /api/positions`
- ✅ Web UI usuario: `/#/orders` con tabs Órdenes/Posiciones/Ejecuciones + diálogo crear orden (React desde 2026-10-08)
- ✅ Web UI admin: `/#/admin/orders` con filtros por lado/estado/tipo + diálogo de fills
- ✅ LiveExecutor: integración completa ccxt + Fernet credentials
- ✅ (2026-10-19) **Propiedad** en `POST/GET /api/orders`, `GET /api/orders/{id}`, `/api/fills` y `/api/positions` vía `find_accessible_bot`
- ✅ (2026-10-19) **RiskGateService**: kill switch, live apagado, notional máximo, drawdown máximo
- ✅ (2026-10-19) **Idempotencia y estado real**: `orders.client_order_id` (`ta-{id}`), orden confirmada antes de llamar al exchange, `ExecutionResult` con el estado reportado, rechazos guardados como `rejected`, `ORDER_EXECUTION_UNCERTAIN` + `meta.needs_reconciliation`
- ✅ (2026-10-19) **Señal vinculada validada** (mismo agente, aprobada, misma dirección, una sola orden activa) y regla spot sin cortos
- ✅ (2026-10-19) **ExecuteSignalService**: aprobar/rechazar señales pendientes con reclamo atómico y revalidación al precio actual
- ✅ (2026-10-19) **ProtectPositionsService**: SL/TP automáticos por ciclo del scheduler (`positions.stop_loss`, `take_profit`, `signal_id`)
- ✅ (2026-10-19) REST `POST /api/signals/{id}/approve` y `/reject` (router `signal_decisions`)

## Decisiones de diseño

| Decisión | Motivo | Alternativa descartada |
|---|---|---|
| **Strategy Pattern** para la ejecución: `ExecutorInterface` → `PaperExecutor` / `LiveExecutor` | Mismo flujo para simular y operar con dinero real; añadir un broker no toca el servicio | `if mode == ...` repartido por el código |
| El executor lo elige `bot.mode` (`paper` → `PaperExecutor`, `live` → `LiveExecutor`) en `CreateOrderService` | El modo vive en el bot; no se puede ejecutar *live* por error desde una cuenta paper | Parámetro `mode` en cada request |
| `PaperExecutor` rellena con el cierre de la última vela y `fee = 0`, siempre `filled` | Simulación simple y determinista, sin red | Simular *slippage* y comisiones |
| `LiveExecutor` descifra las credenciales con Fernet ([M4](M04-ACCOUNTS-PORTFOLIO.md)) y envía la orden con ccxt | Las claves nunca viajan ni se guardan en claro | Credenciales en variables de entorno |
| **Persistir antes de enviar:** la orden se crea (`new`), se le asigna `client_order_id = "ta-{id}"` y se hace `commit()` **antes** de llamar al exchange; después se actualiza con el resultado | Si la llamada se corta por red, la orden puede existir en el exchange: revertirla dejaría una orden viva que el sistema no conoce. Los rechazos quedan como historial auditable | Transacción única orden + fill con `rollback()` si falla el executor (esquema anterior a 2026-10-19) |
| `client_order_id` determinista (`Order.build_client_order_id`), UNIQUE en BD y enviado como `clientOrderId` | El exchange rechaza un segundo envío con el mismo ID y permite buscar la orden si se pierde la respuesta; ≤ 36 caracteres válidos en Binance/Bybit/OKX | UUID aleatorio (no se puede reconstruir) |
| El executor devuelve `ExecutionResult(status, exchange_order_id, fill \| None)` con el estado **que reporta el exchange** (`filled` / `partially_filled` / `sent`) | Una límite lejos del precio queda `sent` sin fill; no se asume ejecución total ni se inventa precio 0 | Devolver siempre un `Fill` (antes) |
| Dos tipos de error: `RuntimeError` → orden `rejected` (no existe en el exchange) · `ExecutionUncertainError` (timeout/red/error inesperado o ejecución sin precio) → queda `sent` con `meta.needs_reconciliation` | Distinguir "seguro que no se envió" de "no sabemos" evita reenviar una orden duplicada | Tratar todo fallo como rechazo |
| **RiskGate** como última barrera, para órdenes manuales, aprobadas o automáticas: `TRADING_ENABLED` → `TRADING_LIVE_ENABLED` → solo en compras: notional ≤ min(`ORDER_MAX_NOTIONAL`, `risk_params.max_notional`) y drawdown < `risk_params.max_drawdown_pct` | Las reglas del servidor no dependen del front ni de la IA | Validar solo en el front o en el agente |
| Las **ventas** no se bloquean por notional ni drawdown (sí por el kill switch y por live apagado) | Reducir o cerrar riesgo siempre debe poder hacerse | Mismo filtro para compras y ventas |
| Drawdown alcanzado → el agente pasa a `error` (`BOT_MAX_DRAWDOWN_REACHED`) | Frena al agente hasta que una persona lo revise | Solo rechazar la orden y seguir operando |
| Drawdown = pérdida realizada acumulada / (saldo libre en la moneda base + esa pérdida) | Aproxima el capital inicial sin snapshots | `portfolio_snapshots` (tiene modelo ORM, pero ningún servicio la escribe) |
| **Spot sin cortos:** `side=sell` solo hasta la cantidad de la posición (`ORDER_SELL_EXCEEDS_POSITION`); una señal SELL ejecutada cierra la posición abierta | El esquema (`chk_positions_qty`, `qty ≥ 0`) y los executors no manejan cortos | Representar cortos con `qty` negativa |
| **Una señal = una orden:** `signal_id` debe ser del mismo agente, aprobada, con la misma dirección y sin otra orden que no esté `rejected`/`canceled` | No ejecutar dos veces la misma decisión | Permitir varias órdenes por señal |
| Aprobar una señal = crear la orden, por eso `POST /signals/{id}/approve|reject` vive en `orders` (router `signal_decisions`) y no en `bots` | `orders` ya depende de `bots`; al revés habría ciclo | Endpoint en `bots` que importe `orders` |
| **Reclamo atómico** `pending → executing` con UPDATE condicional (`SignalRepository.transition_decision`) y `commit()` antes de crear la orden | Si la app y Telegram aprueban a la vez, solo uno gana; el otro recibe `SIGNAL_ALREADY_DECIDED` | Bloqueo de fila o comprobación en Python |
| **Revalidar al precio actual** al aprobar: precio sobre el SL, bajo el TP y R/R ≥ `AGENT_MIN_RR_RATIO` desde el cierre actual (`SIGNAL_PRICE_MOVED`); sin piramidar (`SIGNAL_POSITION_ALREADY_OPEN`) | Entre la señal y la aprobación puede pasar una hora: la operación tiene que seguir cumpliendo el 2:1 | Ejecutar con los niveles originales |
| Cantidad recalculada: `riesgo_en_dinero = position_size × \|entry − SL\|` de la señal; `qty = riesgo_en_dinero / (precio_actual − SL)` | Mantiene la regla del 1 % aunque el precio se haya movido | Usar `position_size` tal cual |
| SL/TP **por ciclo del scheduler**, no orden stop/OCO en el exchange | Funciona igual en paper y live y con cualquier exchange de ccxt | Órdenes nativas (mejora futura) |
| Si una vela toca SL y TP a la vez, **gana el SL** (`Position.protection_hit`) | Sin datos intravela no se sabe cuál llegó primero: se asume el peor caso | Asumir el TP |
| La protección actúa aunque el agente esté pausado o detenido (`require_running=False`); el kill switch sí la detiene | Proteger el capital no depende de que el agente siga buscando entradas | Exigir agente `running` |
| Al quedar flat, `apply_sell_fill` borra SL/TP/`signal_id` de la posición | Una posición nueva no hereda la protección de la anterior | Limpiarlo a mano |
| `meta.reason` en cada orden: `manual`, `signal`, `stop_loss`, `take_profit` | Historial legible de por qué salió cada orden | Inferirlo de `signal_id` |
| Mensaje de éxito según el estado real (`Orden ejecutada.` / `Orden ejecutada en parte…` / `Orden enviada…`) | La persona sabe si la orden quedó abierta | Un único "Orden ejecutada exitosamente." |
| `positions` único por `(bot_id, symbol_id)` y `qty >= 0` (CHECK) | Una posición abierta por agente y símbolo | Cantidades negativas |
| El símbolo para ccxt se guarda en `order.meta["symbol"]` | `LiveExecutor` no tiene que re-resolver el símbolo | Resolverlo en cada llamada |
| Máquina de estados de la orden en la entidad: `new → sent → filled / partially_filled / canceled / rejected` | Transiciones válidas centralizadas y testeables | Estado libre |
| Solo se crean órdenes para agentes `running` (salvo cierres por SL/TP) | Un agente parado o en error no abre operaciones | Permitirlo y avisar |
| Hook de alertas post-commit en `try/except` ([M9](M09-ALERTS.md)), **también para órdenes rechazadas** | Una alerta no aborta el flujo de trading; un rechazo es justo lo que conviene avisar | Alertas dentro de la transacción |

## Avance

| Métrica | Valor | Evidencia |
|---|---|---|
| Alcance original | **100 %** (10/10) | Dominio, infraestructura, executors paper/live, servicios, REST y UI usuario + admin. Además, 7 entregables nuevos (2026-10-19) |
| Madurez | **≈ 60 %** | Funcionalidad 85 · Tests 0 · Seguridad 90 · Operación 65 |

- **Funcionalidad (85):** señal → orden (aprobación o automático) y SL/TP automáticos por ciclo. Faltan: cancelar órdenes, sincronizar estado y fills de órdenes `sent`/`partially_filled` con el exchange (`fetch_order`), reconciliar las marcadas `needs_reconciliation`, SL/TP nativos en el exchange y un paper realista (comisión, *slippage*, fill en el nivel del SL/TP).
- **Tests (0):** **ningún test** cubre este módulo, que es donde se mueve el dinero (ni `RiskGateService`, ni `ExecuteSignalService`, ni `ProtectPositionsService`).
- **Seguridad (90):** propiedad en todas las rutas (404 para agentes ajenos), RiskGate en el servidor, live apagado por defecto, `client_order_id` UNIQUE, una orden por señal, reclamo atómico de la señal, precios con `max_digits=30, decimal_places=12` en el esquema.
- **Operación (65):** kill switch y límites configurables por entorno; la protección corre sola en el scheduler (proceso líder). Sin job de reconciliación, sin reintentos ni métricas.

## Posibles mejoras

| Prioridad | Mejora | Esfuerzo |
|---|---|---|
| Alta | **Tests** de `CreateOrderService` (paper y live con ccxt mockeado: `filled`/`sent`/rechazo/incierto), `RiskGateService`, `ExecuteSignalService` (carrera app/Telegram, precio movido, cantidad recalculada), `ProtectPositionsService`, `Position.apply_*_fill`/`protection_hit` y la máquina de estados de `Order` | M |
| Alta | **Job de reconciliación:** buscar en el exchange (`fetch_order` por `clientOrderId`) las órdenes con `meta.needs_reconciliation` y las `sent`/`partially_filled`, y registrar sus fills | M |
| Alta | Cancelar órdenes (`POST /api/orders/{id}/cancel`) para `limit`/`stop` abiertas | M |
| Alta | **SL/TP nativos** (orden stop/OCO en el exchange) para live: hoy un hueco de precio entre ciclos cierra más lejos del nivel, y si el proceso cae nadie vigila | L |
| Media | `PaperExecutor` realista: comisión y *slippage* configurables, y cierre por SL/TP al precio del nivel (hoy usa el cierre de la última vela) | S |
| Media | Saldo mínimo y límite diario de pérdidas/operaciones por agente en el RiskGate | S |
| Media | Soporte de posiciones cortas (`qty` negativa o campo `side`) para perpetuos | L |
| Baja | Cálculo de P&L no realizado de la posición abierta en `/api/positions` | S |

## Fuera de alcance y pendientes conocidos

- **Paper:** fill siempre total al cierre de la última vela (también los cierres por SL/TP), sin comisión ni *slippage*.
- **SL/TP:** se vigilan una vez por ciclo del scheduler (`SCHEDULER_INTERVAL_SECONDS`, 60 s), no son órdenes stop/OCO en el exchange.
- **Reconciliación:** las órdenes que quedan `sent` con `meta.needs_reconciliation` no tiene quién las revise todavía; hay que mirarlas en el exchange.
- Cancelación de órdenes.
- Posiciones cortas y apalancamiento / futuros. Por eso los perpetuos TradFi de [M2](M02-MARKET-DATA.md) (`XAU/USDT:USDT`) solo se operan en paper: `LiveExecutor` rechaza cualquier símbolo con `:` (ccxt leería `amount` como contratos).
- Tests (el roadmap original no los listaba).

## Detalle técnico

### Tablas en BD
| Tabla | Acción | Nota |
|-------|--------|------|
| `orders` | WRITE | Órdenes por bot (market/limit/stop/stop_limit). `client_order_id VARCHAR(64) NULL` + `uq_orders_client_order_id` (NULL en las anteriores a m08). `meta`: `symbol`, `mode`, `reason`, y si aplica `error`, `needs_reconciliation` |
| `fills` | WRITE | Ejecuciones de órdenes (CASCADE delete) |
| `positions` | WRITE | Posición por bot+symbol (UNIQUE `uq_positions_bot_symbol`). `stop_loss`, `take_profit` `DECIMAL(30,12) NULL` y `signal_id BIGINT NULL` (FK `fk_positions_signal` → `signals`): protección que vigila el scheduler |
| `signals` | WRITE | `ExecuteSignalService` cambia `decision_status` y los campos de decisión (columnas de [M7](M07-BOTS-SIGNALS.md)) |
| `bots` | READ / WRITE | Validar propiedad y estado; el RiskGate lo pasa a `error` por drawdown |
| `candles` | READ | Precio de referencia, PaperExecutor, revalidación de la señal y SL/TP |
| `symbols` | READ | Para resolver símbolo del bot |
| `exchanges` | READ | Para resolver exchange en LiveExecutor |
| `accounts` | READ | Propiedad y credenciales cifradas en LiveExecutor |
| `account_balances` | READ | Saldo libre para el drawdown del RiskGate |

### Migraciones
- `218d50385270` — `m08 orders client_order_id and otp failed attempts`: `orders.client_order_id` + UNIQUE (y `users.otp_failed_attempts` de [M1](M01-AUTH.md)). Escrita a mano (`AFTER exchange_order_id`).
- `f51e2dad9c13` — `m07 execution mode and signal decisions`: entre otras, `positions.stop_loss`, `take_profit`, `signal_id` + FK. Ver [M7](M07-BOTS-SIGNALS.md#migraciones).

### Modelos ORM (`app/modules/orders/infrastructure/`)
| Archivo | Clase | Tabla |
|---------|-------|-------|
| `order_model.py` | `OrderModel` | `orders` |
| `fill_model.py` | `FillModel` | `fills` |
| `position_model.py` | `PositionModel` | `positions` |

Registrados en: `app/extensions/db/models_registry.py`

Repos: `OrderRepository.has_active_order_for_signal(signal_id)` (orden que no está `rejected`/`canceled`) · `PositionRepository.list_protected()` (`qty > 0` y SL o TP no nulos).

### Dominio
- `Order.build_client_order_id(order_id)` → `"ta-{id}"`.
- `Position.set_protection(sl, tp, signal_id)`, `clear_protection()`, `protection_hit(low, high)` → `"stop_loss"` / `"take_profit"` / `None` (solo largos; SL gana si se tocan los dos).

### Execution layer (`app/modules/orders/execution/`)
| Archivo | Clase | Qué hace |
|---------|-------|---------|
| `executor_interface.py` | `ExecutorInterface` (ABC), `ExecutionResult`, `ExecutionUncertainError` | `execute(order, bot) -> ExecutionResult(status, exchange_order_id, fill \| None)`. `RuntimeError` = rechazada; `ExecutionUncertainError` = no se sabe si llegó |
| `paper_executor.py` | `PaperExecutor` | Fill total con el cierre de la última vela (market), `price` (limit/stop_limit) o `stop_price` (stop); fee = 0 |
| `live_executor.py` | `LiveExecutor` | ccxt + Fernet; envía `params.clientOrderId`; `_to_result` usa `filled` y `average` (o `cost / filled`) del exchange; sin precio → `ExecutionUncertainError`. `InsufficientFunds`/`InvalidOrder`/`ExchangeError` → `RuntimeError`; `RequestTimeout`/`NetworkError`/otro → `ExecutionUncertainError` |

**Selector de executor en `CreateOrderService`:** `bot.mode == "paper"` → PaperExecutor; `"live"` → LiveExecutor

### Servicios (`app/modules/orders/services/`)
| Subdir | Servicios |
|--------|-----------|
| `orders/` | `create_order_service.py`, `get_order_service.py`, `list_orders_service.py` |
| `fills/` | `list_fills_service.py` |
| `positions/` | `list_positions_service.py` |
| `risk/` | `risk_gate_service.py` (`RiskGateService.check(bot, side, qty, reference_price)`) |
| `execution/` | `execute_signal_service.py` (`ExecuteSignalService.execute` / `reject` → `SignalDecision(signal, order)`), `protect_positions_service.py` (`ProtectPositionsService.run()` → `ProtectionReport(checked, closed, failed)`) |

**Flujo de `CreateOrderService.create(...)`** (params nuevos: `owner_id`, `require_running=True`, `reason`):
1. `find_accessible_bot` (si no → `BOT_NOT_FOUND` 404) y `running` (salvo `require_running=False`).
2. Validar lado, tipo, cantidad y precios.
3. `signal_id` (si viene): `SIGNAL_NOT_FOUND` 404 · `ORDER_SIGNAL_MISMATCH` 422 · `ORDER_SIGNAL_ALREADY_USED` 409.
4. Precio de referencia (`price` / `stop_price` / último cierre; sin velas → `ORDER_NO_MARKET_PRICE`); venta > posición → `ORDER_SELL_EXCEEDS_POSITION` 422.
5. `RiskGateService.check`.
6. Crear orden `new` + `client_order_id` + `commit()`.
7. Ejecutar: `ExecutionUncertainError` → `sent` + `needs_reconciliation` → `ORDER_EXECUTION_UNCERTAIN` (502) · `RuntimeError` → `rejected` + `meta.error` + hook de alertas → `ORDER_EXECUTION_FAILED` (502) · éxito → estado real, fill (si hay) y posición.
8. `commit()` + hook de alertas.

**Flujo de `ExecuteSignalService.execute(signal_id, owner_id, decided_by_user_id, channel)`:**
1. Señal y agente accesibles (`SIGNAL_NOT_FOUND`), BUY/SELL aprobada (`SIGNAL_NOT_ACTIONABLE`), `pending` (`SIGNAL_ALREADY_DECIDED`), no vencida (`SIGNAL_EXPIRED`; si venció la marca `expired`).
2. `transition_decision(pending → executing)` + `commit()`; si otro ganó → `SIGNAL_ALREADY_DECIDED` 409.
3. Plan: SELL → vende toda la posición (`SIGNAL_NO_POSITION` si no hay); BUY → sin posición abierta, revalida R/R al cierre actual (`SIGNAL_PRICE_MOVED`) y recalcula la cantidad.
4. `CreateOrderService.create(order_type="market", reason="signal", signal_id=...)`.
5. BUY con posición abierta → `set_protection(signal.stop_loss, signal.take_profit, signal.id)`.
6. `executing → executed`; cualquier fallo → `failed` con `decision_reason` = código (≤ 64).

`reject(...)`: `pending → rejected` con el mismo UPDATE condicional.

Provider: `app/modules/orders/providers/order_provider.py` → `OrderServiceFactory`
- Repos propios: order, fill, position
- Repos borrowed: M7 (bot, signal), M2 (candle/symbol/exchange), M4 (account, account_balance + `CredentialsCipher.from_settings()`)
- `risk_gate()`, `execute_signal()` (con `AGENT_MIN_RR_RATIO`), `protect_positions()`

### Endpoints REST
| Método | Ruta | Auth | Nota |
|--------|------|------|------|
| POST | `/api/orders` | token | Crea y ejecuta orden (paper o live); bot propio (404 si no). 201 con `msg` según estado real |
| GET | `/api/orders` | token | Lista por `bot_id` (propio); sin `bot_id` solo admin (`ORDERS_MISSING_BOT` 400 para los demás) |
| GET | `/api/orders/{id}` | token | Detalle; orden de un agente ajeno → `ORDER_NOT_FOUND` 404 |
| GET | `/api/fills` | token | Por `order_id` o `bot_id`, del usuario (`FILLS_MISSING_FILTER` sin filtro) |
| GET | `/api/positions` | token | Por `bot_id` (propio); sin `bot_id` solo admin (`POSITIONS_MISSING_BOT` 400). Devuelve `stop_loss`, `take_profit`, `signal_id` |
| POST | `/api/signals/{id}/approve` | token | Aprueba una señal pendiente: revalida y envía la orden (`channel="app"`). Devuelve `signal_id`, `decision_status`, `decision_channel`, `decided_at`, `order_id`, `order_status` |
| POST | `/api/signals/{id}/reject` | token | Descarta una señal pendiente |

Los routers declaran `prefix="/orders"`, `"/fills"`, `"/positions"`, `"/signals"` (`signal_decisions`); el `/api` lo añade `app_factory.py` (`settings.API_PREFIX`). Textos: `rest/orders/error_messages.py` (`ORDER_ERROR_MESSAGES`), `rest/signal_decisions/error_messages.py` (`SIGNAL_DECISION_ERROR_MESSAGES` = los de órdenes + los de decisión; [M7](M07-BOTS-SIGNALS.md) lo usa para `decision_reason_message`).

Routers registrados en `app/app_factory.py` (dentro de `api_routers`):
```python
from app.modules.orders.rest import orders_router, fills_router, positions_router, signal_decisions_router
```

### Settings (`app/common/config/settings.py`)
```
TRADING_ENABLED=true          # kill switch global: false → no sale ninguna orden (paper ni live)
TRADING_LIVE_ENABLED=false    # false → solo paper (TRADING_LIVE_DISABLED 403)
ORDER_MAX_NOTIONAL=10000      # tope de qty × precio por compra; 0 = sin tope global
```
Por agente: `risk_params.max_notional` (tope propio; se aplica el menor) y `risk_params.max_drawdown_pct`.

### Frontend (`frontend/src/modules/orders/`)
| Ruta | Archivo de ruta | Página / componentes |
|-----|----------|----|
| `/#/orders` | `routes/_app/orders.lazy.tsx` | `pages/orders.tsx` (`OrdersPage`) + `components/orders-table.tsx` + `components/positions-grid.tsx` + `components/fills-table.tsx` + `components/order-form-dialog.tsx` |
| `/#/admin/orders` | `routes/_app/admin/orders.lazy.tsx` | `pages/admin-orders.tsx` + `components/order-fills-dialog.tsx` |

- API: `api/orders.api.ts` (`listOrders`, `getOrder`, `createOrder`, `listPositions`, `listFills`; `Position` con `stop_loss`, `take_profit`, `signal_id`); hooks `use-orders-queries.ts` / `use-orders-mutations.ts`; etiquetas `lib/orders-labels.ts`; badges `components/order-badges.tsx`.
- `positions-grid.tsx` muestra "Protección automática: SL … · TP …" cuando la posición la tiene.
- Aprobar/descartar: `bots/components/signal-decision-actions.tsx` ([M7](M07-BOTS-SIGNALS.md)).
- El selector de bot de `/#/orders` usa `useBotsByAccountsQuery` de [M7](M07-BOTS-SIGNALS.md); la página admin usa `useBotsQuery()` sin filtro.

## Gotchas críticos

- ~~Prefijo `/api/` obligatorio por colisión con la página web~~ — resuelto el 2026-10-08: ya no hay páginas servidas por FastAPI.
- **La orden se confirma antes de ejecutar:** ya no hay `rollback()` si falla el executor. Un fallo deja la orden en BD como `rejected` (con `meta.error`) o `sent` (con `meta.needs_reconciliation`). Quien lea el historial debe filtrar por estado.
- **`ORDER_EXECUTION_UNCERTAIN` no es "falló":** la orden puede estar viva en el exchange. No reintentar sin revisarla allí (el `client_order_id` la identifica).
- **Paper y SL/TP:** el cierre por stop loss o take profit sale a mercado y en paper se ejecuta al **cierre de la última vela**, no al nivel tocado; el P&L simulado puede ser mejor o peor que el del nivel.
- **Protección y vela en formación:** `ProtectPositionsService` mira la vela más reciente (también la que no ha cerrado); su `high`/`low` ya refleja si se cruzó el nivel.
- **Kill switch y protección:** con `TRADING_ENABLED=false` tampoco salen los cierres por SL/TP.
- **Señal SELL ejecutada = vender toda la posición** del agente, no abrir un corto.
- **Decimales como `float`:** los serializadores de órdenes, fills y posiciones (`_decimal_or_none` → `float(...)`) devuelven `qty`, `price`, `fee`, `avg_price`, `realized_pnl`, `stop_loss`… como números; el front los tipa como `number`. Puede perder precisión en cantidades con muchos decimales.
- **PaperExecutor:** usa `candle_repo.list_candles(symbol_id, timeframe_id, limit=1)` — método se llama `list_candles`, NO `list_by_symbol_and_timeframe`.
- **symbol string para ccxt:** se guarda en `order.meta["symbol"]` en `CreateOrderService` para que `LiveExecutor` lo use.
- **WAP:** `Position.apply_buy_fill()` recalcula avg_price. `apply_sell_fill()` acumula `realized_pnl` y, si queda flat, borra la protección.
- **Esquema requerido:** aplicar `218d50385270` y `f51e2dad9c13` antes de usar esta versión (columnas `client_order_id` y `positions.stop_loss/take_profit/signal_id`).

## Tests

- **No hay tests** para este módulo en `tests/`.
- Recomendado: `tests/orders/test_position_entity.py` (WAP, P&L, `protection_hit`), `test_order_entity.py`, `test_create_order_service.py` (paper + live mockeado, rechazo e incierto), `test_risk_gate_service.py`, `test_execute_signal_service.py`, `test_protect_positions_service.py`.

## Riesgos

- **Dinero real:** el modo `live` envía órdenes reales con un módulo sin tests. Mitigado por `TRADING_LIVE_ENABLED=false` por defecto, el notional máximo y el kill switch.
- Órdenes `sent` con `needs_reconciliation` o ejecuciones parciales quedan sin sincronizar hasta que exista el job de reconciliación.
- SL/TP por ciclo: si el proceso del scheduler se detiene, las posiciones abiertas quedan sin vigilar; en live un hueco de precio cierra lejos del nivel.
- El drawdown se calcula con la pérdida **realizada**: una posición abierta con pérdida grande no lo dispara hasta cerrarse.

## Historial

- **2026-03** — Módulo completado: Order/Fill/Position, `PaperExecutor` + `LiveExecutor`, `CreateOrderService` atómico, UI `/orders` y `/admin/orders`.
- **Requisito:** aplicar antes las migraciones de [M7](M07-BOTS-SIGNALS.md).
- **Posterior** — Hook de alertas post-commit ([M9](M09-ALERTS.md)).
- **2026-10-07** — `commit()` movido a la capa repositorio; rollback explícito cuando falla el executor. Las rutas admin devolvían 500 en vez de 403 (`send()` sin `data`): corregido.
- **2026-10-08** — API headless (/api), páginas migradas a React (frontend/).
- **2026-10-10** — `LiveExecutor` usa el `CCXT_EXCHANGE_MAP` de M2 (sin copia propia) y rechaza perpetuos.
- **2026-10-19** — Auditoría de seguridad: propiedad en órdenes, fills y posiciones (antes cualquier usuario podía operar el agente de otro, incluso en live); `RiskGateService` (kill switch, live apagado por defecto, notional máximo, drawdown → `error`); orden confirmada antes de llamar al exchange con `client_order_id` (migración `218d50385270`), estado real del exchange, rechazos guardados y `ORDER_EXECUTION_UNCERTAIN`; señal vinculada validada y spot sin cortos.
- **2026-10-19** — Modo de ejecución: `ExecuteSignalService` (aprobar/rechazar con reclamo atómico, revalidación al precio actual), `ProtectPositionsService` (SL/TP por ciclo del scheduler, columnas en `positions` de la migración `f51e2dad9c13`), `POST /api/signals/{id}/approve|reject`, protección visible en Posiciones.
