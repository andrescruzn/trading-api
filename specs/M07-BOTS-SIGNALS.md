# Módulo 7 — Bots & Signals (Agentes y Señales) ✅ COMPLETO

← [Índice de módulos](_ROOT.md)

## Ficha

| Campo | Valor |
|---|---|
| Estado | ✅ Completo |
| Avance (alcance original) | 100 % — 11/11 entregables |
| Madurez (estimada) | 75 % — ver [Avance](#avance) |
| Tablas | `bots`, `signals` (R/W); `strategies`, `accounts`, `account_balances`, `candles`, `candle_features`, `feature_sets`, `symbols`, `timeframes` (R) |
| Depende de | [M2](M02-MARKET-DATA.md), [M3](M03-FEATURE-ENGINEERING.md), [M4](M04-ACCOUNTS-PORTFOLIO.md), [M5](M05-STRATEGIES.md), [M6](M06-AI-AGENT.md) |
| Lo usan | [M8](M08-ORDERS-EXECUTION.md) (órdenes por bot), [M9](M09-ALERTS.md) (hooks de señal/error), [M10](M10-BILLING.md) (bot de la cuenta administrada), scheduler de [M2](M02-MARKET-DATA.md), dashboard de [M1](M01-AUTH.md) |
| Prefijo API | `/api/bots`, `/api/signals` (ver [corrección de rutas](#corrección-de-rutas)) |
| Frontend | `frontend/src/modules/bots` |
| Última revisión | 2026-10-19 |

## Descripción

**En palabras simples:** Es el piloto automático y el **punto de entrada de la app**. En la interfaz los bots se llaman **agentes**: un agente vigila un símbolo, aplica una estrategia y le pide a la IA que confirme cada operación. Crear y encender un agente es lo que pone a andar todo lo demás (el scheduler solo descarga velas e indicadores para agentes activos).

**Qué hace:**
- Crea **agentes** (tabla `bots`) con nombre + cuenta + símbolo + estrategia + conjunto de indicadores + parámetros de riesgo.
- Valida al crear: que existan las referencias, que la cuenta sea del usuario y esté activa, que el modo coincida con el de la cuenta, que el conjunto de indicadores cubra las reglas de la estrategia y la regla del 1 %.
- Los agentes se activan (`start`), pausan (`pause`) y detienen (`stop`) con una máquina de estados.
- Un usuario solo ve y opera **sus** agentes (propiedad por cuenta); el admin ve todos.
- Al generar una señal ("Analizar ahora"): invoca el Agente (M6) con el contexto del bot y persiste el resultado.
- Señales APROBADAS: BUY o SELL + entry, SL, TP, position_size, rr_ratio. RECHAZADAS: HOLD, `approved=False`; todas persisten.
- `features_hash`: SHA-256 del contexto de mercado, fingerprint para auditoría.
- Cada señal guarda qué servicio de IA respondió (`llm_provider`), con qué modelo (`llm_model`) y cuánto tardó (`llm_latency_ms`).

## Páginas

Hash routing: la URL real es `/#/<ruta>`.

**Páginas — Usuario (cualquier usuario autenticado):**
- `/#/agents` — **Mis agentes**: tarjetas con estado (punto que late si está activo), símbolo · timeframe, estrategia, última señal y botones Iniciar/Reanudar/Pausar. Filtro Todos / Activos / Detenidos. Sin agentes: bienvenida que explica qué es un agente.
- `/#/agents/new` — **Asistente de creación** en 4 pasos: (1) qué operar (solo símbolos con velas automáticas), (2) cómo opera (estrategia + conjunto de indicadores compatible, con el recomendado preseleccionado), (3) con qué dinero (cuentas propias con su saldo; crea una cuenta de práctica en línea si no hay), (4) revisar: nombre sugerido editable, riesgo de la estrategia en solo lectura, "Iniciarlo al crear".
- `/#/agents/:id` — **Detalle**: nombre editable, controles, **Analizar ahora** (genera una señal y abre su detalle), aviso "Preparando datos" hasta que hay indicadores, pestañas Señales · Órdenes (con Nueva orden) · Posiciones (+ ejecuciones) · Configuración (reglas e indicadores explicados).
- `/#/bots` y `/#/agent` redirigen a `/#/agents`.

**Páginas — Administrador (solo admin):**
- `/#/admin/agents` — Vista global de todos los agentes con filtros por estado y modo; clic en una fila abre el detalle. `/#/admin/bots` redirige aquí.

## Entregables

Tablas: `bots`, `signals`

Entregables:
- ✅ Bot = nombre + cuenta + símbolo + estrategia + feature_set + parámetros de riesgo
- ✅ CRUD bots (start/pause/stop) con máquina de estados en domain entity
- ✅ Cada bot tiene su propio `feature_set_id` (migración m07b)
- ✅ Señales: BUY / SELL / HOLD con entry, SL, TP, position_size, rr_ratio (migración m07a)
- ✅ Señales rechazadas persisten con approved=False (trazabilidad completa)
- ✅ features_hash: SHA-256 del snapshot de features para auditoría
- ✅ Web UI en React: Mis agentes, asistente, detalle y vista admin
- ✅ 55 tests unitarios pasando (bot entity, status transitions, signal generation)
- ✅ **Agentes con nombre** (`bots.name`, migración `m07 add name to bots`)
- ✅ **Propiedad** en todas las rutas de bots y señales (404 para bots ajenos)
- ✅ **Servicio, modelo y latencia de la IA** por señal (`signals.llm_provider`, `llm_model`, `llm_latency_ms`; migración `m07 signals llm provider model latency`), visibles en el detalle de la señal
- ✅ **Validaciones al crear** (referencias, cuenta propia y activa, modo = cuenta, compatibilidad estrategia/indicadores, regla del 1 %)

## Decisiones de diseño

| Decisión | Motivo | Alternativa descartada |
|---|---|---|
| En la UI "bot" se llama **agente**; código, tablas y API siguen siendo `bot` | El usuario piensa en "agentes" que operan por él; renombrar el backend no aporta y rompe contratos | Renombrar tablas y endpoints |
| La página "Agente de IA" (análisis puntual sin bot) se integra en cada agente como **Analizar ahora** | Un solo concepto para el usuario; el análisis queda guardado como señal | Mantener dos páginas con nombres parecidos |
| Bot = nombre + cuenta + símbolo + estrategia + feature set + `risk_params` | Un bot es una configuración completa y reproducible | Bot ligado solo a la estrategia |
| El asistente deriva **timeframe** y **riesgo** de la estrategia y el **modo** de la cuenta | Menos campos y sin incoherencias (antes se podían elegir distintos) | Pedirlos de nuevo en el formulario |
| Solo se ofrecen conjuntos de indicadores **compatibles** con las reglas de la estrategia; el backend lo vuelve a validar | Una regla sin su indicador se rechazaría siempre en silencio | Dejar elegir cualquiera |
| Un bot ajeno responde **404** (`BOT_NOT_FOUND`) | No revela qué IDs existen | 403 |
| `GET /api/bots` sin `account_id` devuelve los bots del usuario; `?mine=true` hace lo mismo para admin | Una sola petición desde el front (antes una por cuenta) | `useBotsByAccountsQuery` con N peticiones |
| `risk_pct` ≤ 0.01 validado en el backend (`Bot.is_valid_risk_pct`) | Regla de negocio del 1 %; antes solo la validaba el front | Aceptar hasta 100 % |
| El nombre se puede cambiar en cualquier estado; modo y riesgo solo con el bot `stopped` | Renombrar no afecta la operación | Exigir `stopped` para todo |
| `feature_set_id` es **por bot**, no global (migración `m07b`) | Cada bot usa su propio conjunto; se pasa al `AnalyzeService` | Un feature set global |
| Máquina de estados en la **entidad de dominio** (`stopped` / `running` / `paused` / `error`) | Las transiciones viven en un solo sitio y se testean sin BD | Validar transiciones en las rutas |
| Un bot nuevo siempre nace `stopped` (el asistente lo inicia después si se marca "Iniciarlo al crear") | Crear y operar son pasos distintos en la API | Crear ya activo |
| `paused` **sí** es activo (`is_active() = True`) | Sigue con datos al día y puede generar señales | Pausa = inactivo |
| Las señales rechazadas **también se persisten** con `approved=False` (acción `hold`) | Trazabilidad completa y base para medir el edge | Descartarlas |
| `features_hash`: SHA-256 del contexto de mercado | Huella para auditar con qué datos se generó cada señal | Guardar el snapshot completo |
| Servicio, modelo y latencia de la IA en **columnas propias** (`llm_provider`, `llm_model`, `llm_latency_ms`), además de `reasons.llm` | Con el pool rotativo cada señal la puede responder un servicio distinto; en columnas se puede filtrar y agregar por servicio sin leer JSON | Solo dentro de `reasons` (JSON) o reutilizar `model_version` (pensada para los modelos ML) |
| Dirección buy/sell inferida: `entry > stop_loss` → buy; `entry < stop_loss` → sell | La señal no necesita un campo de dirección aparte | Pedirle la dirección al LLM |
| `GenerateSignalService` invoca [M6](M06-AI-AGENT.md) vía `_build_analyze_service()` con repos propios y *prestados* | Reutiliza el agente sin duplicar su cableado | Llamar a `/api/agent/analyze` por HTTP |
| Hook de alertas post-commit, siempre en `try/except` ([M9](M09-ALERTS.md)) | Una alerta nunca debe abortar el flujo de trading | Alertas dentro de la transacción |

## Avance

| Métrica | Valor | Evidencia |
|---|---|---|
| Alcance original | **100 %** (11/11) | CRUD, estados, señales, trazabilidad, nombre, propiedad, validaciones, UI y 55 tests |
| Madurez | **≈ 75 %** | Funcionalidad 85 · Tests 75 · Seguridad 90 · Operación 50 |

- **Funcionalidad (85):** flujo guiado de punta a punta (asistente → iniciar → analizar). Las señales siguen generándose **solo a mano** ("Analizar ahora" / `POST /api/signals/generate`).
- **Tests (75):** 55 tests (entidad, transiciones, generación); sin tests de propiedad, de las nuevas validaciones de creación ni de REST.
- **Seguridad (90):** propiedad en todas las rutas; validación de referencias y de la regla del 1 % en el backend.
- **Operación (50):** sin ejecución periódica de señales ni paso automático señal → orden.

## Posibles mejoras

| Prioridad | Mejora | Esfuerzo |
|---|---|---|
| Alta | **Generación automática de señales:** que el scheduler llame a `generate_signal` para cada bot `running` cuando cierra una vela nueva (hoy es manual) | M |
| Alta | **Puente señal → orden:** crear la orden de [M8](M08-ORDERS-EXECUTION.md) a partir de una señal aprobada | M |
| Alta | Evitar señales duplicadas por vela (idempotencia por `bot_id` + `ts`) | S |
| Media | Tests de propiedad (usuario vs admin), de `CreateBotService` (validaciones) y de rutas REST | S |
| Media | *Kill switch* / límites de riesgo por bot (pérdida diaria máxima, nº de operaciones) y paso automático a `error` ante fallos repetidos | M |
| Media | `risk_params.risk_pct` del bot no se usa al dimensionar (el agente usa el de la estrategia); unificar | S |
| Media | Resumen por agente en la tarjeta (PnL, nº de operaciones, win rate) | M |
| Baja | Paginación y filtros por fecha/acción en el listado de señales | S |
| Baja | Duplicar un agente desde el detalle | S |

## Fuera de alcance y pendientes conocidos

- Ejecución autónoma de bots (generar señal + operar sin intervención).
- Editar símbolo, estrategia, cuenta o conjunto de un agente ya creado (se crea otro).
- Tabla `predictions` (diferida desde [M6](M06-AI-AGENT.md); sin modelo ORM todavía).
- Tabla `portfolio_snapshots` (por bot; sin modelo ORM todavía).

## Detalle técnico

### Tablas en BD
| Tabla | Acción | Nota |
|-------|--------|------|
| `bots` | WRITE | CRUD + state machine (stopped/running/paused/error); `name VARCHAR(80) NOT NULL` |
| `signals` | WRITE | Señales generadas por bot (buy/sell/hold + precios + servicio/modelo/latencia de la IA) |
| `strategies` | READ | Validar al crear y construir AnalyzeService (M5) |
| `accounts` | READ | Propiedad, estado y modo; capital (M4) |
| `account_balances` | READ | Balance más reciente (M4) |
| `candles` | READ | Última vela (M2) |
| `candle_features` | READ | Features del feature_set del bot (M3) |
| `feature_sets` | READ | Validar existencia y compatibilidad (M3) |
| `symbols` | READ | Validar que exista y esté activo (M2) |
| `timeframes` | READ | Validar (M2) |

### Modelos ORM (`app/modules/bots/infrastructure/`)
| Archivo | Clase ORM | Tabla |
|---------|-----------|-------|
| `bot_model.py` | `BotModel` | `bots` |
| `signal_model.py` | `SignalModel` | `signals` |

Registrados en: `app/extensions/db/models_registry.py`

### Migraciones
- Columnas de precio en `signals` y `bots.feature_set_id`: en la migración inicial de Alembic.
- `bots.name`: revisión `m07 add name to bots` (columna nullable → backfill `CONCAT('Agente #', id)` → NOT NULL).
- `signals.llm_provider VARCHAR(32)`, `llm_model VARCHAR(128)`, `llm_latency_ms INT` (nullable, después de `features_hash`): revisión `a4e81c5d27f9` `m07 signals llm provider model latency`, escrita a mano.

### Repositorios
| Domain (interfaz) | Infrastructure (impl) |
|-------------------|-----------------------|
| `domain/bot_repository.py` | `infrastructure/bot_repository_impl.py` → `SqlAlchemyBotRepository` (incluye `list_by_account_ids`) |
| `domain/signal_repository.py` | `infrastructure/signal_repository_impl.py` → `SqlAlchemySignalRepository` |

### Servicios (`app/modules/bots/services/`)
| Subdir | Servicios |
|--------|-----------|
| `bots/` | `list_bots_service.py`, `get_bot_service.py`, `create_bot_service.py`, `update_bot_service.py`, `update_bot_status_service.py`, `bot_access.py` (`find_accessible_bot`: regla de propiedad compartida) |
| `signals/` | `list_signals_service.py`, `generate_signal_service.py` |

Todos los servicios que reciben un `bot_id` aceptan `owner_id` (`None` = admin, sin restricción).

Provider: `app/modules/bots/providers/bot_provider.py` → `BotServiceFactory`
- Repos propios: `SqlAlchemyBotRepository`, `SqlAlchemySignalRepository`
- Repos borrowed: M2 (candle/symbol/timeframe), M3 (feature_set/candle_feature), M4 (account/balance), M5 (strategy)
- `_build_analyze_service()` instancia M6 AnalyzeService con todos sus deps

### Endpoints REST
| Método | Ruta | Auth | Nota |
|--------|------|------|------|
| GET | `/api/bots` | token | Usuario: sus bots (opcional `account_id` propio). Admin: todos, por `account_id`, o los suyos con `?mine=true` |
| POST | `/api/bots` | token | Crea bot (`name` obligatorio; siempre inicia en stopped) |
| GET | `/api/bots/{id}` | token | Detalle (404 si no es del usuario) |
| PUT | `/api/bots/{id}` | token | `name` en cualquier estado; `mode`/`risk_params` solo si stopped |
| POST | `/api/bots/{id}/start` | token | Transición → running |
| POST | `/api/bots/{id}/pause` | token | Transición → paused |
| POST | `/api/bots/{id}/stop` | token | Transición → stopped |
| GET | `/api/signals` | token | Lista señales (requiere `?bot_id=`; 404 si el bot no es del usuario) |
| POST | `/api/signals/generate` | token | Genera señal invocando M6 ("Analizar ahora") |

`owner_scope(identity)` (en `rest/bots/routes.py`) devuelve el `user_id` o `None` para admin; lo reutiliza `rest/signals/routes.py`.

Routers registrados en `app/app_factory.py` (dentro de `api_routers`, con `prefix=settings.API_PREFIX`).

### Frontend (`frontend/src/modules/bots/`)
| Ruta | Archivo de ruta | Página / componentes |
|-----|----------|----|
| `/#/agents` | `routes/_app/agents/index.lazy.tsx` | `pages/agents.tsx` + `components/agent-card.tsx` + `components/agents-empty-state.tsx` |
| `/#/agents/new` | `routes/_app/agents/new.lazy.tsx` | `pages/agent-new.tsx` + `components/agent-wizard/{choice-card,symbol-step,strategy-step,account-step}.tsx` + `shared/components/stepper.tsx` |
| `/#/agents/:id` | `routes/_app/agents/$agentId.lazy.tsx` | `pages/agent-detail.tsx` + `components/{agent-controls,analyze-now-button,signals-table,signal-detail-sheet}.tsx` |
| `/#/admin/agents` | `routes/_app/admin/agents.lazy.tsx` | `pages/admin-agents.tsx` + `components/bot-actions-menu.tsx` |
| `/#/bots`, `/#/admin/bots`, `/#/agent` | `routes/_app/{bots,agent}.tsx`, `routes/_app/admin/bots.tsx` | Redirecciones (`beforeLoad` + `redirect`) |

- API: `api/bots.api.ts` (`listBots({account_id, mine})`, `getBot`, `createBot`, `updateBot`, transiciones, `listSignals`, `generateSignal`).
- Queries: `useBotsQuery`, `useMyBotsQuery` (`?mine=true`), `useBotQuery`, `useSignalsQuery`. Mutations: create, update, transition, generate signal. `hooks/use-bot-transition.ts` centraliza las transiciones con sus toasts.
- `lib/agent-wizard.ts`: compatibilidad estrategia ↔ conjunto (mismo criterio que `rule_keys` del backend), conjunto recomendado, timeframe y riesgo de la estrategia, nombre sugerido.
- `lib/bots-labels.ts`: `describeBot(bot)` = nombre; `describeBotMarket(bot, catalogs)` = `BTC/USDT · 1h`.

### Corrección de rutas

> Los routers declaran `prefix="/bots"` y `prefix="/signals"` y `app_factory.py` les añade `/api`. En el front se escriben sin `/api`.

## Gotchas críticos

- **Perpetuos solo en paper:** `CreateBotService` y `UpdateBotService` (al pasar a live) devuelven `BOT_PERPETUAL_LIVE_NOT_SUPPORTED` (422) si el símbolo es un perpetuo (`XAU/USDT:USDT`, `is_perpetual()` de M2). El asistente oculta las cuentas live con un perpetuo elegido y acepta `?symbol_id=` (desde Explorar mercados).
- **Seed `bots`:** dos agentes demo en paper y detenidos para el usuario demo ("Oro — tendencia 4h" con Tendencia Metales y "BTC — tendencia 1h" con EMA Trend Follower, conjunto Tendencia), idempotente por (account_id, name).

- `ServiceResult` almacena el error en `result.error.code` (NO `result.code`).
- `feature_set_id` es por bot, NO global. El bot pasa su propio `feature_set_id` al AnalyzeService.
- El bot `paused` ES activo (`is_active() = True`).
- Señales rechazadas siempre se persisten con `approved=False`.
- Dirección buy/sell se infiere: `entry > stop_loss` → buy; `entry < stop_loss` → sell.
- **Admin y `GET /api/bots`:** sin filtros recibe **todos** los bots del sistema. En pantallas de usuario usar `useMyBotsQuery` (`?mine=true`), nunca `useBotsQuery()` a secas.
- **Compatibilidad en dos lados:** el front filtra conjuntos con `isFeatureSetCompatible` y el backend valida con `indicator_catalog.is_compatible`. Si cambia el formato de las reglas, actualizar ambos.
- **`llm_*` en NULL:** las señales rechazadas por régimen o reglas no consultan a la IA, y las anteriores al 2026-10-19 no lo tienen; el detalle oculta "Consulta a la IA" si `llm_provider` es `null`. `model_version` sigue sin usarse (reservada a modelos ML).
- **Decimales como `float`:** `_signal_to_dict` serializa precios y `confidence` con `float(...)`; el front los tipa como `number`.

## Tests

- `tests/bots/test_bot_entity.py` — 22 tests (máquina de estados, is_active, risk_params)
- `tests/bots/test_update_bot_status_service.py` — 16 tests (transiciones, timestamps, repo.commit)
- `tests/bots/test_generate_signal_service.py` — 17 tests (validaciones, dirección, campos)
- Total: 55 tests unitarios. **Huecos:** propiedad, validaciones de `CreateBotService`, rutas REST, hook de alertas.

## Riesgos

- Una señal generada con velas/features desactualizados (scheduler apagado o fetch fallido) puede llevar a operar con datos viejos.
- Sin idempotencia por vela, "Analizar ahora" repetido crea señales duplicadas.

## Historial

- **2026-03** — Módulo completado: CRUD de bots con máquina de estados, `GenerateSignalService`, UI `/bots` y `/admin/bots`, 55 tests.
- **Posterior** — Hook post-commit de alertas ([M9](M09-ALERTS.md)).
- **2026-10-08** — API headless (/api), páginas migradas a React (frontend/).
- **2026-10-08** — **Agentes:** los bots pasan a llamarse agentes en la UI y son el punto de entrada (dashboard, asistente, detalle). Nombre (`bots.name`), propiedad en todas las rutas, validaciones de creación, regla del 1 % en el backend, `?mine=true`. La página "Agente de IA" se integra como "Analizar ahora".
- **2026-10-10** — Perpetuos TradFi bloqueados en live; `?symbol_id=` en `/agents/new`; seed `bots` con dos agentes demo.
- **2026-10-19** — Cada señal guarda servicio, modelo y latencia de la IA (`signals.llm_*`); sección "Consulta a la IA" en `signal-detail-sheet.tsx` (`llmProviderLabel`, `formatLatency` en `bots-labels.ts`).
