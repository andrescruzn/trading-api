# Módulo 8 — Orders & Execution (Órdenes y Ejecución) ✅ COMPLETO

← [Índice de módulos](_ROOT.md)

## Ficha

| Campo | Valor |
|---|---|
| Estado | ✅ Completo (sin tests) |
| Avance (alcance original) | 100 % — 10/10 entregables |
| Madurez (estimada) | 50 % — ver [Avance](#avance) |
| Tablas | `orders`, `fills`, `positions` (R/W); `bots`, `candles`, `symbols`, `exchanges`, `accounts` (R) |
| Depende de | [M2](M02-MARKET-DATA.md), [M4](M04-ACCOUNTS-PORTFOLIO.md) (credenciales Fernet), [M7](M07-BOTS-SIGNALS.md) |
| Lo usan | [M9](M09-ALERTS.md) (hook de orden), [M10](M10-BILLING.md) (historial de órdenes y fills) |
| Prefijo API | `/api/orders`, `/api/fills`, `/api/positions` (el `/api/` es obligatorio) |
| Última revisión | 2026-10-07 |

## Descripción

**En palabras simples:** Es quien aprieta el botón de comprar/vender. Cuando el bot genera una señal aprobada, este módulo ejecuta la orden real en el exchange.

**Qué hace:**
- Crea **órdenes** para un bot: market (precio actual), limit (precio fijo), stop y stop-limit
- Ejecuta la orden según el modo del bot:
  - **Paper mode:** simula el fill usando el precio de cierre de la última vela (fee = 0)
  - **Live mode:** envía la orden real al exchange vía ccxt, recibe precio y fee reales
- Registra las **ejecuciones** (fills): cuánto se ejecutó realmente, a qué precio y con qué comisión
- Gestiona las **posiciones abiertas**: recalcula el precio promedio (WAP) en cada compra, acumula el P&L realizado en cada venta
- Máquina de estados de la orden: `new → sent → filled / partially_filled / canceled / rejected`

**Importante:** Las cuentas "paper" simulan las órdenes sin tocar dinero real. Las cuentas "live" operan con dinero real.

## Páginas

**Páginas — Usuario (cualquier usuario autenticado):**
- `/orders` — Libro de órdenes: selector de bot, tabs de Órdenes / Posiciones / Ejecuciones, modal para crear nueva orden

**Páginas — Administrador (solo admin):**
- `/admin/orders` — Vista global de todas las órdenes del sistema con filtros por lado, estado y tipo

## Entregables

Tablas: `orders`, `fills`, `positions`

Entregables:
- ✅ Domain: Order entity (state machine), Fill entity, Position entity (WAP + P&L)
- ✅ Infrastructure: ORM models + repository impls para orders, fills, positions
- ✅ Execution (Strategy Pattern): PaperExecutor (simula con última vela) + LiveExecutor (ccxt real)
- ✅ Services: list_orders, get_order, create_order, list_fills, list_positions
- ✅ CreateOrderService: valida bot, selecciona executor según bot.mode, crea order+fill+position en transacción atómica
- ✅ Provider: OrderServiceFactory con repos propios + borrowed de M7/M2/M4
- ✅ REST: POST /orders, GET /orders, GET /orders/{id}, GET /fills, GET /positions
- ✅ Web UI usuario: /orders con tabs Órdenes/Posiciones/Ejecuciones + modal crear orden
- ✅ Web UI admin: /admin/orders con filtros por lado/estado/tipo + modal fills
- ✅ LiveExecutor: integración completa ccxt + Fernet credentials

## Decisiones de diseño

| Decisión | Motivo | Alternativa descartada |
|---|---|---|
| **Strategy Pattern** para la ejecución: `ExecutorInterface` → `PaperExecutor` / `LiveExecutor` | Mismo flujo para simular y operar con dinero real; añadir un broker no toca el servicio | `if mode == ...` repartido por el código |
| El executor lo elige `bot.mode` (`paper` → `PaperExecutor`, `live` → `LiveExecutor`) en `CreateOrderService` | El modo vive en el bot; no se puede ejecutar *live* por error desde una cuenta paper | Parámetro `mode` en cada request |
| `PaperExecutor` rellena con el cierre de la última vela y `fee = 0` | Simulación simple y determinista, sin red | Simular *slippage* y comisiones |
| `LiveExecutor` descifra las credenciales con Fernet ([M4](M04-ACCOUNTS-PORTFOLIO.md)) y envía la orden con ccxt | Las claves nunca viajan ni se guardan en claro | Credenciales en variables de entorno |
| **Transacción atómica:** orden + fill + upsert de posición en un solo `order_repo.commit()` (repos con sesión compartida); `order_repo.rollback()` si falla el executor | Nunca queda una orden sin su fill/posición | Commits separados |
| Posición con **precio medio ponderado (WAP)**: `apply_buy_fill()` recalcula `avg_price`; `apply_sell_fill()` acumula `realized_pnl` | Cálculo estándar de coste medio y P&L realizado | FIFO / lotes |
| `positions` único por `(bot_id, symbol_id)` y `qty >= 0` (CHECK) | Una posición abierta por bot y símbolo; **no admite posiciones cortas** | Cantidades negativas |
| El símbolo para ccxt se guarda en `order.meta["symbol"]` | `LiveExecutor` no tiene que re-resolver el símbolo | Resolverlo en cada llamada |
| Máquina de estados de la orden en la entidad: `new → sent → filled / partially_filled / canceled / rejected` | Transiciones válidas centralizadas y testeables | Estado libre |
| Solo se crean órdenes para bots `running` | Un bot parado o en error no opera | Permitirlo y avisar |
| Prefijo `/api/` obligatorio | Las páginas `/orders` y `/admin/orders` quedaban tapadas por el router REST | Cambiar las páginas de ruta |
| Hook de alertas post-commit en `try/except` ([M9](M09-ALERTS.md)) | Una alerta no aborta el flujo de trading | Alertas dentro de la transacción |

## Avance

| Métrica | Valor | Evidencia |
|---|---|---|
| Alcance original | **100 %** (10/10) | Dominio, infraestructura, executors paper/live, servicios, REST y UI usuario + admin |
| Madurez | **≈ 50 %** | Funcionalidad 80 · Tests 0 · Seguridad 70 · Operación 50 |

- **Funcionalidad (80):** no hay gestión automática de Stop Loss / Take Profit tras la entrada (no aparecen en `CreateOrderService` ni en los executors), ni endpoint de cancelación, ni sincronización del estado de órdenes abiertas con el exchange.
- **Tests (0):** **ningún test** cubre este módulo, que es donde se mueve el dinero.
- **Seguridad (70):** credenciales cifradas y listados por bot (el admin puede listar todo); sin límites de tamaño de orden ni confirmación para `live`.
- **Operación (50):** sin reconciliación con el exchange ni reintentos.

## Posibles mejoras

| Prioridad | Mejora | Esfuerzo |
|---|---|---|
| Alta | **Tests** de `CreateOrderService` (paper y live con ccxt mockeado), `Position.apply_buy_fill/apply_sell_fill` (WAP y P&L) y la máquina de estados de `Order` | M |
| Alta | **SL/TP automáticos:** crear órdenes de protección (OCO/`stop`) al abrir una posición o monitorizar precio y cerrar; hoy la señal de [M7](M07-BOTS-SIGNALS.md) los calcula pero nadie los ejecuta | L |
| Alta | Cancelar órdenes (`DELETE`/`POST .../cancel`) y **sincronizar estado y fills** con el exchange (`fetch_order`), para `limit`/`stop` y ejecuciones parciales | L |
| Alta | Salvaguardas para `live`: tamaño máximo de orden, saldo mínimo, límite diario y confirmación explícita | M |
| Media | Soporte de posiciones cortas (`qty` negativa o campo `side`): una señal SELL de [M7](M07-BOTS-SIGNALS.md) implica corto y el esquema hoy lo impide (`chk_positions_qty`) | L |
| Media | `PaperExecutor` realista: comisión y *slippage* configurables | S |
| Media | Idempotencia con `client_order_id` para no duplicar órdenes al reintentar | M |
| Baja | Cálculo de P&L no realizado de la posición abierta en `/api/positions` | S |

## Fuera de alcance y pendientes conocidos

- Stop Loss / Take Profit automáticos (el flujo de [`_ROOT.md`](_ROOT.md) los describe como objetivo, no están implementados).
- Cancelación de órdenes y reconciliación con el exchange.
- Posiciones cortas y apalancamiento / futuros.
- Tests (el roadmap original no los listaba).

## Detalle técnico

### Tablas en BD
| Tabla | Acción | Nota |
|-------|--------|------|
| `orders` | WRITE | Órdenes por bot (market/limit/stop/stop_limit) |
| `fills` | WRITE | Ejecuciones de órdenes (CASCADE delete) |
| `positions` | WRITE | Posición abierta por bot+symbol (UNIQUE uq_positions_bot_symbol) |
| `bots` | READ | Para validar bot existe y está running |
| `candles` | READ | PaperExecutor usa última vela para precio |
| `symbols` | READ | Para resolver símbolo del bot |
| `exchanges` | READ | Para resolver exchange en LiveExecutor |
| `accounts` | READ | Para obtener credenciales cifradas en LiveExecutor |

### Modelos ORM (`app/modules/orders/infrastructure/`)
| Archivo | Clase | Tabla |
|---------|-------|-------|
| `order_model.py` | `OrderModel` | `orders` |
| `fill_model.py` | `FillModel` | `fills` |
| `position_model.py` | `PositionModel` | `positions` |

Registrados en: `app/extensions/db/models_registry.py`

### Execution layer (`app/modules/orders/execution/`)
| Archivo | Clase | Qué hace |
|---------|-------|---------|
| `executor_interface.py` | `ExecutorInterface` (ABC) | Interfaz: `execute(order, bot) -> Fill` |
| `paper_executor.py` | `PaperExecutor` | Simula fill con precio de última vela, fee=0 |
| `live_executor.py` | `LiveExecutor` | Envía orden real al exchange via ccxt + Fernet decrypt |

**Selector de executor en `CreateOrderService`:** `bot.mode == "paper"` → PaperExecutor; `"live"` → LiveExecutor

### Servicios (`app/modules/orders/services/`)
| Subdir | Servicios |
|--------|-----------|
| `orders/` | `create_order_service.py`, `get_order_service.py`, `list_orders_service.py` |
| `fills/` | `list_fills_service.py` |
| `positions/` | `list_positions_service.py` |

Provider: `app/modules/orders/providers/order_provider.py` → `OrderServiceFactory`
- Repos propios: order, fill, position
- Repos borrowed: M7 (bot), M2 (candle/symbol/exchange), M4 (account + CredentialsCipher)

### Endpoints REST
| Método | Ruta | Auth | Nota |
|--------|------|------|------|
| POST | `/api/orders` | token | Crea y ejecuta orden (paper o live) |
| GET | `/api/orders` | token | Lista por bot_id (admin puede listar todo) |
| GET | `/api/orders/{id}` | token | Detalle de una orden |
| GET | `/api/fills` | token | Lista por order_id o bot_id |
| GET | `/api/positions` | token | Lista por bot_id (admin puede listar todo) |

**⚠️ IMPORTANTE:** Prefijo `/api/` obligatorio — sin él colisiona con las páginas web `/orders` y `/admin/orders`.

Routers registrados en `app/app_factory.py`:
```python
from app.modules.orders.rest import orders_router, fills_router, positions_router
```

### Páginas web
| URL | Template | JS |
|-----|----------|----|
| `/orders` | `templates/orders/index.html` | `static/js/orders/index.js` |
| `/admin/orders` | `templates/admin/orders.html` | `static/js/admin/orders.js` |

## Gotchas críticos

- **Prefijo `/api/`:** las rutas REST DEBEN usar `/api/orders`, `/api/fills`, `/api/positions` — sin él la página web `/orders` nunca se renderiza (el router REST captura antes).
- **PaperExecutor:** usa `candle_repo.list_candles(symbol_id, timeframe_id, limit=1)` — método se llama `list_candles`, NO `list_by_symbol_and_timeframe`.
- **symbol string para ccxt:** se guarda en `order.meta["symbol"]` en `CreateOrderService` para que `LiveExecutor` lo use.
- **Transacción atómica:** order + fill + upsert position en un solo `order_repo.commit()`; si el executor lanza `RuntimeError`, `order_repo.rollback()` explícito.
- **WAP:** `Position.apply_buy_fill()` recalcula avg_price. `apply_sell_fill()` acumula `realized_pnl`.
- **Migraciones M7 requeridas:** `m07_add_signal_price_columns.sql` y `m07b_add_bot_feature_set_id.sql` deben aplicarse antes de usar M8.

## Tests

- **No hay tests** para este módulo en `tests/`.
- Recomendado: `tests/orders/test_position_entity.py`, `test_order_entity.py`, `test_create_order_service.py` (paper + live mockeado).

## Riesgos

- **Dinero real:** el modo `live` envía órdenes reales con un módulo sin tests y sin salvaguardas de tamaño.
- Una orden aceptada por el exchange pero con fallo posterior en BD (o al revés) deja estado inconsistente: no hay reconciliación.
- Sin SL/TP automáticos, una posición abierta no está protegida si el sistema se detiene.
- Una señal SELL de [M7](M07-BOTS-SIGNALS.md) (corto) no se puede representar en `positions`.

## Historial

- **2026-03** — Módulo completado: Order/Fill/Position, `PaperExecutor` + `LiveExecutor`, `CreateOrderService` atómico, UI `/orders` y `/admin/orders`.
- **Requisito:** aplicar antes las migraciones de [M7](M07-BOTS-SIGNALS.md).
- **Posterior** — Hook de alertas post-commit ([M9](M09-ALERTS.md)).
- **2026-10-07** — `commit()` movido a la capa repositorio; rollback explícito cuando falla el executor. Las rutas admin devolvían 500 en vez de 403 (`send()` sin `data`): corregido.
