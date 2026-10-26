# Módulo 8 — Orders & Execution (Órdenes y Ejecución) ✅ COMPLETO

← [Índice de módulos](_ROOT.md)

## Ficha

| Campo | Valor |
|---|---|
| Estado | ✅ Completo |
| Avance (alcance original) | 100 % — 10/10 entregables del plan original (+ 11 nuevos de 2026-10-19) |
| Madurez (estimada) | 84 % — ver [Avance](#avance) |
| Tablas | `orders`, `fills`, `positions`, `funding_payments` (R/W); `signals` (R/W: decisión de ejecución); `bots` (R, y `status` → `error` por drawdown); `candles`, `symbols`, `exchanges`, `accounts`, `account_balances` (R) |
| Depende de | [M2](M02-MARKET-DATA.md), [M4](M04-ACCOUNTS-PORTFOLIO.md) (credenciales Fernet, saldo para el drawdown), [M7](M07-BOTS-SIGNALS.md) (bots, señales, propiedad) |
| Lo usan | [M9](M09-ALERTS.md) (hook de orden; Telegram aprueba/rechaza vía `ExecuteSignalService`), [M11](M11-FUND.md) (fills del agente para liquidar; drawdown sobre su capital), scheduler de [M2](M02-MARKET-DATA.md) (ejecución automática, reconciliación y SL/TP) |
| Prefijo API | `/api/orders`, `/api/fills`, `/api/positions`, `/api/signals/{id}/approve`, `/api/signals/{id}/reject` |
| Frontend | `frontend/src/modules/orders` (aprobar/descartar vive en `frontend/src/modules/bots`) |
| Última revisión | 2026-10-26 |

## Descripción

**En palabras simples:** Es quien aprieta el botón de comprar/vender. Cuando un agente tiene una señal aprobada, este módulo envía la orden al exchange (o la simula en paper), y después protege la posición: en live deja el stop loss como orden en el exchange y vigila el take profit; en paper vigila los dos.

**Qué hace:**
- Crea **órdenes** para un agente: market (precio actual), limit (precio fijo), stop y stop-limit. Solo para agentes del usuario (el admin puede todos).
- Antes de enviar, pasa toda orden por el **RiskGate**: kill switch global, live apagado por defecto, valor máximo por compra y pérdida máxima del agente.
- **Guarda la orden antes de llamar al exchange** (con un `client_order_id` propio) y luego registra lo que el exchange respondió de verdad: ejecutada, ejecutada en parte, enviada sin ejecutar, rechazada o "sin respuesta" (la reconciliación la resuelve después en live).
- Ejecuta según el modo del agente:
  - **Paper:** simula la ejecución total con el cierre de la última vela (fee = 0).
  - **Live:** envía la orden real con ccxt y registra precio, cantidad y comisión reales.
- **Convierte señales en órdenes** (`ExecuteSignalService`): cuando la persona aprueba una señal pendiente (app o Telegram) o cuando el agente está en modo Automático. Revalida al precio actual (R/R ≥ 2:1) y recalcula la cantidad para mantener el mismo riesgo en dinero.
- **Protege posiciones** (`ProtectPositionsService`): una posición abierta desde una señal **o desde una compra manual a mercado con SL/TP** guarda su stop loss y take profit; el scheduler la cierra a mercado cuando una vela los toca.
- **Cancela órdenes** live abiertas (`CancelOrderService`, `POST /api/orders/{id}/cancel`) y las sincroniza con el exchange en el mismo paso.
- **Stop loss nativo en live** (`NativeStopService`): tras la compra de una señal en live, el SL queda como orden stop en el exchange (`positions.sl_order_id`), así protege aunque la app esté caída; el scheduler solo vigila el TP. Antes de cualquier otra venta de esa posición se cancela el SL nativo. Sin OCO: el TP no es una orden en el exchange.
- **Reconcilia con el exchange** (`ReconcileOrdersService`, paso del scheduler): pone al día las órdenes live abiertas (límites que se ejecutaron después, ejecuciones parciales, el SL nativo que disparó el exchange y las órdenes "sin respuesta" que nunca llegaron).
- Registra las **ejecuciones** (fills) y gestiona las **posiciones**: precio medio ponderado (WAP) en cada compra y P&L realizado en cada venta. No hay cortos: no se vende más de lo que hay.
- **Perpetuos de Binance en live (2026-10-26):** metales, materias primas, ETFs y acciones (`XAU/USDT:USDT`) se operan con dinero real, **solo largos, a 1x y con margen aislado**, desde la billetera de Futuros USDⓈ-M. Registra además el **funding** que Binance cobra o paga sobre esas posiciones.
- Máquina de estados de la orden: `new → sent → filled / partially_filled / canceled / rejected`.

**Importante:** Las cuentas "paper" simulan las órdenes sin tocar dinero real. Las cuentas "live" operan con dinero real y, por defecto, están **desactivadas en el servidor** (`TRADING_LIVE_ENABLED=false`).

## Páginas

Hash routing: la URL real es `/#/<ruta>`.

**Páginas — Usuario (cualquier usuario autenticado):**
- Las órdenes de cada agente viven en su detalle (`/#/agents/:id`, [M7](M07-BOTS-SIGNALS.md)): pestaña **Órdenes** (con "Nueva orden", que en compras a mercado ofrece **Protección automática** opcional: stop loss y take profit; y botón **Cancelar** con confirmación en las órdenes live abiertas) y **Posiciones** (con las ejecuciones debajo). `/#/orders` redirige al inicio (`/#/dashboard`) (era un selector de agente que repetía esas pestañas). Las posiciones con protección muestran "Protección automática: SL … · TP …" y, si el SL está en el exchange (live), "El stop loss está como orden en el exchange."
- Aprobar / descartar una señal pendiente: en el detalle de la señal del agente y en la tarjeta "Señales por aprobar" del dashboard ([M7](M07-BOTS-SIGNALS.md)); llaman a `POST /api/signals/{id}/approve|reject` de este módulo.

- `/#/track-record` — "Track record" (Explorar): por estrategia y modo, sumando las operaciones cerradas de todos los agentes que la usan; anónimo y en retornos %.
- Pestaña **Rendimiento** del agente ([M7](M07-BOTS-SIGNALS.md)): resultado realizado y no realizado, % de ganadoras, R/R real contra el objetivo 2:1, profit factor, caída máxima y operaciones cerradas.

**Páginas — Administrador (solo admin):**

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
- ✅ Web UI usuario: pestañas Órdenes y Posiciones (+ ejecuciones) del detalle del agente + diálogo crear orden (página `/#/orders` retirada el 2026-10-19)
- 🗄️ Web UI admin `/#/admin/orders` (retirada el 2026-10-23: las órdenes se ven en la pestaña Órdenes de cada agente)
- ✅ LiveExecutor: integración completa ccxt + Fernet credentials
- ✅ (2026-10-19) **Propiedad** en `POST/GET /api/orders`, `GET /api/orders/{id}`, `/api/fills` y `/api/positions` vía `find_accessible_bot`
- ✅ (2026-10-19) **RiskGateService**: kill switch, live apagado, notional máximo, drawdown máximo
- ✅ (2026-10-19) **Idempotencia y estado real**: `orders.client_order_id` (`ta-{id}`), orden confirmada antes de llamar al exchange, `ExecutionResult` con el estado reportado, rechazos guardados como `rejected`, `ORDER_EXECUTION_UNCERTAIN` + `meta.needs_reconciliation`
- ✅ (2026-10-19) **Señal vinculada validada** (mismo agente, aprobada, misma dirección, una sola orden activa) y regla spot sin cortos
- ✅ (2026-10-19) **ExecuteSignalService**: aprobar/rechazar señales pendientes con reclamo atómico y revalidación al precio actual
- ✅ (2026-10-19) **ProtectPositionsService**: SL/TP automáticos por ciclo del scheduler (`positions.stop_loss`, `take_profit`, `signal_id`)
- ✅ (2026-10-19) REST `POST /api/signals/{id}/approve` y `/reject` (router `signal_decisions`)
- ✅ (2026-10-19) **LiveExecutor ampliado:** cliente ccxt compartido (`_build_client`, `LIVE_USE_SANDBOX` → testnet), `fetch` (por `exchange_order_id` o `clientOrderId`), `cancel` y `place_stop_loss`
- ✅ (2026-10-19) **ReconcileOrdersService:** paso del scheduler que sincroniza estado y fills de las órdenes live `sent`/`partially_filled` (incluidas las `needs_reconciliation`); `position_updater.apply_fill` compartido con `CreateOrderService`
- ✅ (2026-10-19) **NativeStopService:** SL nativo en live tras la BUY de una señal (`positions.sl_order_id`, migración `3ac9fef574cb`, `ORDER_NATIVE_STOP_LOSS`), cancelación antes de cualquier otra venta (`ORDER_NATIVE_STOP_ACTIVE`) y scheduler solo para el TP
- ✅ (2026-10-19) UI: `GET /api/positions` devuelve `sl_order_id` y Posiciones muestra "El stop loss está como orden en el exchange."
- ✅ (2026-10-20) **Cancelar órdenes**: `CancelOrderService` + `POST /api/orders/{id}/cancel` + botón en la UI
- ✅ (2026-10-20) **Protección en órdenes manuales**: `stop_loss` / `take_profit` en `POST /api/orders` (compras a mercado) + SL nativo en live
- ✅ (2026-10-20) **Rate limit** por usuario en crear, cancelar y aprobar órdenes (`ORDER_REQUESTS_PER_MINUTE`)
- ✅ (2026-10-20) **Tests** del módulo (`tests/orders/`) y **script de testnet** (`scripts/testnet_check.py` + `docs/TESTNET.md`)
- ✅ (2026-10-26) **Perpetuos en live**: `LiveExecutor` con precisión y mínimos del mercado, `isolated` + 1x + modo one-way por cuenta y símbolo, margen libre de Futuros, `reduceOnly` en ventas y SL nativo, comisión desde los trades; tabla `funding_payments` y `SyncFundingService` (migración `b7d4e2a91c63`)
- ✅ (2026-10-20) **Rendimiento y track record**: `domain/performance.py` (`compute_performance`), `GetBotPerformanceService`, `ListStrategyTrackRecordService`, `GET /api/performance` y `/api/performance/strategies`; pestaña Rendimiento del agente y página `/#/track-record`

## Decisiones de diseño

> **Fondo común (2026-10-23, [M11](M11-FUND.md)):** el drawdown máximo del RiskGate de un agente del fondo se mide desde la equity de su última liquidación hasta su capital de ahora (`FundCapitalPort`). `FillRepository` suma `list_by_bot_after(bot_id, after_fill_id)` y `max_id_by_bot(bot_id)` (`BotFill` con `fee_asset`) para la contabilidad del fondo, y el armado del cliente ccxt del `LiveExecutor` vive en `accounts/infrastructure/exchange_client.py`.

| Decisión | Motivo | Alternativa descartada |
|---|---|---|
| **Strategy Pattern** para la ejecución: `ExecutorInterface` → `PaperExecutor` / `LiveExecutor` | Mismo flujo para simular y operar con dinero real; añadir un broker no toca el servicio | `if mode == ...` repartido por el código |
| El executor lo elige `bot.mode` (`paper` → `PaperExecutor`, `live` → `LiveExecutor`) en `CreateOrderService` | El modo vive en el bot; no se puede ejecutar *live* por error desde una cuenta paper | Parámetro `mode` en cada request |
| `PaperExecutor` rellena con el cierre de la última vela y `fee = 0`, siempre `filled` | Simulación simple y determinista, sin red | Simular *slippage* y comisiones |
| `LiveExecutor` descifra las credenciales con Fernet ([M4](M04-ACCOUNTS-PORTFOLIO.md)) y envía la orden con ccxt | Las claves nunca viajan ni se guardan en claro | Credenciales en variables de entorno |
| **Persistir antes de enviar:** la orden se crea (`new`), se le asigna `client_order_id = "ta-{id}"` y se hace `commit()` **antes** de llamar al exchange; después se actualiza con el resultado | Si la llamada se corta por red, la orden puede existir en el exchange: revertirla dejaría una orden viva que el sistema no conoce. Los rechazos quedan como historial auditable | Transacción única orden + fill con `rollback()` si falla el executor (esquema anterior a 2026-10-19) |
| `client_order_id` determinista (`Order.build_client_order_id`), UNIQUE en BD y enviado como `clientOrderId` | El exchange rechaza un segundo envío con el mismo ID y permite buscar la orden si se pierde la respuesta; ≤ 36 caracteres válidos en Binance | UUID aleatorio (no se puede reconstruir) |
| El executor devuelve `ExecutionResult(status, exchange_order_id, fill \| None)` con el estado **que reporta el exchange** (`filled` / `partially_filled` / `sent`) | Una límite lejos del precio queda `sent` sin fill; no se asume ejecución total ni se inventa precio 0 | Devolver siempre un `Fill` (antes) |
| Dos tipos de error: `RuntimeError` → orden `rejected` (no existe en el exchange) · `ExecutionUncertainError` (timeout/red/error inesperado o ejecución sin precio) → queda `sent` con `meta.needs_reconciliation` | Distinguir "seguro que no se envió" de "no sabemos" evita reenviar una orden duplicada | Tratar todo fallo como rechazo |
| **RiskGate** como última barrera, para órdenes manuales, aprobadas o automáticas: `TRADING_ENABLED` → `TRADING_LIVE_ENABLED` → solo en compras: notional ≤ min(`ORDER_MAX_NOTIONAL`, `risk_params.max_notional`) y drawdown < `risk_params.max_drawdown_pct` | Las reglas del servidor no dependen del front ni de la IA | Validar solo en el front o en el agente |
| Las **ventas** no se bloquean por notional ni drawdown (sí por el kill switch y por live apagado) | Reducir o cerrar riesgo siempre debe poder hacerse | Mismo filtro para compras y ventas |
| Drawdown alcanzado → el agente pasa a `error` (`BOT_MAX_DRAWDOWN_REACHED`) | Frena al agente hasta que una persona lo revise | Solo rechazar la orden y seguir operando |
| Drawdown = pérdida realizada acumulada / (saldo libre en la moneda base + esa pérdida) | Aproxima el capital inicial sin snapshots | `portfolio_snapshots` (tiene modelo ORM, pero ningún servicio la escribe) |
| **Perpetuos en live, solo largos a 1x con margen aislado** (decisión del usuario, 2026-10-26). Antes de la primera compra de cada (cuenta, símbolo) se exige modo one-way (`fetch_position_mode`; Hedge → rechazo), se fija `isolated` y `set_leverage(1)` (cache en memoria del proceso). Toda venta y todo SL nativo de un perpetuo llevan `reduceOnly` | Con 1x un perpetuo se contabiliza igual que spot (compra = nocional = margen; venta lo devuelve): posiciones, P&L, flujo de caja del fondo y regla del 1 % siguen valiendo. `reduceOnly` impide abrir un corto si la posición ya se cerró en el exchange (p. ej. el SL nativo se disparó) | Cortos y apalancamiento configurable (cambian posiciones, SL/TP, riesgo y la liquidación del fondo) |
| El USDT de Futuros lo pasa **un super admin a mano**; antes de comprar un perpetuo se lee el margen libre (`fetch_balance({"type": "future"})`) y se rechaza si no cubre el nocional × 1,01 | La API key no necesita permiso de transferencias | Transferir Spot → Futuros por API |
| Cantidad redondeada **hacia abajo** a la precisión del mercado (`amount_to_precision`) y, en compras, mínimos de cantidad y de valor (`limits.amount.min`, `limits.cost.min`) con el precio de referencia (`meta.reference_price`). La orden queda con la cantidad enviada (`order.qty`) | El exchange rechazaría cantidades con más decimales; guardar lo enviado mantiene `filled == qty` | Enviar la cantidad tal cual y dejar que el exchange la rechace |
| Comisión de futuros leída de los trades (`fetch_order_trades`) cuando la respuesta no la trae | Binance Futuros no la devuelve al crear la orden; sin ella el flujo de caja del fondo quedaría inflado | Comisión 0 |
| **Funding** en su propia tabla (`funding_payments`, con signo) leída cada `WALLET_SYNC_INTERVAL_SECONDS` con `fetch_funding_history`; un agente live por perpetuo y cuenta ([M7](M07-BOTS-SIGNALS.md)) para poder asignarlo | No es un fill (no compra ni vende) pero mueve dinero: entra al resultado del agente y al flujo del fondo ([M11](M11-FUND.md)) | Ignorarlo · guardarlo como fill |
| Perpetuos con `contractSize` distinto de 1 se rechazan | Binance USDⓈ-M usa 1 unidad por contrato; otro tamaño cambiaría tamaños y P&L | Convertir contratos ↔ unidades |
| **Spot sin cortos:** `side=sell` solo hasta la cantidad de la posición (`ORDER_SELL_EXCEEDS_POSITION`); una señal SELL ejecutada cierra la posición abierta | El esquema (`chk_positions_qty`, `qty ≥ 0`) y los executors no manejan cortos | Representar cortos con `qty` negativa |
| **Una señal = una orden:** `signal_id` debe ser del mismo agente, aprobada, con la misma dirección y sin otra orden que no esté `rejected`/`canceled` | No ejecutar dos veces la misma decisión | Permitir varias órdenes por señal |
| Aprobar una señal = crear la orden, por eso `POST /signals/{id}/approve|reject` vive en `orders` (router `signal_decisions`) y no en `bots` | `orders` ya depende de `bots`; al revés habría ciclo | Endpoint en `bots` que importe `orders` |
| **Reclamo atómico** `pending → executing` con UPDATE condicional (`SignalRepository.transition_decision`) y `commit()` antes de crear la orden | Si la app y Telegram aprueban a la vez, solo uno gana; el otro recibe `SIGNAL_ALREADY_DECIDED` | Bloqueo de fila o comprobación en Python |
| **Revalidar al precio actual** al aprobar: precio sobre el SL, bajo el TP y R/R ≥ `AGENT_MIN_RR_RATIO` desde el cierre actual (`SIGNAL_PRICE_MOVED`); sin piramidar (`SIGNAL_POSITION_ALREADY_OPEN`) | Entre la señal y la aprobación puede pasar una hora: la operación tiene que seguir cumpliendo el 2:1 | Ejecutar con los niveles originales |
| Cantidad recalculada: `riesgo_en_dinero = position_size × \|entry − SL\|` de la señal; `qty = riesgo_en_dinero / (precio_actual − SL)` | Mantiene la regla del 1 % aunque el precio se haya movido | Usar `position_size` tal cual |
| **Protección híbrida:** en live (con `ORDER_NATIVE_STOP_LOSS=true`, por defecto) el SL es una orden stop nativa en el exchange (`create_stop_loss_order`, a mercado) y el TP lo vigila el scheduler; en paper, o si el exchange no soporta `createStopLossOrder` o rechaza el stop, el scheduler vigila los dos. **Sin OCO** | El SL es lo que protege el capital: debe funcionar aunque la app o el scheduler estén caídos. El TP puede esperar al siguiente ciclo. OCO no está en la API unificada de ccxt para la mayoría de exchanges | Todo por ciclo del scheduler (esquema anterior: si el proceso cae nadie vigila) · OCO / TP nativo (mejora futura) |
| Con SL nativo, **toda otra venta de la posición cancela antes el SL** (`NativeStopService.cancel` dentro de `CreateOrderService`); si no se puede cancelar o ya se ejecutó → `ORDER_NATIVE_STOP_ACTIVE` (409) y no se vende | Sin OCO, el SL y la otra venta podrían ejecutarse los dos y vender dos veces la misma posición | Vender y cancelar el SL después |
| El SL nativo se guarda como `Order` propia (`type=stop`, `side=sell`, `meta.reason=stop_loss_native`) con `client_order_id`, persistida **antes** de enviarla; si la respuesta se pierde queda `sent` + `needs_reconciliation` y se vincula igual | Mismo esquema de idempotencia que el resto de órdenes; la reconciliación decide si llegó | Guardar solo el id del exchange en la posición |
| Si el SL nativo no se coloca (no soportado / rechazado → `NATIVE_STOP_FAILED`), **la señal no falla** | La posición ya está abierta y sigue protegida por el scheduler | Marcar la señal `failed` |
| **Reconciliación por ciclo del scheduler** (`ReconcileOrdersService`): órdenes live `sent`/`partially_filled` de los últimos 7 días; registra solo lo ejecutado nuevo (ejecutado en el exchange − fills guardados, y la diferencia de comisión), adopta el estado del exchange y da por perdida (`rejected`, "La orden no llegó al exchange.") a los 10 min una orden `needs_reconciliation` que el exchange no conoce | Las límites, el SL nativo y las respuestas perdidas se resuelven solas sin duplicar fills; 10 min de gracia evitan marcar perdida una orden que el exchange aún no indexa | Revisión manual en el exchange (esquema anterior) · webhooks/websockets del exchange |
| Reconciliación: un `commit()` por orden y errores de red se reintentan en el siguiente ciclo | Un fallo en una orden no deshace las demás | Un commit por ciclo |
| Ejecutada en parte y luego cerrada en el exchange (cancelada/vencida) → `canceled`; cerrada sin ejecutar → `canceled` o `rejected` (`_to_result`) | Estado final real en vez de quedar `partially_filled`/`sent` para siempre | Mantener el último estado conocido |
| **Cancelar = pedir al exchange + sincronizar** (`ReconcileOrdersService.sync_one`) en el mismo request; si el exchange no responde, `meta.cancel_requested` y el siguiente ciclo deja el estado final | Entre el último ciclo y la cancelación pueden haberse ejecutado partes: marcar `canceled` a ciegas perdería esos fills (la reconciliación ya no revisa órdenes finales) | Marcar `canceled` sin consultar |
| Solo se cancelan órdenes **live** `sent`/`partially_filled` con `exchange_order_id`; cancelar no pasa por el RiskGate | En paper todo se ejecuta al instante; sin id hay que esperar a la reconciliación; cancelar reduce riesgo | Cancelar por `clientOrderId` sin id del exchange |
| **Protección pendiente en la orden** (`meta.protection`): si una compra con SL/TP (manual o de señal) no se ejecuta al enviarla (`sent` o sin respuesta), la reconciliación pone SL/TP en la posición al registrar su fill y, en live, el SL nativo; marca `applied` para no repetirlo | Antes, una compra ejecutada tarde abría la posición **sin protección** y nadie la vigilaba | Rechazar la protección en compras que no se ejecutan al instante |
| **La protección la aplica `CreateOrderService`**, también la de las señales (`ExecuteSignalService` le pasa el SL/TP de la señal) | Un solo lugar decide SL/TP y SL nativo, con o sin ejecución inmediata | Que cada llamador ponga la protección después de crear la orden (esquema anterior) |
| **Señal sin confirmar = `executing`**: con `ORDER_EXECUTION_UNCERTAIN` o una orden `sent`, la señal no pasa a `failed`/`executed`; la reconciliación la cierra (`executed` si se ejecutó algo, `failed` con `ORDER_EXECUTION_FAILED` si terminó sin ejecutarse) | "Sin respuesta" no es "falló": la orden puede estar viva en el exchange | Marcarla `failed` (esquema anterior) |
| **Protección manual solo en compras a mercado**, SL < precio < TP y R/R ≥ `AGENT_MIN_RR_RATIO` si vienen los dos; no sobre una posición con SL nativo | Una límite no se sabe cuándo se ejecuta (la protección quedaría colgada); la regla 2:1 aplica también a lo manual; el SL nativo cubriría solo la cantidad anterior | Guardar la protección en la orden y aplicarla al ejecutarse |
| **Operación = de posición 0 a posición 0**, reproduciendo los fills con la misma regla de `Position` (WAP, P&L por precio); las comisiones se informan aparte | Las comisiones pueden venir en el activo base o en la cotización: restarlas mezclaría unidades | Una operación por fill de venta |
| **Track record anónimo en retornos %** por operación (`pnl / invertido`), agrupado por estrategia y modo; profit factor y drawdown sobre los retornos | Cuentas de tamaños distintos no se pueden sumar en dinero, y no se expone quién opera qué | Sumar P&L en dinero de todos los agentes |
| Si una vela toca SL y TP a la vez, **gana el SL** (`Position.protection_hit`) | Sin datos intravela no se sabe cuál llegó primero: se asume el peor caso | Asumir el TP |
| La protección actúa aunque el agente esté pausado o detenido (`require_running=False`); el kill switch sí la detiene | Proteger el capital no depende de que el agente siga buscando entradas | Exigir agente `running` |
| Al quedar flat, `apply_sell_fill` borra SL/TP/`signal_id` de la posición | Una posición nueva no hereda la protección de la anterior | Limpiarlo a mano |
| `meta.reason` en cada orden: `manual`, `signal`, `stop_loss`, `take_profit`, `stop_loss_native` | Historial legible de por qué salió cada orden | Inferirlo de `signal_id` |
| Mensaje de éxito según el estado real (`Orden ejecutada.` / `Orden ejecutada en parte…` / `Orden enviada…`) | La persona sabe si la orden quedó abierta | Un único "Orden ejecutada exitosamente." |
| `positions` único por `(bot_id, symbol_id)` y `qty >= 0` (CHECK) | Una posición abierta por agente y símbolo | Cantidades negativas |
| El símbolo para ccxt se guarda en `order.meta["symbol"]` | `LiveExecutor` no tiene que re-resolver el símbolo | Resolverlo en cada llamada |
| Máquina de estados de la orden en la entidad: `new → sent → filled / partially_filled / canceled / rejected` | Transiciones válidas centralizadas y testeables | Estado libre |
| Solo se crean órdenes para agentes `running` (salvo cierres por SL/TP) | Un agente parado o en error no abre operaciones | Permitirlo y avisar |
| Hook de alertas post-commit en `try/except` ([M9](M09-ALERTS.md)), **también para órdenes rechazadas** | Una alerta no aborta el flujo de trading; un rechazo es justo lo que conviene avisar | Alertas dentro de la transacción |

## Avance

| Métrica | Valor | Evidencia |
|---|---|---|
| Alcance original | **100 %** (10/10) | Dominio, infraestructura, executors paper/live, servicios, REST y UI usuario + admin. Además, 11 entregables nuevos (2026-10-19) |
| Madurez | **≈ 84 %** | Funcionalidad 92 · Tests 80 · Seguridad 90 · Operación 75 |

- **Funcionalidad (92):** señal → orden (aprobación o automático), SL nativo en el exchange en live + TP por ciclo, protección en compras manuales y en compras que se ejecutan tarde, cancelación desde la app y reconciliación automática de las órdenes live abiertas (fills tardíos, parciales, órdenes que nunca llegaron). Faltan: TP nativo / OCO, ajustar el SL nativo si la posición crece con una compra manual, y un paper realista (comisión, *slippage*, fill en el nivel del SL/TP).
- **Tests (80):** `tests/orders/` (2026-10-20) cubre entidades, `LiveExecutor` (ccxt mockeado), RiskGate, crear y cancelar órdenes, señales, protección, reconciliación y SL nativo; destaparon 6 bugs, ya corregidos. Falta correr el circuito contra una **testnet** real (`scripts/testnet_check.py`).
- **Seguridad (90):** propiedad en todas las rutas (404 para agentes ajenos), RiskGate en el servidor, live apagado por defecto, `client_order_id` UNIQUE, una orden por señal, reclamo atómico de la señal, cancelación obligatoria del SL nativo antes de otra venta (evita doble venta), precios con `max_digits=30, decimal_places=12` en el esquema.
- **Operación (75):** kill switch y límites configurables por entorno; reconciliación y protección corren solas en el scheduler (proceso líder), con reintento en el siguiente ciclo ante errores de red; testnet con `LIVE_USE_SANDBOX`; SL nativo desactivable (`ORDER_NATIVE_STOP_LOSS`). Sin métricas ni avisos cuando la reconciliación falla seguido.

## Posibles mejoras

| Prioridad | Mejora | Esfuerzo |
|---|---|---|
| Alta | **Tests** de `CreateOrderService` (paper y live con ccxt mockeado: `filled`/`sent`/rechazo/incierto, cancelación del SL nativo), `RiskGateService`, `ExecuteSignalService` (carrera app/Telegram, precio movido, cantidad recalculada, SL nativo que falla), `ProtectPositionsService` (con y sin SL nativo), `ReconcileOrdersService` (fill tardío, parcial, delta de comisión, perdida a los 10 min, desvincular SL), `NativeStopService`, `LiveExecutor.fetch`/`_to_result`, `Position.apply_*_fill`/`protection_hit` y la máquina de estados de `Order` | M |
| Alta | **Correr** la prueba de testnet (`scripts/testnet_check.py` y el checklist de `docs/TESTNET.md`) con cada exchange que se vaya a usar y anotar el resultado aquí | S |
| Media | **Índice `idx_orders_ts`** (migración): "Todas las órdenes" sin filtros hace `COUNT` y `ORDER BY ts, id` sin índice propio; con mucho volumen se notará | S |
| Media | **TP nativo / OCO** en los exchanges que lo soporten (`create_take_profit_order` o OCO propia del exchange): hoy el TP se vigila por ciclo y un hueco de precio cierra más lejos del nivel | L |
| Media | Ajustar la cantidad del SL nativo si la posición cambia (compra manual sobre una posición protegida: hoy el SL cubre solo la cantidad que había al colocarlo) | S |
| Media | `PaperExecutor` realista: comisión y *slippage* configurables, y cierre por SL/TP al precio del nivel (hoy usa el cierre de la última vela) | S |
| Media | Métricas/avisos de la reconciliación (órdenes que siguen abiertas días, errores seguidos del exchange) | S |
| Media | Saldo mínimo y límite diario de pérdidas/operaciones por agente en el RiskGate | S |
| Media | Soporte de posiciones cortas (`qty` negativa o campo `side`) para perpetuos | L |
| Media | Apalancamiento configurable por agente en perpetuos (hoy fijo 1x) | M |
| Media | Aviso cuando el margen libre de Futuros no alcanza para la próxima compra de un agente | S |
| Baja | Tope de tamaño por capital también al revalidar una señal aprobada (hoy solo en el análisis; si el precio se acercó al SL la cantidad crece y el margen de Futuros puede rechazarla) | S |
| Baja | Cálculo de P&L no realizado de la posición abierta en `/api/positions` | S |

## Fuera de alcance y pendientes conocidos

- **Paper:** fill siempre total al cierre de la última vela (también los cierres por SL/TP), sin comisión ni *slippage*.
- **SL/TP:** en live el SL es una orden stop nativa (si el exchange soporta `createStopLossOrder`), pero el **TP** se vigila una vez por ciclo del scheduler (`SCHEDULER_INTERVAL_SECONDS`, 60 s); no hay OCO. En spot un TP nativo aparte no sirve: el exchange bloquea el saldo del SL y rechazaría la segunda venta por la misma cantidad; solo una OCO (API propia de cada exchange) dejaría los dos niveles en el exchange. En paper, y en live sin SL nativo, los dos van por ciclo. Las órdenes manuales solo tienen protección si se pidió SL/TP (compras a mercado).
- **Reconciliación:** solo órdenes **live** `sent`/`partially_filled` de los **últimos 7 días** (hasta 50 por ciclo); una más vieja que siga abierta hay que revisarla en el exchange.
- Posiciones cortas y apalancamiento > 1x en perpetuos (desde el 2026-10-26 se operan en live solo largos a 1x; antes, solo paper).
- Tests (el roadmap original no los listaba).

## Detalle técnico

### Tablas en BD
| Tabla | Acción | Nota |
|-------|--------|------|
| `orders` | WRITE | Órdenes por bot (market/limit/stop/stop_limit). `client_order_id VARCHAR(64) NULL` + `uq_orders_client_order_id` (NULL en las anteriores a m08). `meta`: `symbol`, `mode`, `reason` (`stop_loss_native` para el SL nativo), y si aplica `error`, `needs_reconciliation` |
| `fills` | WRITE | Ejecuciones de órdenes (CASCADE delete); la reconciliación añade un fill por cada tramo nuevo ejecutado |
| `funding_payments` | WRITE | (2026-10-26) Funding de perpetuos en live: `bot_id`, `account_id`, `symbol_id`, `amount` con signo (+ recibido, − pagado), `asset`, `exchange_funding_id` (UNIQUE con `account_id`), `ts`; índice `(bot_id, ts)` |
| `positions` | WRITE | Posición por bot+symbol (UNIQUE `uq_positions_bot_symbol`). `stop_loss`, `take_profit` `DECIMAL(30,12) NULL` y `signal_id BIGINT NULL` (FK `fk_positions_signal` → `signals`): protección que vigila el scheduler. `sl_order_id BIGINT NULL` (FK `fk_positions_sl_order` → `orders`): orden stop loss nativa en el exchange (NULL = la vigila el scheduler) |
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
- `b7d4e2a91c63` — `m08 futuros live y funding` (2026-10-26): tabla `funding_payments` y, para [M11](M11-FUND.md), `agent_pools.last_funding_id` y `agent_settlements.funding_total`. Escrita a mano.
- `3ac9fef574cb` — `m08 positions native stop order` (`down_revision = f51e2dad9c13`): `positions.sl_order_id BIGINT NULL` + FK `fk_positions_sl_order` → `orders`. Escrita a mano (`AFTER signal_id`); el downgrade quita la FK, su índice y la columna.

### Modelos ORM (`app/modules/orders/infrastructure/`)
| Archivo | Clase | Tabla |
|---------|-------|-------|
| `order_model.py` | `OrderModel` | `orders` |
| `fill_model.py` | `FillModel` | `fills` |
| `position_model.py` | `PositionModel` | `positions` |
| `funding_payment_model.py` | `FundingPaymentModel` | `funding_payments` (repo `SqlAlchemyFundingRepository`: `latest_ts`, `add_new`, `total_after`, `total_by_bot`) |

Registrados en: `app/extensions/db/models_registry.py`

Repos: `OrderRepository.has_active_order_for_signal(signal_id)` (orden que no está `rejected`/`canceled`) · `OrderRepository.list_open_live(since, limit=50)` (`sent`/`partially_filled` desde `since`, más antiguas primero; el modo `live` se filtra en Python desde `meta` para no depender de la sintaxis JSON de MySQL, por eso lee `limit × 4` filas) · `PositionRepository.list_protected()` (`qty > 0` y SL o TP no nulos).

### Dominio
- `Order.build_client_order_id(order_id)` → `"ta-{id}"`.
- `Position.set_protection(sl, tp, signal_id)`, `clear_protection()` (también borra `sl_order_id`), `has_native_stop()` (`sl_order_id` no nulo), `protection_hit(low, high)` → `"stop_loss"` / `"take_profit"` / `None` (solo largos; SL gana si se tocan los dos).

### Execution layer (`app/modules/orders/execution/`)
| Archivo | Clase | Qué hace |
|---------|-------|---------|
| `executor_interface.py` | `ExecutorInterface` (ABC), `ExecutionResult`, `ExecutionUncertainError` | `execute(order, bot) -> ExecutionResult(status, exchange_order_id, fill \| None)`. `RuntimeError` = rechazada; `ExecutionUncertainError` = no se sabe si llegó |
| `paper_executor.py` | `PaperExecutor` | Fill total con el cierre de la última vela (market), `price` (limit/stop_limit) o `stop_price` (stop); fee = 0 |
| `live_executor.py` | `LiveExecutor` | ccxt + Fernet. `_build_client(bot)`: cliente autenticado compartido por todos los métodos (`LIVE_USE_SANDBOX=true` → `set_sandbox_mode(True)`). `execute`: envía `params.clientOrderId`. `place_stop_loss(order, bot)`: exige `client.has['createStopLossOrder']` (si no → `RuntimeError`) y llama `create_stop_loss_order(symbol, 'market', 'sell', qty, None, stop_price, {'clientOrderId'})`. `fetch(order, bot)`: por `exchange_order_id`; sin él, `fetch_order(None, symbol, {'clientOrderId': cid})` y, si el exchange no acepta ese filtro, busca en `fetch_open_orders`/`fetch_closed_orders`; `OrderNotFound` → `None`. `cancel(order, bot)`: `True` si canceló, `False` si `OrderNotFound` o no hay `exchange_order_id`. `_to_result` usa `filled` y `average` (o `cost / filled`); sin ejecución, estado ccxt `canceled`/`cancelled` → `canceled`, `rejected`/`expired` → `rejected`, si no `sent`; sin precio → `ExecutionUncertainError`. Errores al enviar: `InsufficientFunds`/`InvalidOrder`/`ExchangeError` → `RuntimeError`; `RequestTimeout`/`NetworkError`/otro → `ExecutionUncertainError` |

**Selector de executor en `CreateOrderService`:** `bot.mode == "paper"` → PaperExecutor; `"live"` → LiveExecutor

### Servicios (`app/modules/orders/services/`)
| Subdir | Servicios |
|--------|-----------|
| `orders/` | `create_order_service.py`, `cancel_order_service.py`, `get_order_service.py`, `list_orders_service.py`, `position_updater.py` (`apply_fill(position_repo, bot, position, fill_qty, fill_price, side)`: crea la posición o aplica `apply_buy_fill`/`apply_sell_fill`; sin commit. Lo comparten `CreateOrderService` y `ReconcileOrdersService`) |
| `fills/` | `list_fills_service.py` |
| `positions/` | `list_positions_service.py` |
| `risk/` | `risk_gate_service.py` (`RiskGateService.check(bot, side, qty, reference_price)`) |
| `execution/` | `execute_signal_service.py` (`ExecuteSignalService.execute` / `reject` → `SignalDecision(signal, order)`), `protect_positions_service.py` (`ProtectPositionsService.run()` → `ProtectionReport(checked, closed, failed)`), `reconcile_orders_service.py` (`ReconcileOrdersService.run(limit=50)` → `ReconcileReport(checked, updated)`), `native_stop_service.py` (`NativeStopService.place(bot, position, stop_price)` / `cancel(bot, position)`) |

**Flujo de `CreateOrderService.create(...)`** (params nuevos: `owner_id`, `require_running=True`, `reason`):
1. `find_accessible_bot` (si no → `BOT_NOT_FOUND` 404) y `running` (salvo `require_running=False`).
2. Validar lado, tipo, cantidad y precios.
3. `signal_id` (si viene): `SIGNAL_NOT_FOUND` 404 · `ORDER_SIGNAL_MISMATCH` 422 · `ORDER_SIGNAL_ALREADY_USED` 409.
4. Precio de referencia (`price` / `stop_price` / último cierre; sin velas → `ORDER_NO_MARKET_PRICE`); venta > posición → `ORDER_SELL_EXCEEDS_POSITION` 422.
5. `RiskGateService.check`.
5b. Venta de una posición con SL nativo → `NativeStopService.cancel` (sin commit propio: se confirma con la orden en el paso 6); si falla → `ORDER_NATIVE_STOP_ACTIVE` (409) y no se crea la orden.
6. Crear orden `new` + `client_order_id` + `commit()`.
7. Ejecutar: `ExecutionUncertainError` → `sent` + `needs_reconciliation` → `ORDER_EXECUTION_UNCERTAIN` (502) · `RuntimeError` → `rejected` + `meta.error` + hook de alertas → `ORDER_EXECUTION_FAILED` (502) · éxito → estado real, fill (si hay) y posición (`apply_fill`).
8. `commit()` + hook de alertas.

**Flujo de `ExecuteSignalService.execute(signal_id, owner_id, decided_by_user_id, channel)`:**
1. Señal y agente accesibles (`SIGNAL_NOT_FOUND`), BUY/SELL aprobada (`SIGNAL_NOT_ACTIONABLE`), `pending` (`SIGNAL_ALREADY_DECIDED`), no vencida (`SIGNAL_EXPIRED`; si venció la marca `expired`).
2. `transition_decision(pending → executing)` + `commit()`; si otro ganó → `SIGNAL_ALREADY_DECIDED` 409.
3. Plan: SELL → vende toda la posición (`SIGNAL_NO_POSITION` si no hay); BUY → sin posición abierta, revalida R/R al cierre actual (`SIGNAL_PRICE_MOVED`) y recalcula la cantidad.
4. `CreateOrderService.create(order_type="market", reason="signal", signal_id=...)`.
5. La BUY lleva el SL/TP de la señal a `CreateOrderService`: si se ejecuta al instante, la posición guarda la protección (con `signal_id`) y, en live con `ORDER_NATIVE_STOP_LOSS=true`, el SL queda nativo (si falla, solo un warning: el scheduler vigila el SL). Si no se ejecutó, queda en `order.meta.protection` para la reconciliación.
6. `executing → executed`; `ORDER_EXECUTION_UNCERTAIN` u orden `sent` → sigue `executing` (la cierra la reconciliación); cualquier otro fallo → `failed` con `decision_reason` = código (≤ 64).

`reject(...)`: `pending → rejected` con el mismo UPDATE condicional.

**Flujo de `NativeStopService.place(bot, position, stop_price)`:**
1. Crea `Order(type="stop", side="sell", qty=position.qty, stop_price, meta.reason="stop_loss_native")` + `client_order_id` + `commit()` **antes** de enviarla.
2. `LiveExecutor.place_stop_loss`: éxito → estado y `exchange_order_id` reales, vincula `positions.sl_order_id` · `ExecutionUncertainError` → `sent` + `needs_reconciliation` y **se vincula igual** (la reconciliación decide) · `RuntimeError` (no soportado / rechazado) → `rejected` + `meta.error` → `NATIVE_STOP_FAILED` (502), sin vincular.

`cancel(bot, position)`: sin `sl_order_id` → ok · orden inexistente, `canceled` o `rejected` → desvincula · `filled` → `ORDER_NATIVE_STOP_ACTIVE` (409) · `LiveExecutor.cancel` con error o `False` (ya no está abierta) → `ORDER_NATIVE_STOP_ACTIVE` · cancelada → `canceled` y desvincula. No hace commit (lo hace el llamador).

**Flujo de `ReconcileOrdersService.run(limit=50)`** (paso del scheduler):
1. `list_open_live(since=ahora − 7 días)`; por cada orden, `LiveExecutor.fetch`.
2. Error de red (`ExecutionUncertainError`) o del exchange (`RuntimeError`) → se salta; se reintenta en el siguiente ciclo.
3. El exchange no la conoce (`None`): si tiene `needs_reconciliation` y más de **10 min** → `rejected` con `meta.error = "La orden no llegó al exchange."`; si no, se espera.
4. Si la conoce: `_to_result` → completa `exchange_order_id`; fill nuevo = ejecutado en el exchange − suma de fills guardados (comisión = total − comisiones ya guardadas, mínimo 0); adopta el estado del exchange; `partially_filled` con estado ccxt `canceled`/`expired`/`rejected` → `canceled`; quita `needs_reconciliation`. Sin cambios → no escribe nada.
5. `_finish`: guarda el fill y lo aplica a la posición (`apply_fill`); si la orden era el SL nativo de la posición y terminó (`filled`/`canceled`/`rejected`) → `sl_order_id = None`; `commit()` **por orden**; si quedó `rejected` → hook de alertas ([M9](M09-ALERTS.md)).
6. Compra con `meta.protection` sin aplicar y fill nuevo → SL/TP en la posición + SL nativo en live (`native_stop`, solo si `ORDER_NATIVE_STOP_LOSS=true`). Orden de una señal (`signal_repo`) que terminó → `executing → executed | failed`.
7. Cualquier excepción inesperada → `rollback()` de esa orden y sigue con las demás.

**`ProtectPositionsService` con SL nativo:** si la vela toca el SL y la posición `has_native_stop()`, no hace nada (lo ejecuta el exchange y la reconciliación lo registra); solo vende por TP, y esa venta pasa por el paso 5b de `CreateOrderService`.

Provider: `app/modules/orders/providers/order_provider.py` → `OrderServiceFactory`
- Repos propios: order, fill, position
- Repos borrowed: M7 (bot, signal), M2 (candle/symbol/exchange), M4 (account, account_balance + `CredentialsCipher.from_settings()`)
- `risk_gate()`, `execute_signal()` (con `AGENT_MIN_RR_RATIO`; recibe `native_stop()` solo si `ORDER_NATIVE_STOP_LOSS=true`), `protect_positions()`, `native_stop()`, `reconcile_orders()` (con el hook de alertas)
- `create_order()` siempre recibe `native_stop()`: aunque se apague `ORDER_NATIVE_STOP_LOSS`, los SL nativos ya colocados se cancelan antes de vender

### Endpoints REST
| Método | Ruta | Auth | Nota |
|--------|------|------|------|
| POST | `/api/orders` | token | Crea y ejecuta orden (paper o live); bot propio (404 si no). `stop_loss` / `take_profit` opcionales (compras a mercado). 201 con `msg` según estado real. Rate limit por usuario |
| POST | `/api/orders/{id}/cancel` | token | Cancela una orden live abierta y la sincroniza; `msg` según el estado final (cancelada / ya ejecutada / pedida). Rate limit por usuario |
| GET | `/api/orders` | token | Lista por `bot_id` (propio); sin `bot_id` solo admin (`ORDERS_MISSING_BOT` 400 para los demás). Filtros `side`, `status`, `type` (`ORDERS_INVALID_FILTER` 422) y, solo admin, `user_id` (dueño: sus cuentas → sus agentes; ignorado para usuarios). Más reciente primero (`ts`, `id` desc). Paginación opt-in: con `page` (≥ 1) y `page_size` (1–100, 20 por defecto) `data` pasa a ser `{items, pagination: {total, page, page_size, total_pages}}` (`build_paginated_response`); sin `page`, la lista de siempre hasta `limit` (1–500) |
| GET | `/api/orders/{id}` | token | Detalle; orden de un agente ajeno → `ORDER_NOT_FOUND` 404 |
| GET | `/api/fills` | token | Por `order_id` o `bot_id`, del usuario (`FILLS_MISSING_FILTER` sin filtro) |
| GET | `/api/performance?bot_id=` | token | Rendimiento de un agente propio (404 si no): métricas, operaciones cerradas (la más reciente primero), curva de P&L acumulado y P&L no realizado al último cierre |
| GET | `/api/performance/strategies` | token | Track record por estrategia y modo (`?mode=paper\|live`), anónimo y en retornos % |
| GET | `/api/positions` | token | Por `bot_id` (propio); sin `bot_id` solo admin (`POSITIONS_MISSING_BOT` 400). Devuelve `stop_loss`, `take_profit`, `signal_id`, `sl_order_id` (orden stop loss nativa; `null` = la vigila el scheduler) |
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
ORDER_REQUESTS_PER_MINUTE=20  # crear, cancelar o aprobar órdenes por usuario y minuto
ORDER_NATIVE_STOP_LOSS=true   # live: el SL de una posición abierta desde una señal queda como orden en el exchange; false = solo el scheduler
LIVE_USE_SANDBOX=false        # true = testnet del exchange (set_sandbox_mode); necesita claves de testnet en la cuenta
```
Por agente: `risk_params.max_notional` (tope propio; se aplica el menor) y `risk_params.max_drawdown_pct`.

### Frontend (`frontend/src/modules/orders/`)
| Ruta | Archivo de ruta | Página / componentes |
|-----|----------|----|
| `/#/agents/:id` (pestañas Órdenes y Posiciones, página de [M7](M07-BOTS-SIGNALS.md)) | — | `components/orders-table.tsx` + `components/positions-grid.tsx` + `components/fills-table.tsx` + `components/order-form-dialog.tsx` + `components/order-fills-dialog.tsx` |
| `/#/orders` | `routes/_app/orders.tsx` | Redirección a `/dashboard` |

- Paginación en el servidor (2026-10-20): `listOrdersPage(filters, {page, page_size})` → `Paginated<Order>` y `useOrdersPageQuery` (clave `['orders', 'page', filtros, página]`, `keepPreviousData`), usados por Todas las órdenes y por la pestaña Órdenes del agente. `OrdersTable` acepta `pagination` / `isFetching` y los pasa a `DataTable`.
- API: `api/orders.api.ts` (`listOrdersPage`, `getOrder`, `createOrder`, `listPositions`, `listFills`; `Position` con `stop_loss`, `take_profit`, `signal_id`, `sl_order_id`); hooks `use-orders-queries.ts` / `use-orders-mutations.ts`; etiquetas `lib/orders-labels.ts`; badges `components/order-badges.tsx`.
- `positions-grid.tsx` muestra "Protección automática: SL … · TP …" cuando la posición la tiene y, si `sl_order_id` no es `null`, "El stop loss está como orden en el exchange."
- Aprobar/descartar: `bots/components/signal-decision-actions.tsx` ([M7](M07-BOTS-SIGNALS.md)).
- La página admin usa `useBotsQuery()` sin filtro de [M7](M07-BOTS-SIGNALS.md) como catálogo para las columnas Agente y Dueño.

## Gotchas críticos

- ~~Prefijo `/api/` obligatorio por colisión con la página web~~ — resuelto el 2026-10-08: ya no hay páginas servidas por FastAPI.
- **La orden se confirma antes de ejecutar:** ya no hay `rollback()` si falla el executor. Un fallo deja la orden en BD como `rejected` (con `meta.error`) o `sent` (con `meta.needs_reconciliation`). Quien lea el historial debe filtrar por estado.
- **`ORDER_EXECUTION_UNCERTAIN` no es "falló":** la orden puede estar viva en el exchange. No reintentar: en live la reconciliación la busca por `client_order_id` en los ciclos siguientes y, si a los 10 min el exchange no la conoce, la marca `rejected`.
- **La venta por TP cancela antes el SL nativo:** sin OCO, el SL y la venta podrían ejecutarse los dos. Si la cancelación falla (red, error del exchange) o el SL ya se ejecutó, **el scheduler no vende** (`ORDER_NATIVE_STOP_ACTIVE`) y lo reintenta en el siguiente ciclo; la reconciliación registra el SL ejecutado y deja la posición flat. Lo mismo para una venta manual o una señal SELL (409 con el mensaje de `error_messages.py`).
- **SL nativo "incierto" bloquea las ventas un rato:** si `place_stop_loss` se quedó sin respuesta, la orden queda `sent` + `needs_reconciliation` sin `exchange_order_id`; `cancel` devuelve `False` → `ORDER_NATIVE_STOP_ACTIVE` hasta que la reconciliación la encuentre (y complete el id) o la dé por perdida a los 10 min (se desvincula y el scheduler vuelve a vigilar el SL).
- **Venta rechazada después de cancelar el SL nativo:** el SL ya se canceló (se confirma con la orden nueva); la posición conserva `stop_loss`/`take_profit` sin `sl_order_id`, así que el scheduler vuelve a vigilar el SL. No se vuelve a colocar el nativo.
- **El SL nativo cubre la cantidad que había al colocarlo:** una compra manual posterior sobre la misma posición no amplía la orden stop, y mientras haya SL nativo el scheduler no vigila el SL. La cantidad extra solo se vende por ciclo **después** de que la reconciliación registre el SL nativo ejecutado y lo desvincule (un ciclo o más de retraso). Evitar compras manuales sobre posiciones protegidas en live.
- **Testnet:** `LIVE_USE_SANDBOX=true` cambia **todos** los clientes live a la testnet del exchange (`set_sandbox_mode`); la cuenta del agente necesita claves creadas **en la testnet** (las de producción no sirven allí y viceversa). Algunos exchanges de ccxt no tienen testnet: `set_sandbox_mode` falla y la orden queda `rejected` ("No se pudo inicializar el cliente ccxt…").
- **SL nativo depende del exchange:** solo si `client.has['createStopLossOrder']` es verdadero en ccxt; si no, `NATIVE_STOP_FAILED` (orden `rejected` en el historial con `meta.error`) y la protección sigue por ciclo.
- **Órdenes del SL nativo en el libro de órdenes:** aparecen como órdenes `stop` de venta con `meta.reason = stop_loss_native`; cuando el exchange las dispara, la reconciliación registra el fill y la posición queda flat (`clear_protection` borra también `sl_order_id`).
- **Paper y SL/TP:** el cierre por stop loss o take profit sale a mercado y en paper se ejecuta al **cierre de la última vela**, no al nivel tocado; el P&L simulado puede ser mejor o peor que el del nivel.
- **Protección y vela en formación:** `ProtectPositionsService` mira la vela más reciente (también la que no ha cerrado); su `high`/`low` ya refleja si se cruzó el nivel.
- **Kill switch y protección:** con `TRADING_ENABLED=false` tampoco salen los cierres por SL/TP del scheduler. Un SL nativo ya colocado sí lo ejecuta el exchange (el kill switch no lo cancela) y la reconciliación, que no pasa por el RiskGate, lo registra.
- **Señal SELL ejecutada = vender toda la posición** del agente, no abrir un corto (en perpetuos, además, con `reduceOnly`).
- **Perpetuos en live — requisitos en Binance:** API key con "Enable Futures" (sin retiro ni transferencias), el acuerdo de los perpetuos TradFi firmado en la app de Binance, modo de posición **One-way** (con Hedge la compra se rechaza) y USDT en la billetera de Futuros. Sin margen suficiente, la compra queda `rejected` con "Margen insuficiente en la billetera de Futuros…".
- **Preparación de perpetuos en memoria:** el margen aislado y 1x se fijan una vez por proceso y (cuenta, símbolo). Si alguien cambia el apalancamiento a mano en Binance, la app no lo vuelve a fijar hasta reiniciar. No cambiarlo a mano.
- **`order.qty` cambia al enviar en live:** el `LiveExecutor` la redondea a la precisión del mercado y el servicio la guarda así; una compra demasiado chica (bajo el mínimo de cantidad o de valor) queda `rejected` con el motivo.
- **Funding sin agente:** el funding se asigna al agente live de esa cuenta y símbolo; con dos agentes en el mismo perpetuo se mezclaría (por eso la regla de [M7](M07-BOTS-SIGNALS.md)).
- **Testnet de Futuros:** con `LIVE_USE_SANDBOX=true` ccxt usa la testnet de Futuros de Binance para los perpetuos; las claves se crean en testnet.binancefuture.com (distintas de las de spot).
- **Decimales como `float`:** los serializadores de órdenes, fills y posiciones (`_decimal_or_none` → `float(...)`) devuelven `qty`, `price`, `fee`, `avg_price`, `realized_pnl`, `stop_loss`… como números; el front los tipa como `number`. Puede perder precisión en cantidades con muchos decimales.
- **PaperExecutor:** usa `candle_repo.list_candles(symbol_id, timeframe_id, limit=1)` — método se llama `list_candles`, NO `list_by_symbol_and_timeframe`.
- **symbol string para ccxt:** se guarda en `order.meta["symbol"]` en `CreateOrderService` para que `LiveExecutor` lo use.
- **WAP:** `Position.apply_buy_fill()` recalcula avg_price. `apply_sell_fill()` acumula `realized_pnl` y, si queda flat, borra la protección.
- **Esquema requerido:** aplicar `218d50385270`, `f51e2dad9c13` y `3ac9fef574cb` antes de usar esta versión (columnas `client_order_id`, `positions.stop_loss/take_profit/signal_id` y `positions.sl_order_id`).

## Tests

- `tests/orders/` (2026-10-20, unitarios con mocks, sin BD ni red): `test_order_entity.py`, `test_position_entity.py`, `test_live_executor.py` (ccxt mockeado), `test_risk_gate_service.py`, `test_create_order_service.py` (incluye protección manual), `test_cancel_order_service.py`, `test_execute_signal_service.py`, `test_protect_positions_service.py`, `test_reconcile_orders_service.py`, `test_native_stop_service.py`.
- **Pendiente:** correr el circuito contra una testnet real (`scripts/testnet_check.py`, `docs/TESTNET.md`).

## Riesgos

- **Dinero real:** el modo `live` envía órdenes reales con un módulo sin tests y sin pruebas en testnet. Mitigado por `TRADING_LIVE_ENABLED=false` por defecto, el notional máximo y el kill switch.
- Reconciliación por ciclo: mientras el scheduler esté caído, las órdenes abiertas y los SL nativos ejecutados no se registran (la posición en la app va por detrás del exchange); las órdenes de más de 7 días que sigan abiertas no se revisan.
- TP por ciclo (y SL en paper o sin SL nativo): si el proceso del scheduler se detiene, el TP no se vigila; en live un hueco de precio cierra lejos del nivel. El SL nativo sí sigue protegiendo en el exchange.
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
- **2026-10-19** — Reconciliación y SL nativo: `LiveExecutor` con cliente compartido, `fetch`/`cancel`/`place_stop_loss` y `LIVE_USE_SANDBOX`; `ReconcileOrdersService` en el ciclo del scheduler (fills tardíos y parciales, órdenes perdidas a los 10 min); `NativeStopService` (SL como orden en el exchange en live, `positions.sl_order_id`, migración `3ac9fef574cb`, `ORDER_NATIVE_STOP_LOSS`, `ORDER_NATIVE_STOP_ACTIVE`); TP sigue por ciclo, sin OCO; `position_updater.apply_fill` compartido; aviso en Posiciones. Verificado solo con pruebas de humo con mocks.
- **2026-10-19** — Página `/orders` retirada (duplicaba las pestañas Órdenes y Posiciones del agente): redirige a `/agents` y sale del menú.
- **2026-10-20** — Todas las órdenes: columna **Dueño** (nombre y correo) y filtro por dueño.
- **2026-10-20** — Fase 1: cancelar órdenes (`CancelOrderService`, `POST /api/orders/{id}/cancel`, botón en la UI), protección SL/TP en compras manuales a mercado (con SL nativo en live), rate limit por usuario en crear/cancelar/aprobar (`ORDER_REQUESTS_PER_MINUTE`), tests del módulo y script + checklist de testnet. TP nativo / OCO sigue pendiente (ver Fuera de alcance). Los tests destaparon y se corrigieron: posición sin protección si la compra se ejecutaba tarde, señal `failed` con la orden viva, precio del fill de una límite (`price` antes que `cost / filled`), P&L de una venta mayor que la posición y la máquina de estados de `Order` (ahora `new` pasa directo a `filled`/`partially_filled`/`rejected`).
- **2026-10-20** — **Paginación en el servidor** (Fase 4): `GET /api/orders` acepta `page`/`page_size` opt-in (sin `page`, misma lista que antes) y los filtros `side`, `status`, `type` y `user_id` (dueño, solo admin). `OrderRepository.search/count` con `OrderCriteria` reemplaza a `list_all`/`list_by_bot`; `ListOrdersService.list_page`. Todas las órdenes deja de traer 500 y filtrar en el navegador; la pestaña Órdenes del agente también pagina. Tests: `tests/orders/test_list_orders_service.py` (servicio, repo con sesión mockeada y contrato de la ruta con y sin `page`).
- **2026-10-20** — Rendimiento por agente y track record por estrategia (`domain/performance.py`, `GET /api/performance`, `/api/performance/strategies`, pestaña Rendimiento y página Track record; `tests/orders/test_performance.py`).
- **2026-10-23** — Se retira el grupo **Supervisión** del menú: fuera "Todas las órdenes" (`/#/admin/orders`, `pages/admin-orders.tsx`); `OrdersTable` pierde `botNames` y `renderOwner`. Las órdenes se ven en la pestaña Órdenes del agente. `GET /api/orders` sigue igual en el backend.
- **2026-10-26** — `CreateOrderService` rechaza las compras live cuyo símbolo es de otro exchange que la cuenta (`ORDER_EXCHANGE_MISMATCH`); las ventas siguen para no atrapar posiciones. Respaldo de la regla de [M7](M07-BOTS-SIGNALS.md).
- **2026-10-26** — Se quita `ORDER_EXCHANGE_MISMATCH`: la plataforma opera solo con Binance ([M2](M02-MARKET-DATA.md)).
- **2026-10-26** — **Perpetuos de Binance en live** (solo largos, 1x, margen aislado, modo one-way): precisión y mínimos, margen libre de Futuros, `reduceOnly` en ventas y SL nativo, comisión desde los trades, funding en `funding_payments` (paso del scheduler junto a la billetera) y en Rendimiento (`funding_total`). Migración `b7d4e2a91c63`.
