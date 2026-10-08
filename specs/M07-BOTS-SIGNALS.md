# Módulo 7 — Bots & Signals (Bots y Señales) ✅ COMPLETO

← [Índice de módulos](_ROOT.md)

## Ficha

| Campo | Valor |
|---|---|
| Estado | ✅ Completo |
| Avance (alcance original) | 100 % — 8/8 entregables |
| Madurez (estimada) | 73 % — ver [Avance](#avance) |
| Tablas | `bots`, `signals` (R/W); `strategies`, `accounts`, `account_balances`, `candles`, `candle_features`, `feature_sets`, `symbols`, `timeframes` (R) |
| Depende de | [M2](M02-MARKET-DATA.md), [M3](M03-FEATURE-ENGINEERING.md), [M4](M04-ACCOUNTS-PORTFOLIO.md), [M5](M05-STRATEGIES.md), [M6](M06-AI-AGENT.md) |
| Lo usan | [M8](M08-ORDERS-EXECUTION.md) (órdenes por bot), [M9](M09-ALERTS.md) (hooks de señal/error), [M10](M10-BILLING.md) (bot de la cuenta administrada), scheduler de [M2](M02-MARKET-DATA.md) |
| Prefijo API | `/api/bots`, `/api/signals` (ver [corrección de rutas](#corrección-de-rutas)) |
| Última revisión | 2026-10-07 |

## Descripción

**En palabras simples:** Es el piloto automático. Un bot es una instancia que aplica una estrategia sobre un símbolo específico, de forma continua y automática.

**Qué hace:**
- Crea **bots** que combinan: cuenta + símbolo + estrategia + feature set + parámetros de riesgo
- Los bots se pueden activar (`start`), pausar (`pause`) y detener (`stop`) — máquina de estados con transiciones válidas
- Cada bot tiene su propio `feature_set_id` (no es global)
- Al generar una señal: invoca el Agente (M6) con el contexto del bot y persiste el resultado
- Las señales APROBADAS: acción BUY o SELL + entry, SL, TP, position_size, rr_ratio
- Las señales RECHAZADAS: acción HOLD, `approved=False`, todas persisten para trazabilidad
- `features_hash`: SHA-256 del contexto de mercado, fingerprint para auditoría

## Páginas

**Páginas — Usuario (cualquier usuario autenticado):**
- `/bots` — Panel de bots: lista tus bots, crea nuevos, start/pause/stop, ver señales de cada bot, generar señal manualmente

**Páginas — Administrador (solo admin):**
- `/admin/bots` — Vista global de todos los bots del sistema con filtros por estado y modo

## Entregables

Tablas: `bots`, `signals`

Entregables:
- ✅ Bot = cuenta + símbolo + estrategia + feature_set + parámetros de riesgo
- ✅ CRUD bots (start/pause/stop) con máquina de estados en domain entity
- ✅ Cada bot tiene su propio `feature_set_id` (migración m07b)
- ✅ Señales: BUY / SELL / HOLD con entry, SL, TP, position_size, rr_ratio (migración m07a)
- ✅ Señales rechazadas persisten con approved=False (trazabilidad completa)
- ✅ features_hash: SHA-256 del snapshot de features para auditoría
- ✅ Web UI: /bots (usuario) + /admin/bots (admin)
- ✅ 55 tests unitarios pasando (bot entity, status transitions, signal generation)

## Decisiones de diseño

| Decisión | Motivo | Alternativa descartada |
|---|---|---|
| Bot = cuenta + símbolo + estrategia + feature set + `risk_params` | Un bot es una configuración completa y reproducible | Bot ligado solo a la estrategia |
| `feature_set_id` es **por bot**, no global (migración `m07b`) | Cada bot puede usar su propio conjunto de indicadores; se pasa al `AnalyzeService` | Un feature set global |
| Máquina de estados en la **entidad de dominio** (`stopped` / `running` / `paused` / `error`) | Las transiciones válidas viven en un solo sitio y se testean sin BD | Validar transiciones en las rutas |
| Un bot nuevo siempre nace `stopped`; solo se edita su configuración cuando está `stopped` | Evita cambiar parámetros de riesgo con el bot operando | Edición libre |
| `paused` **sí** es activo (`is_active() = True`) | Puede seguir generando señales aunque esté pausado | Pausa = inactivo |
| Las señales rechazadas **también se persisten** con `approved=False` (acción `hold`) | Trazabilidad completa y base para medir el edge | Descartarlas |
| `features_hash`: SHA-256 del contexto de mercado | Huella para auditar con qué datos se generó cada señal | Guardar el snapshot completo |
| Dirección buy/sell inferida: `entry > stop_loss` → buy; `entry < stop_loss` → sell | La señal no necesita un campo de dirección aparte | Pedirle la dirección al LLM |
| Migración `m07` añade `entry_price`, `stop_loss`, `take_profit`, `position_size`, `rr_ratio`, `approved` a `signals` | La señal guarda el plan completo de la operación | Dejarlo en `reasons` JSON |
| `GenerateSignalService` invoca [M6](M06-AI-AGENT.md) vía `_build_analyze_service()` con repos propios y *prestados* | Reutiliza el agente sin duplicar su cableado | Llamar a `/agent/analyze` por HTTP |
| Hook de alertas post-commit, siempre en `try/except` ([M9](M09-ALERTS.md)) | Una alerta nunca debe abortar el flujo de trading | Alertas dentro de la transacción |
| Rutas bajo `/api/bots` y `/api/signals` | La página web `/bots` no debe colisionar con el router REST | Rutas sin prefijo |

## Avance

| Métrica | Valor | Evidencia |
|---|---|---|
| Alcance original | **100 %** (8/8) | CRUD, estados, señales con precios, trazabilidad, `features_hash`, UI y 55 tests |
| Madurez | **≈ 73 %** | Funcionalidad 80 · Tests 80 · Seguridad 80 · Operación 50 |

- **Funcionalidad (80):** las señales se generan **solo a mano** (`POST /api/signals/generate`): el único llamador de `generate_signal` es esa ruta. El scheduler de [M2](M02-MARKET-DATA.md) mantiene velas y features al día pero **no genera señales**.
- **Tests (80):** 55 tests (entidad, transiciones de estado, generación de señal); sin tests de REST ni de propiedad.
- **Operación (50):** sin ejecución periódica de bots ni paso automático de la señal a una orden.

## Posibles mejoras

| Prioridad | Mejora | Esfuerzo |
|---|---|---|
| Alta | **Generación automática de señales:** que el scheduler llame a `generate_signal` para cada bot `running` cuando cierra una vela nueva (hoy es manual) | M |
| Alta | **Puente señal → orden:** crear la orden de [M8](M08-ORDERS-EXECUTION.md) a partir de una señal aprobada (hoy `signal_id` es un parámetro opcional de `CreateOrderService`, no un flujo automático) | M |
| Alta | Evitar señales duplicadas por vela (idempotencia por `bot_id` + `ts`) | S |
| Media | *Kill switch* / límites de riesgo por bot (pérdida diaria máxima, nº de operaciones) y paso automático a `error` ante fallos repetidos (dispara las alertas `error` de [M9](M09-ALERTS.md)) | M |
| Media | Tests de rutas REST y de propiedad (usuario vs admin) | S |
| Baja | Paginación y filtros por fecha/acción en el listado de señales | S |

## Fuera de alcance y pendientes conocidos

- Ejecución autónoma de bots (generar señal + operar sin intervención).
- Tabla `predictions` (diferida desde [M6](M06-AI-AGENT.md) porque requiere `bot_id`; sin modelo ORM todavía).
- Tabla `portfolio_snapshots` (por bot; sin modelo ORM todavía).

## Detalle técnico

### Tablas en BD
| Tabla | Acción | Nota |
|-------|--------|------|
| `bots` | WRITE | CRUD + state machine (stopped/running/paused/error) |
| `signals` | WRITE | Señales generadas por bot (buy/sell/hold + precios) |
| `strategies` | READ | Para construir AnalyzeService (borrowed de M5) |
| `accounts` | READ | Para obtener capital (borrowed de M4) |
| `account_balances` | READ | Balance más reciente (borrowed de M4) |
| `candles` | READ | Última vela (borrowed de M2) |
| `candle_features` | READ | Features del feature_set del bot (borrowed de M3) |
| `feature_sets` | READ | Validar feature_set_id del bot |
| `symbols` | READ | Para validar (borrowed de M2) |
| `timeframes` | READ | Para validar (borrowed de M2) |

### Modelos ORM (`app/modules/bots/infrastructure/`)
| Archivo | Clase ORM | Tabla |
|---------|-----------|-------|
| `bot_model.py` | `BotModel` | `bots` |
| `signal_model.py` | `SignalModel` | `signals` |

Registrados en: `app/extensions/db/models_registry.py`

### Migraciones
- `migrations/m07_add_signal_price_columns.sql` — añade entry_price, stop_loss, take_profit, position_size, rr_ratio, approved a `signals`
- `migrations/m07b_add_bot_feature_set_id.sql` — añade feature_set_id BIGINT NULL con FK a `feature_sets` en `bots`

### Repositorios
| Domain (interfaz) | Infrastructure (impl) |
|-------------------|-----------------------|
| `domain/bot_repository.py` | `infrastructure/bot_repository_impl.py` → `SqlAlchemyBotRepository` |
| `domain/signal_repository.py` | `infrastructure/signal_repository_impl.py` → `SqlAlchemySignalRepository` |

### Servicios (`app/modules/bots/services/`)
| Subdir | Servicios |
|--------|-----------|
| `bots/` | `list_bots_service.py`, `get_bot_service.py`, `create_bot_service.py`, `update_bot_service.py`, `update_bot_status_service.py` |
| `signals/` | `list_signals_service.py`, `generate_signal_service.py` |

Provider: `app/modules/bots/providers/bot_provider.py` → `BotServiceFactory`
- Repos propios: `SqlAlchemyBotRepository`, `SqlAlchemySignalRepository`
- Repos borrowed: M2 (candle/symbol/timeframe), M3 (feature/candle_feature), M4 (account/balance), M5 (strategy)
- `_build_analyze_service()` instancia M6 AnalyzeService con todos sus deps

### Endpoints REST
| Método | Ruta | Auth | Nota |
|--------|------|------|------|
| GET | `/bots` | token | Admin ve todos; user filtra por account_id |
| POST | `/bots` | token | Crea bot (siempre inicia en stopped) |
| GET | `/bots/{id}` | token | Detalle del bot |
| PUT | `/bots/{id}` | token | Edita config (solo cuando stopped) |
| POST | `/bots/{id}/start` | token | Transición → running |
| POST | `/bots/{id}/pause` | token | Transición → paused |
| POST | `/bots/{id}/stop` | token | Transición → stopped |
| GET | `/signals` | token | Lista señales (requiere ?bot_id=X) |
| POST | `/signals/generate` | token | Genera señal invocando M6 |

Routers registrados en `app/app_factory.py`:
```python
from app.modules.bots.rest import bots_router, signals_router
```

### Páginas web
| URL | Template | JS |
|-----|----------|----|
| `/bots` | `templates/bots/index.html` | `static/js/bots/index.js` |
| `/admin/bots` | `templates/admin/bots.html` | `static/js/admin/bots.js` |

### Corrección de rutas

> El antiguo MODULES_MAP listaba los endpoints sin prefijo; en el código los routers declaran `prefix="/api/bots"` y `prefix="/api/signals"`. Usar siempre `/api/bots`, `/api/bots/{id}`, `/api/bots/{id}/start|pause|stop`, `/api/signals` y `/api/signals/generate`.

## Gotchas críticos

- `ServiceResult` almacena el error en `result.error.code` (NO `result.code`). Error que se encontró en `generate_signal_service.py` y se corrigió.
- `feature_set_id` es por bot, NO global. El bot pasa su propio `feature_set_id` al AnalyzeService.
- El bot `paused` ES activo (`is_active() = True`) — puede generar señales aunque esté pausado.
- Señales rechazadas siempre se persisten con `approved=False` para trazabilidad.
- Dirección buy/sell se infiere: `entry > stop_loss` → buy; `entry < stop_loss` → sell.

## Tests

- `tests/bots/test_bot_entity.py` — 22 tests (máquina de estados, is_active, risk_params)
- `tests/bots/test_update_bot_status_service.py` — 16 tests (transiciones, timestamps, session.commit)
- `tests/bots/test_generate_signal_service.py` — 17 tests (validaciones, dirección, campos)
- Total: 55 tests unitarios (22 + 16 + 17).
- **Huecos:** rutas REST, listado/ownership, hook de alertas.

## Riesgos

- Una señal generada con velas/features desactualizados (si el scheduler está apagado o falla un fetch) puede llevar a operar con datos viejos.
- Sin idempotencia por vela, generaciones manuales repetidas crean señales duplicadas.

## Historial

- **2026-03** — Módulo completado: CRUD de bots con máquina de estados, `GenerateSignalService`, UI `/bots` y `/admin/bots`, 55 tests.
- **Migraciones:** `m07_add_signal_price_columns.sql`, `m07b_add_bot_feature_set_id.sql` (deben aplicarse antes de usar [M8](M08-ORDERS-EXECUTION.md)).
- **Posterior** — Hook post-commit de alertas ([M9](M09-ALERTS.md)).
