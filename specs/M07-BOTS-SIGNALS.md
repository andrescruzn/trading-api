# Módulo 7 — Bots & Signals (Agentes y Señales) ✅ COMPLETO

← [Índice de módulos](_ROOT.md)

## Ficha

| Campo | Valor |
|---|---|
| Estado | ✅ Completo |
| Avance (alcance original) | 100 % — 11/11 entregables (+ 6 del modo de ejecución, 2026-10-19; + 1 de señales compartidas, 2026-10-20) |
| Madurez (estimada) | 81 % — ver [Avance](#avance) |
| Tablas | `bots`, `signals`, `signal_subscriptions` (R/W); `users` (R: `telegram_chat_id`); `strategies`, `accounts`, `account_balances`, `candles`, `candle_features`, `feature_sets`, `symbols`, `timeframes` (R) |
| Depende de | [M2](M02-MARKET-DATA.md), [M3](M03-FEATURE-ENGINEERING.md), [M4](M04-ACCOUNTS-PORTFOLIO.md), [M5](M05-STRATEGIES.md), [M6](M06-AI-AGENT.md); [M9](M09-ALERTS.md) (aviso por Telegram de señales pendientes y de señales compartidas) |
| Lo usan | [M8](M08-ORDERS-EXECUTION.md) (órdenes por bot, ejecución de señales), [M9](M09-ALERTS.md) (hooks de señal/error), [M11](M11-FUND.md) (capital del agente del fondo vía `FundCapitalPort`), scheduler de [M2](M02-MARKET-DATA.md) (señales automáticas), dashboard de [M1](M01-AUTH.md) |
| Prefijo API | `/api/bots`, `/api/signals` (ver [corrección de rutas](#corrección-de-rutas)) |
| Frontend | `frontend/src/modules/bots` |
| Última revisión | 2026-10-26 |

## Descripción

**En palabras simples:** Es el piloto automático y el **punto de entrada de la app**. En la interfaz los bots se llaman **agentes**: un agente vigila un símbolo, aplica una estrategia y le pide a la IA que confirme cada operación. Cada agente tiene un **modo de ejecución** que decide qué pasa cuando la IA aprueba: **Manual** (tú decides todo), **Con aprobación** (te pide confirmación en la app o en Telegram) o **Automático** (envía la orden solo).

**Qué hace:**
- Crea **agentes** (tabla `bots`) con nombre + cuenta + símbolo + estrategia + conjunto de indicadores + parámetros de riesgo + modo de ejecución.
- Valida al crear: que existan las referencias, que la cuenta sea del usuario y esté activa, que el modo coincida con el de la cuenta, que en live el símbolo sea del mismo exchange que la cuenta, que el conjunto de indicadores cubra las reglas de la estrategia, la regla del 1 % y las reglas del modo de ejecución.
- Los agentes se activan (`start`), pausan (`pause`) y detienen (`stop`) con una máquina de estados.
- Un usuario solo ve y opera **sus** agentes (propiedad por cuenta); el admin ve todos.
- **Manual:** la señal se genera con "Analizar ahora" y la orden la crea la persona.
- **Con aprobación / Automático:** el scheduler genera una señal por **vela cerrada**. Si la IA aprueba una BUY/SELL, la señal queda **pendiente** hasta su vencimiento (`expires_at`): en Con aprobación se avisa por Telegram y se aprueba o descarta desde la app o Telegram; en Automático se ejecuta en el acto ([M8](M08-ORDERS-EXECUTION.md)).
- Señales APROBADAS: BUY o SELL + entry, SL, TP, position_size, rr_ratio. RECHAZADAS: HOLD, `approved=False`; todas persisten.
- El agente le pasa a la IA **su** riesgo (`risk_params.risk_pct`, acotado al 1 %), no el de la estrategia.
- **Fondo común (2026-10-23, [M11](M11-FUND.md)):** si el agente está en el fondo, el 1 % se calcula sobre **su** capital (`FundCapitalPort`, `bots/domain/fund_capital_port.py`, inyectado en `GenerateSignalService` como `fund_capital`; `AnalyzeService.analyze(capital=…)`). Un agente sobre la billetera de la plataforma sin pool no genera señales (`AGENT_NO_FUND_CAPITAL`).
- `features_hash`: SHA-256 del contexto de mercado, fingerprint para auditoría.
- **Señales compartidas:** el dueño de un agente puede activar **Compartir señales**; cualquier otro usuario lo ve en Track record y lo sigue. Quien lo sigue recibe por Telegram sus BUY/SELL aprobadas (acción, símbolo, timeframe, entrada, SL, TP, R/R), sin datos de la cuenta ni del dueño y sin botones: no ejecuta nada.
- Cada señal guarda qué servicio de IA respondió (`llm_provider`), con qué modelo (`llm_model`) y cuánto tardó (`llm_latency_ms`), y su **decisión de ejecución** (estado, canal, quién, cuándo y por qué falló).

## Páginas

Hash routing: la URL real es `/#/<ruta>`.

**Páginas — Usuario (cualquier usuario autenticado):**
- `/#/dashboard` ([M1](M01-AUTH.md)) — **Inicio = lista de agentes** (desde 2026-10-20; `/#/agents` redirige aquí): tarjetas con estado (punto que late si está activo), símbolo · timeframe, precio (último cierre, variación frente a la vela anterior y régimen), estrategia, última señal y botones Iniciar/Reanudar/Pausar. Filtro Todos / Activos / Detenidos. Sin agentes: bienvenida que explica qué es un agente.
- `/#/agents/new` — **Asistente de creación** en 4 pasos: (1) qué operar (solo símbolos con velas automáticas), (2) cómo opera (estrategia + conjunto de indicadores compatible, con el recomendado preseleccionado), (3) con qué dinero (cuentas propias con su saldo; crea una cuenta de práctica en línea si no hay), (4) revisar: nombre sugerido editable, riesgo de la estrategia en solo lectura, **"Cuando la IA aprueba una operación"** (selector Manual / Con aprobación / Automático, Manual por defecto; aviso en rojo si es Automático con cuenta live), "Iniciarlo al crear".
- `/#/agents/:id` — **Detalle**: nombre editable, badge del modo de ejecución, controles, **Analizar ahora** (genera una señal y abre su detalle), aviso "Preparando datos" hasta que hay indicadores, pestañas Señales (columna **Ejecución**) · Órdenes (con Nueva orden) · Posiciones (+ ejecuciones) · **Mercado** (gráfico del precio de cierre con líneas de Entrada, SL y TP de la posición abierta —recorrible con el cursor o las flechas—, velas e indicadores del símbolo y timeframe del agente, con selector de cantidad y botón **Actualizar datos**, que descarga velas y recalcula indicadores también con el agente detenido; si no hay datos dice si se están preparando o cómo conseguirlos) · Configuración (tarjeta "Cuando la IA aprueba una operación" para cambiar el modo en cualquier estado —Automático pide confirmación—; en Con aprobación incluye **Minutos para aprobar**, 1–1440, vacío = valor por defecto del servidor; tarjeta **Compartir señales** con una casilla —en cualquier estado— que explica qué ven los demás y cuántas personas lo siguen; reglas e indicadores explicados). El detalle de una señal pendiente muestra **Aprobar** / **Descartar** con la cuenta atrás ("Vence en 45 min") y, en live, una confirmación extra.
- `/#/dashboard` ([M1](M01-AUTH.md)) — tarjeta **Señales por aprobar** (solo si hay alguna): agente, acción, precios, R/R y botones Aprobar/Descartar; se refresca cada 30 s.
- `/#/track-record` ([M8](M08-ORDERS-EXECUTION.md)) — sección **Agentes que comparten sus señales** (`SharedAgentsSection`): estrategia, símbolo · timeframe, modo, estado y cuántos lo siguen, con **Suscribirme** / **Dejar de seguir**; los propios muestran "Es tuyo". Sin Telegram conectado, un aviso y el botón **Conectar Telegram** abren el diálogo de vínculo (también está en el menú de usuario).
- `/#/agents`, `/#/bots` y `/#/agent` redirigen a `/#/dashboard`. La miga del detalle y del asistente es "Inicio".

**Páginas — Administrador (solo admin):**

## Entregables

Tablas: `bots`, `signals`

Entregables:
- ✅ Bot = nombre + cuenta + símbolo + estrategia + feature_set + parámetros de riesgo
- ✅ CRUD bots (start/pause/stop) con máquina de estados en domain entity
- ✅ Cada bot tiene su propio `feature_set_id` (migración m07b)
- ✅ Señales: BUY / SELL / HOLD con entry, SL, TP, position_size, rr_ratio (migración m07a)
- ✅ Señales rechazadas persisten con approved=False (trazabilidad completa)
- ✅ features_hash: SHA-256 del snapshot de features para auditoría
- ✅ Web UI en React: lista de agentes (en el inicio), asistente, detalle y vista admin
- ✅ 55 tests unitarios pasando (bot entity, status transitions, signal generation)
- ✅ **Agentes con nombre** (`bots.name`, migración `m07 add name to bots`)
- ✅ **Propiedad** en todas las rutas de bots y señales (404 para bots ajenos)
- ✅ **Servicio, modelo y latencia de la IA** por señal (`signals.llm_provider`, `llm_model`, `llm_latency_ms`; migración `m07 signals llm provider model latency`), visibles en el detalle de la señal
- ✅ **Validaciones al crear** (referencias, cuenta propia y activa, modo = cuenta, compatibilidad estrategia/indicadores, regla del 1 %)
- ✅ (2026-10-19) **Modo de ejecución** por agente: `bots.execution_mode` (`manual` | `approval` | `auto`) + `approval_ttl_minutes`, reglas en `execution_mode_rules.py`
- ✅ (2026-10-19) **Decisión de ejecución** por señal (`decision_status`, `expires_at`, `decided_at`, `decided_by_user_id`, `decision_channel`, `decision_reason`) con transición atómica
- ✅ (2026-10-19) **Señales automáticas por vela cerrada** en el scheduler (`app/modules/scheduler/execution_cycle.py`), una por vela (`candle_ts` + UNIQUE)
- ✅ (2026-10-19) **Cola de pendientes** `GET /api/signals/pending` (`ListPendingSignalsService`)
- ✅ (2026-10-19) **Riesgo del agente** (`effective_risk_pct`, acotado al 1 %) en el análisis
- ✅ (2026-10-20) **Señales compartidas**: `bots.share_signals` + tabla `signal_subscriptions`, `GET /api/bots/shared`, `POST`/`DELETE /api/bots/{id}/subscription`, hook `notify_subscribers` → `SharedSignalNotifier` ([M9](M09-ALERTS.md)), tarjeta en Configuración y sección en Track record, 31 tests
- ✅ (2026-10-19) UI: selector de modo (asistente + Configuración), badges de modo y de decisión, Aprobar/Descartar en el detalle de la señal y tarjeta de pendientes en el dashboard

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
| El agente pasa a la IA `effective_risk_pct` (su `risk_pct` acotado a `MAX_RISK_PCT`; inválido o ≤ 0 → 1 %) | Antes la IA usaba el `risk_pct` de la estrategia y el del agente se ignoraba | Mantener el de la estrategia |
| El nombre y el **modo de ejecución** se pueden cambiar en cualquier estado; modo paper/live y riesgo solo con el bot `stopped` | Renombrar no afecta la operación; pasar de Automático a Con aprobación es un freno que no debe esperar a detener el agente | Exigir `stopped` para todo |
| Pasar el agente a otro modo paper/live exige una cuenta de ese modo (`BOT_MODE_ACCOUNT_MISMATCH`), igual que al crear | Antes `PUT` permitía un agente live sobre una cuenta paper (o al revés) | Validarlo solo al crear |
| En **live**, `symbol.exchange_id` debe ser igual a `account.exchange_id` (`BOT_EXCHANGE_ACCOUNT_MISMATCH` 422) al crear y al pasar a live; el asistente oculta las cuentas live de otro exchange y explica por qué. En paper no aplica (2026-10-26) | `LiveExecutor` manda la orden al exchange de la cuenta con el texto del par (`BTC/USDT`): con velas de Kraken y la billetera en Binance, entry/SL/TP saldrían de otro mercado, y si el par no existe allí la orden falla | Mapear el símbolo al exchange de la cuenta por nombre · validarlo solo al enviar la orden |
| **Tres modos de ejecución** (`manual` por defecto, `approval`, `auto`) en una columna del bot | La persona decide cuánta autonomía da a cada agente; los agentes existentes siguen como antes | Un interruptor "automático sí/no" |
| `auto` + live solo con `TRADING_LIVE_AUTO_ENABLED=true` (`BOT_AUTO_LIVE_DISABLED`) | Órdenes con dinero real sin una persona en medio es decisión del administrador | Permitirlo a cualquier usuario |
| Modos automáticos solo con timeframe ≥ `SIGNALS_AUTO_MIN_TIMEFRAME_SECONDS` (900 s = 15m) (`BOT_TIMEFRAME_TOO_SHORT_FOR_AUTOMATION`) | Un análisis de IA por vela de 1m dispararía el coste | Sin mínimo |
| Las señales automáticas usan la **última vela cerrada** (`AnalyzeService(as_of=candle_ts)`) | No decidir con una vela en formación, que todavía cambia | Analizar la última vela, cerrada o no |
| Una señal automática por vela: `signals.candle_ts` + `UNIQUE (bot_id, candle_ts)`; las manuales tienen `candle_ts = NULL` y no chocan | Idempotencia aunque dos ciclos coincidan; el `IntegrityError` se trata como "ya existe" | Comprobar solo en Python |
| La señal aprobada BUY/SELL de un agente `approval`/`auto` nace `pending` con `expires_at = ts + approval_ttl_minutes` (o `SIGNAL_APPROVAL_TTL_MINUTES` = 60) | Una señal vieja no debe ejecutarse tarde; la persona sabe cuánto tiene para decidir | Pendiente sin límite |
| `approval_ttl_minutes` entre 1 y 1440 (CHECK + Pydantic); `NULL` = valor global | Configurable por agente sin obligar a fijarlo | Solo valor global |
| Estados de decisión `not_required` → `pending` → `executing` → `executed` / `failed`, o `pending` → `rejected` / `expired` | Distinguir "nadie decidió" de "se aprobó pero no se pudo ejecutar" | Reutilizar `approved` |
| `SignalRepository.transition_decision` = **UPDATE condicional** (`WHERE decision_status IN from_statuses`) que devuelve si cambió la fila | Si la app y Telegram deciden a la vez, solo una decisión gana | Leer, comprobar y escribir (carrera) |
| `decision_reason` guarda el **código** del fallo; la API añade `decision_reason_message` con el texto de `SIGNAL_DECISION_ERROR_MESSAGES` ([M8](M08-ORDERS-EXECUTION.md)) | Los textos de UI viven en el backend | Traducir códigos en el front |
| El aviso por Telegram es un **hook** (`notify_pending`) post-commit, solo en modo `approval`, en `try/except` con log | Un fallo de Telegram no frena la señal; la señal aparece igual en la app | Enviar dentro de la transacción |
| Tope diario de análisis automáticos por usuario (`AGENT_MAX_AUTO_ANALYSES_PER_DAY` = 96) | Coste de la IA acotado aunque haya muchos agentes | Sin tope |
| `feature_set_id` es **por bot**, no global (migración `m07b`) | Cada bot usa su propio conjunto; se pasa al `AnalyzeService` | Un feature set global |
| Máquina de estados en la **entidad de dominio** (`stopped` / `running` / `paused` / `error`) | Las transiciones viven en un solo sitio y se testean sin BD | Validar transiciones en las rutas |
| Un bot nuevo siempre nace `stopped` (el asistente lo inicia después si se marca "Iniciarlo al crear") | Crear y operar son pasos distintos en la API | Crear ya activo |
| `paused` **sí** es activo (`is_active() = True`); las señales automáticas solo se generan con `running` | Pausado sigue con datos al día y se puede analizar a mano, pero no busca entradas solo | Pausa = inactivo |
| Las señales rechazadas **también se persisten** con `approved=False` (acción `hold`) | Trazabilidad completa y base para medir el edge | Descartarlas |
| `features_hash`: SHA-256 del contexto de mercado | Huella para auditar con qué datos se generó cada señal | Guardar el snapshot completo |
| Servicio, modelo y latencia de la IA en **columnas propias** (`llm_provider`, `llm_model`, `llm_latency_ms`), además de `reasons.llm` | Con el pool rotativo cada señal la puede responder un servicio distinto; en columnas se puede filtrar y agregar por servicio sin leer JSON | Solo dentro de `reasons` (JSON) o reutilizar `model_version` (pensada para los modelos ML) |
| Dirección buy/sell inferida: `entry > stop_loss` → buy; `entry < stop_loss` → sell | La señal no necesita un campo de dirección aparte | Pedirle la dirección al LLM |
| `GenerateSignalService` invoca [M6](M06-AI-AGENT.md) vía `_build_analyze_service()` con repos propios y *prestados* | Reutiliza el agente sin duplicar su cableado | Llamar a `/api/agent/analyze` por HTTP |
| Hook de alertas post-commit, siempre en `try/except` ([M9](M09-ALERTS.md)) | Una alerta nunca debe abortar el flujo de trading | Alertas dentro de la transacción |
| **Compartir señales** = `bots.share_signals` (por agente, lo cambia quien puede editar el agente, en cualquier estado) + tabla `signal_subscriptions` (UNIQUE `bot_id, user_id`, `ON DELETE CASCADE`) | El dueño decide qué agente expone; compartir no toca la operación | Compartir todos los agentes del usuario |
| Quien sigue recibe **solo BUY/SELL aprobadas** por Telegram, sin botones ni tamaño de posición, cuenta o nombre del agente; el dueño nunca recibe este aviso | No ejecuta nada; el tamaño revela el capital y el nombre puede identificar al dueño | Copiar la orden en la cuenta del suscriptor (copy trading) |
| `GET /bots/shared` muestra estrategia, símbolo, timeframe, modo, estado y nº de suscriptores (+ `is_subscribed`, `is_mine`); nunca nombre, cuenta ni dueño | Se elige un agente por lo que hace, no por quién es | Mostrar nombre y dueño |
| Seguir un agente privado o inexistente → `BOT_NOT_FOUND` (404) | No revela qué agentes privados existen | 403 |
| Seguir **exige Telegram vinculado** (`SUBSCRIPTION_TELEGRAM_REQUIRED` 422) y no se puede seguir uno propio (`SUBSCRIPTION_OWN_BOT` 422) | Telegram es el único canal de envío; los propios ya se ven en la app | Guardar la suscripción y avisar "cuando conectes" |
| Suscribirse y dejar de seguir son **idempotentes** (200 con `{bot_id, is_subscribed, subscribers_count}`) | Un doble clic o una pestaña vieja no es un error para la persona | 409 `SUBSCRIPTION_EXISTS` |
| Al **apagar** Compartir señales las suscripciones **se conservan**: el hook no envía nada (mira `share_signals`) y el agente sale del listado; si se vuelve a compartir, siguen recibiendo. Dejar de seguir funciona aunque ya no se comparta | Un apagado por error no hace perder a quienes lo seguían | Borrar las suscripciones al apagar |
| Hook `notify_subscribers` post-commit en `GenerateSignalService`, en `try/except`, solo si `share_signals` y la señal `is_actionable()` (manual, Con aprobación o Automático por igual) | Igual que las alertas: un fallo de Telegram no frena la señal | Enviar dentro de la transacción |
| `read_scope(identity)` / `write_scope(identity)` (antes `owner_scope`) viven en `app/common/security/jwt/role_guard.py` (antes en `rest/bots/routes.py`); desde 2026-10-22 crear, editar, iniciar/pausar/detener, "Actualizar datos" y "Analizar ahora" exigen super admin | Lo usan bots, signals, orders, agent y alerts | Copiarlo en cada router |

## Avance

| Métrica | Valor | Evidencia |
|---|---|---|
| Alcance original | **100 %** (11/11) | CRUD, estados, señales, trazabilidad, nombre, propiedad, validaciones, UI y 55 tests. Además, 6 entregables del modo de ejecución (2026-10-19) |
| Madurez | **≈ 81 %** | Funcionalidad 95 · Tests 65 · Seguridad 90 · Operación 75 |

- **Funcionalidad (95):** flujo guiado de punta a punta y tres modos de ejecución; señales automáticas por vela cerrada, aprobación en app o Telegram, ejecución automática. Falta el resumen por agente (PnL, win rate).
- **Tests (65):** los 55 tests siguen (solo se ajustó la llamada a `analyze` en `test_generate_signal_service.py`), pero **nada nuevo está cubierto**: `execution_mode_rules`, `pending`/`expires_at` en `GenerateSignalService`, `transition_decision`, `ListPendingSignalsService`, el ciclo del scheduler y la UI.
- **Seguridad (90):** propiedad en todas las rutas (también en `/signals/pending` y al aprobar); UPDATE condicional para la decisión; `auto` + live apagado por defecto; rate limit por usuario en `POST /api/signals/generate` ([M6](M06-AI-AGENT.md)) y en `POST /api/bots/{id}/market/sync`; `risk_params` con máximo 20 claves.
- **Operación (75):** el scheduler (proceso líder) genera, caduca y ejecuta solo, con tope diario por usuario, timeframe mínimo y descarte de datos viejos; todo configurable por entorno. Sin métricas del ciclo ni avisos cuando un agente automático falla seguido.

## Posibles mejoras

| Prioridad | Mejora | Esfuerzo |
|---|---|---|
| Alta | Tests de `execution_mode_rules`, `GenerateSignalService` con `candle_ts`/pending/hook, `SqlAlchemySignalRepository.transition_decision`/`expire_pending` (con BD), `ListPendingSignalsService` y `execution_cycle` (`_closed_candle_to_analyze`) | M |
| Media | Tests de propiedad (usuario vs admin), de `CreateBotService` / `UpdateBotService` (validaciones) y de rutas REST | S |
| Media | Pasar a `error` (o volver a Con aprobación) un agente Automático tras N fallos seguidos de ejecución, y avisarlo | M |
| Media | Pérdida diaria máxima y nº máximo de operaciones por agente (el drawdown total ya existe en el RiskGate de [M8](M08-ORDERS-EXECUTION.md)) | M |
| Media | Resumen por agente en la tarjeta (PnL, nº de operaciones, win rate) | M |
| Media | El tope diario cuenta **todas** las señales del día de los agentes del usuario (también las de "Analizar ahora"); separarlas si hace falta | S |
| Baja | Paginación y filtros por fecha/acción/decisión en el listado de señales | S |
| Baja | Duplicar un agente desde el detalle | S |

## Fuera de alcance y pendientes conocidos

- Editar símbolo, estrategia, cuenta o conjunto de un agente ya creado (se crea otro).
- Avisar por Telegram las señales que ejecuta un agente Automático (solo se avisa en Con aprobación; las alertas de [M9](M09-ALERTS.md) siguen disponibles).
- Tabla `predictions` (diferida desde [M6](M06-AI-AGENT.md); sin modelo ORM todavía).
- Tabla `portfolio_snapshots` (por bot; tiene modelo ORM en `accounts/infrastructure/portfolio_snapshot_model.py`, pero ningún servicio la escribe).

## Detalle técnico

### Tablas en BD
| Tabla | Acción | Nota |
|-------|--------|------|
| `bots` | WRITE | CRUD + state machine (stopped/running/paused/error); `name VARCHAR(80) NOT NULL`; `share_signals TINYINT(1) NOT NULL DEFAULT 0` (señales compartidas); `execution_mode VARCHAR(16) NOT NULL DEFAULT 'manual'` (CHECK `chk_bots_execution_mode`: manual \| approval \| auto); `approval_ttl_minutes INT NULL` (CHECK `chk_bots_approval_ttl`: NULL o 1–1440) |
| `signals` | WRITE | Señales generadas por bot (buy/sell/hold + precios + servicio/modelo/latencia de la IA). Decisión: `decision_status VARCHAR(16) NOT NULL DEFAULT 'not_required'` (CHECK: not_required \| pending \| executing \| executed \| rejected \| expired \| failed), `expires_at`, `decided_at` (`TIMESTAMP(6)`), `decided_by_user_id BIGINT` (FK `fk_signals_decided_by` → users; NULL = automático), `decision_channel VARCHAR(16)` (CHECK: app \| telegram \| auto), `decision_reason VARCHAR(64)`, `candle_ts TIMESTAMP(6)` + `UNIQUE uq_signals_bot_candle (bot_id, candle_ts)`, índice `idx_signals_decision_status (decision_status, expires_at)` |
| `signal_subscriptions` | WRITE | Quién sigue qué agente compartido: `id`, `bot_id` (FK `fk_signal_subscriptions_bot` → bots, CASCADE), `user_id` (FK `fk_signal_subscriptions_user` → users, CASCADE), `created_at TIMESTAMP(6)`; `UNIQUE uq_signal_subscriptions_bot_user (bot_id, user_id)`, índice `idx_signal_subscriptions_user` |
| `users` | READ | `telegram_chat_id` para exigir Telegram al suscribirse ([M1](M01-AUTH.md)) |
| `strategies` | READ | Validar al crear y construir AnalyzeService (M5) |
| `accounts` | READ | Propiedad, estado y modo; capital (M4) |
| `account_balances` | READ | Balance más reciente (M4) |
| `candles` | READ | Última vela (M2) y última vela cerrada (scheduler) |
| `candle_features` | READ | Features del feature_set del bot (M3) |
| `feature_sets` | READ | Validar existencia y compatibilidad (M3) |
| `symbols` | READ | Validar que exista y esté activo (M2) |
| `timeframes` | READ | Validar (M2); `seconds` para las reglas del modo de ejecución |

### Modelos ORM (`app/modules/bots/infrastructure/`)
| Archivo | Clase ORM | Tabla |
|---------|-----------|-------|
| `bot_model.py` | `BotModel` | `bots` |
| `signal_model.py` | `SignalModel` | `signals` |
| `signal_subscription_model.py` | `SignalSubscriptionModel` | `signal_subscriptions` |

Registrados en: `app/extensions/db/models_registry.py`

### Migraciones
- Columnas de precio en `signals` y `bots.feature_set_id`: en la migración inicial de Alembic.
- `bots.name`: revisión `m07 add name to bots` (columna nullable → backfill `CONCAT('Agente #', id)` → NOT NULL).
- `signals.llm_provider VARCHAR(32)`, `llm_model VARCHAR(128)`, `llm_latency_ms INT` (nullable, después de `features_hash`): revisión `a4e81c5d27f9` `m07 signals llm provider model latency`, escrita a mano.
- **Pendiente de generar** (lo hace el usuario con `alembic revision --autogenerate`): `bots.share_signals` (revisar que lleve `server_default 0`) y la tabla `signal_subscriptions`.
- `f51e2dad9c13` `m07 execution mode and signal decisions` (escrita a mano, con `AFTER` y los CHECK que autogenerate no detecta): columnas y CHECK de `bots` y `signals` de arriba; además `positions.stop_loss/take_profit/signal_id` ([M8](M08-ORDERS-EXECUTION.md)) y `users.telegram_chat_id/telegram_link_hash/telegram_link_expires_at` ([M1](M01-AUTH.md)). Los agentes existentes quedan en `manual`. `downgrade()` real.

### Dominio
- `Bot.VALID_EXECUTION_MODES`, `AUTOMATED_EXECUTION_MODES = ("approval", "auto")`, `is_valid_execution_mode()`, `is_automated()`, `effective_risk_pct`, `max_notional` (de `risk_params.max_notional`, > 0 o `None`).
- `Bot.share_signals` (bool, `False` por defecto). `SignalSubscription` (`domain/signal_subscription_entity.py`): `id`, `bot_id`, `user_id`, `created_at`.
- `Signal.VALID_DECISION_STATUSES`, `VALID_DECISION_CHANNELS`, `is_actionable()` (aprobada y BUY/SELL), `is_pending()`, `is_expired_at(now)`.

### Repositorios
| Domain (interfaz) | Infrastructure (impl) |
|-------------------|-----------------------|
| `domain/bot_repository.py` | `infrastructure/bot_repository_impl.py` → `SqlAlchemyBotRepository` (incluye `list_by_account_ids`) |
| `domain/signal_repository.py` | `infrastructure/signal_repository_impl.py` → `SqlAlchemySignalRepository` |
| `domain/signal_subscription_repository.py` | `infrastructure/signal_subscription_repository_impl.py` → `SqlAlchemySignalSubscriptionRepository` (`list_by_bot`, `list_bot_ids_by_user`, `count_by_bot_ids`, `exists`, `create`, `delete`) |

`BotRepository.list_shared()`: agentes con `share_signals = True`.

Nuevos en `SignalRepository`: `exists_for_candle(bot_id, candle_ts)`, `count_created_since(bot_ids, since)`, `list_by_decision_status(status, bot_ids=None, limit=100)` (máx. 500), `transition_decision(signal_id, from_statuses, to_status, **fields) -> bool`, `expire_pending(now) -> list[int]`.

### Servicios (`app/modules/bots/services/`)
| Subdir | Servicios |
|--------|-----------|
| `bots/` | `list_bots_service.py`, `get_bot_service.py`, `create_bot_service.py`, `update_bot_service.py`, `update_bot_status_service.py`, `bot_access.py` (`find_accessible_bot`: regla de propiedad compartida; `bot_owner_id`), `execution_mode_rules.py` (`check_execution_mode(bot, timeframe_seconds)`, compartida por crear y editar) |
| `signals/` | `list_signals_service.py`, `generate_signal_service.py` (`generate(bot_id, owner_id=None, candle_ts=None)`), `list_pending_signals_service.py` (`ListPendingSignalsService.list(owner_id, limit)` → `PendingSignal(signal, bot)`; excluye las vencidas que el scheduler aún no marcó) |
| `subscriptions/` | `list_shared_bots_service.py` (`ListSharedBotsService.list(user_id)` → `SharedBot`), `subscribe_to_bot_service.py` (`SubscribeToBotService.subscribe(bot_id, user_id)` → `SubscriptionState`), `unsubscribe_from_bot_service.py` (`UnsubscribeFromBotService.unsubscribe(bot_id, user_id)`) |

Todos los servicios que reciben un `bot_id` aceptan `owner_id` (`None` = admin o scheduler, sin restricción).

`check_execution_mode`: `BOT_INVALID_EXECUTION_MODE` · `BOT_INVALID_APPROVAL_TTL` · `BOT_AUTO_LIVE_DISABLED` · `BOT_TIMEFRAME_TOO_SHORT_FOR_AUTOMATION` (422). `UpdateBotService` lo vuelve a correr en cada `PUT` (con el timeframe del bot) y valida `BOT_MODE_ACCOUNT_MISMATCH` al cambiar `mode`; al pasar a live también `BOT_PERPETUAL_LIVE_NOT_SUPPORTED` y `BOT_EXCHANGE_ACCOUNT_MISMATCH` (meta `account_exchange_id`, `symbol_exchange_id`), igual que `CreateBotService`.

Provider: `app/modules/bots/providers/bot_provider.py` → `BotServiceFactory`
- Repos propios: `SqlAlchemyBotRepository`, `SqlAlchemySignalRepository`
- Repos borrowed: M2 (candle/symbol/timeframe), M3 (feature_set/candle_feature), M4 (account/balance), M5 (strategy)
- `_build_analyze_service()` instancia M6 AnalyzeService con todos sus deps (incluye `AGENT_MAX_ENTRY_ATR_DISTANCE`)
- `generate_signal()` inyecta `build_evaluate_alerts_service(session)`, `notify_pending=build_signal_approval_notifier(session).notify`, `notify_subscribers=build_shared_signal_notifier(session).notify` ([M9](M09-ALERTS.md)) y `SIGNAL_APPROVAL_TTL_MINUTES`
- `list_shared_bots()`, `subscribe_to_bot()` (con `SqlAlchemyUserRepository` de [M1](M01-AUTH.md)), `unsubscribe_from_bot()`

### Ciclo de ejecución del scheduler (`app/modules/scheduler/execution_cycle.py`)
`run_execution_cycle()` corre después de `run_cycle()` (velas + indicadores, [M2](M02-MARKET-DATA.md)), solo en el proceso líder (`SchedulerLock`). Cada paso está aislado: si uno falla, los demás corren.
1. **Señales automáticas** — agentes `running`, `approval`/`auto`, con `feature_set_id` y cuenta. Por agente (una sesión cada uno): última vela **cerrada** (`ts ≤ ahora − timeframe`); se omite si el timeframe es menor al mínimo, si la vela tiene más de **2 timeframes** de antigüedad (descarga caída), si sus indicadores aún no están calculados o si ya hay señal para esa vela; tope diario por usuario (`AGENT_MAX_AUTO_ANALYSES_PER_DAY`, cuenta las señales creadas desde las 00:00 UTC). `generate(owner_id=None, candle_ts=...)`; en `auto` y `pending` → `ExecuteSignalService.execute(channel="auto", decided_by_user_id=None)`.
2. **Caducar pendientes** — `expire_pending(utc_now())`.
3. **Reconciliar órdenes** — `ReconcileOrdersService.run()` ([M8](M08-ORDERS-EXECUTION.md)): órdenes live abiertas, SL nativos y respuestas perdidas.
4. **Proteger posiciones** — `ProtectPositionsService.run()` ([M8](M08-ORDERS-EXECUTION.md)).
5. **Telegram en polling** — si `TELEGRAM_UPDATES_MODE=polling` ([M9](M09-ALERTS.md)).

### Settings (`app/common/config/settings.py`)
```
TRADING_LIVE_AUTO_ENABLED=false          # permite agentes Automáticos en live
SIGNAL_APPROVAL_TTL_MINUTES=60           # vencimiento si el agente no fija approval_ttl_minutes
SIGNALS_AUTO_MIN_TIMEFRAME_SECONDS=900   # timeframe mínimo de los modos automáticos (15m)
AGENT_MAX_AUTO_ANALYSES_PER_DAY=96       # análisis automáticos por usuario y día
```

### Endpoints REST
| Método | Ruta | Auth | Nota |
|--------|------|------|------|
| GET | `/api/bots` | token | Usuario: sus bots (opcional `account_id` propio). Admin: todos, por `account_id`, por dueño (`user_id`, ignorado para usuarios) o los suyos con `?mine=true`. Filtros `status`, `mode` (`BOTS_INVALID_FILTER` 422). Más reciente primero (`created_at`, `id` desc). Paginación opt-in: con `page` (≥ 1) y `page_size` (1–100, 20 por defecto) `data` pasa a ser `{items, pagination: {total, page, page_size, total_pages}}` (`build_paginated_response`); sin `page`, la lista de siempre (catálogo que usan muchas pantallas) |
| POST | `/api/bots` | token | Crea bot (`name` obligatorio; siempre inicia en stopped). Opcionales `execution_mode` (default `manual`) y `approval_ttl_minutes` (1–1440) |
| GET | `/api/bots/{id}` | token | Detalle (404 si no es del usuario); incluye `execution_mode` y `approval_ttl_minutes` |
| GET | `/api/bots/shared` | token | Agentes que comparten señales (de cualquier usuario): `id`, `strategy_name`, `symbol`, `timeframe` (+ sus IDs), `mode`, `status`, `subscribers_count`, `is_subscribed`, `is_mine`. Sin nombre, cuenta ni dueño. Declarada antes de `/{bot_id}` |
| PUT | `/api/bots/{id}` | token | `name`, `execution_mode`, `approval_ttl_minutes` y `share_signals` en cualquier estado (enviar `approval_ttl_minutes: null` lo borra); `mode`/`risk_params` solo si stopped |
| POST | `/api/bots/{id}/start` | token | Transición → running |
| POST | `/api/bots/{id}/pause` | token | Transición → paused |
| POST | `/api/bots/{id}/stop` | token | Transición → stopped |
| POST | `/api/bots/{id}/market/sync` | token | "Actualizar datos": descarga 500 velas del símbolo/timeframe del agente (ccxt, M2) y recalcula sus indicadores (M3). 404 si no es del usuario; rate limit 3/min por usuario (`market_sync_rate_limiter`). Devuelve `rows_fetched` y `rows_calculated` (null sin conjunto) |
| POST | `/api/bots/{id}/subscription` | token | Seguir un agente compartido (idempotente). 404 `BOT_NOT_FOUND` si no existe o no comparte; 422 `SUBSCRIPTION_OWN_BOT` · `SUBSCRIPTION_TELEGRAM_REQUIRED`. Devuelve `{bot_id, is_subscribed, subscribers_count}` |
| DELETE | `/api/bots/{id}/subscription` | token | Dejar de seguir (idempotente; funciona aunque el agente ya no comparta). 404 si no hay suscripción y el agente no comparte |
| GET | `/api/signals` | token | Lista señales (requiere `?bot_id=`; 404 si el bot no es del usuario; `limit` 1–500). Más reciente primero (`ts`, `id` desc). Paginación opt-in: con `page` (≥ 1) y `page_size` (1–100, 20 por defecto) `data` pasa a ser `{items, pagination: {total, page, page_size, total_pages}}` (`build_paginated_response`); sin `page`, la lista de siempre hasta `limit` |
| GET | `/api/signals/pending` | token | Señales `pending` de mis agentes, con `bot_name` y `bot_mode`. `?mine=true` por defecto (también para admin); `mine=false` → admin ve todas. `limit` 1–200 (50) |
| POST | `/api/signals/generate` | token | Genera señal invocando M6 ("Analizar ahora"); rate limit por usuario (`AGENT_ANALYSES_PER_MINUTE`) |
| POST | `/api/signals/{id}/approve` · `/reject` | token | Viven en [M8](M08-ORDERS-EXECUTION.md) (`orders/rest/signal_decisions`) |

`_bot_to_dict` incluye `share_signals`. `_signal_to_dict` añade `decision_status`, `expires_at`, `decided_at`, `decision_channel`, `decision_reason`, `decision_reason_message` y `candle_ts`.

`read_scope(identity)` (lecturas: `None` para super admin y socio) y `write_scope(identity)` (escrituras: `None` solo para super admin) vienen de `app.common.security.jwt`.

Routers registrados en `app/app_factory.py` (dentro de `api_routers`, con `prefix=settings.API_PREFIX`). `signals_router` va antes de `signal_decisions_router` para que `GET /signals/pending` no choque con rutas `/signals/{id}`.

### Frontend (`frontend/src/modules/bots/`)
| Ruta | Archivo de ruta | Página / componentes |
|-----|----------|----|
| `/#/dashboard` (lista de agentes) | `routes/_app/dashboard.lazy.tsx` | `dashboard/pages/dashboard.tsx` ([M1](M01-AUTH.md)) + `components/agent-card.tsx` + `components/agent-price.tsx` (`hooks/use-symbol-snapshot.ts`) + `components/agents-empty-state.tsx` |
| `/#/agents/new` | `routes/_app/agents/new.lazy.tsx` | `pages/agent-new.tsx` + `components/agent-wizard/{choice-card,symbol-step,strategy-step,account-step}.tsx` + `components/execution-mode-picker.tsx` + `shared/components/stepper.tsx` |
| `/#/agents/:id` | `routes/_app/agents/$agentId.lazy.tsx` | `pages/agent-detail.tsx` + `components/{agent-controls,analyze-now-button,signals-table,signal-detail-sheet,signal-decision-actions,execution-mode-card,approval-ttl-field,share-signals-card,agent-market-tab}.tsx` (Mercado: `useSyncBotMarketMutation`, invalida velas e indicadores) |
| `/#/track-record` (sección) | `routes/_app/track-record.lazy.tsx` | `orders/pages/track-record.tsx` + `components/shared-agents-section.tsx` (reutiliza `TelegramLinkDialog` de `app-shell`) |
| `/#/agents`, `/#/bots`, `/#/admin/bots`, `/#/agent` | `routes/_app/agents/index.tsx`, `routes/_app/{bots,agent}.tsx`, `routes/_app/admin/bots.tsx` | Redirecciones (`beforeLoad` + `redirect`) |

- API: `api/bots.api.ts` (`listBots({account_id, mine})`, `getBot`, `createBot`, `updateBot`, transiciones, `listSignals`, `generateSignal`, `listPendingSignals`, aprobar/rechazar, `listSharedBots`, `subscribeToBot`, `unsubscribeFromBot`; tipos `SharedBot`, `BotSubscription`, `BotExecutionMode`, `SignalDecisionStatus`, `SignalDecisionChannel`).
- Paginación en el servidor (2026-10-20): `listSignalsPage` / `useSignalsPageQuery` (pestaña Señales, `SignalsTable`); claves `[..., 'page', filtros, {page, page_size}]` bajo `BOTS_QUERY_KEY` / `SIGNALS_QUERY_KEY` (las mutaciones existentes las invalidan) con `keepPreviousData`. La pestaña Órdenes del detalle usa `useOrdersPageQuery` de [M8](M08-ORDERS-EXECUTION.md). `useBotsQuery` (lista completa) sigue siendo el catálogo de nombres.
- Queries: `useBotsQuery`, `useMyBotsQuery` (`?mine=true`), `useBotQuery`, `useSignalsQuery`, `usePendingSignalsQuery` (clave bajo `SIGNALS_QUERY_KEY`, `refetchInterval` 30 s), `useSharedBotsQuery` (`SHARED_BOTS_QUERY_KEY`, bajo `BOTS_QUERY_KEY`: editar un agente la refresca). Mutations: create, update, transition, generate signal, `useApproveSignalMutation`, `useRejectSignalMutation`, `useSubscribeToBotMutation`, `useUnsubscribeFromBotMutation` (invalidan `SHARED_BOTS_QUERY_KEY`).
- `ShareSignalsCard` (Configuración): casilla "Compartir las señales de este agente" con `useUpdateBotMutation({share_signals})`; el nº de suscriptores sale de `useSharedBotsQuery` (solo se pide si comparte). `hooks/use-bot-transition.ts` centraliza las transiciones con sus toasts.
- Componentes del modo de ejecución: `ExecutionModePicker` (3 `ChoiceCard`; aviso en rojo para Automático + live), `ExecutionModeCard` (Configuración; Automático abre `AlertDialog` "¿Activar el modo Automático?"; en Con aprobación muestra `ApprovalTtlField`), `ApprovalTtlField` (`components/approval-ttl-field.tsx`: campo "Minutos para aprobar", entero 1–1440 como el backend, vacío = valor por defecto del servidor (`approval_ttl_minutes: null` → `SIGNAL_APPROVAL_TTL_MINUTES`); guarda con `useUpdateBotMutation`), `ExecutionModeBadge` y `SignalDecisionBadge` (en `bot-badges.tsx`; columna **Ejecución** de `SignalsTable`), `SignalDecisionActions` (Aprobar / Descartar, cuenta atrás cada 30 s, confirmación extra en live), `PendingSignalsCard` (dashboard; se oculta sin pendientes).
- `lib/agent-wizard.ts`: compatibilidad estrategia ↔ conjunto (mismo criterio que `rule_keys` del backend), conjunto recomendado, timeframe y riesgo de la estrategia, nombre sugerido.
- `lib/bots-labels.ts`: `describeBot(bot)` = nombre; `describeBotMarket(bot, catalogs)` = `BTC/USDT · 1h`; `EXECUTION_MODE_LABELS` (Manual / Con aprobación / Automático), `EXECUTION_MODE_DESCRIPTIONS`, `SIGNAL_DECISION_LABELS` (— / Por aprobar / Enviando orden / Ejecutada / Descartada / Vencida / No ejecutada), `DECISION_CHANNEL_LABELS`; motivos de rechazo `INCONSISTENT_LEVELS` y `ENTRY_TOO_FAR`.

### Corrección de rutas

> Los routers declaran `prefix="/bots"` y `prefix="/signals"` y `app_factory.py` les añade `/api`. En el front se escriben sin `/api`.

## Gotchas críticos

- **Perpetuos solo en paper:** `CreateBotService` y `UpdateBotService` (al pasar a live) devuelven `BOT_PERPETUAL_LIVE_NOT_SUPPORTED` (422) si el símbolo es un perpetuo (`XAU/USDT:USDT`, `is_perpetual()` de M2). El asistente oculta las cuentas live con un perpetuo elegido y acepta `?symbol_id=` (desde Explorar mercados).
- **Live = mismo exchange (2026-10-26):** un agente live solo opera símbolos del exchange de su cuenta (`BOT_EXCHANGE_ACCOUNT_MISMATCH`). El asistente (`agent-new.tsx`) filtra las cuentas live por `exchange_id` del símbolo y pasa `hiddenLiveNote` a `AccountStep` para explicar por qué no aparecen; al cambiar el símbolo se limpia la cuenta si era live. Los agentes live creados **antes** de la regla no se migran: [M8](M08-ORDERS-EXECUTION.md) les bloquea las compras (`ORDER_EXCHANGE_MISMATCH`) pero deja vender para cerrar lo que ya tengan; hay que recrearlos con un símbolo del exchange de la cuenta.
- **Seed `bots`:** dos agentes demo en paper y detenidos para el usuario demo ("Oro — tendencia 4h" con Tendencia Metales y "BTC — tendencia 1h" con EMA Trend Follower, conjunto Tendencia), idempotente por (account_id, name). Quedan en `manual`.
- **Modo automático sin señales:** un agente `approval`/`auto` no genera nada si está `paused`, si su timeframe es < 15m, si la descarga de velas va atrasada (> 2 timeframes) o si el usuario llegó al tope diario. El log del scheduler (`[Execution]`) dice cuál fue.
- **`GET /signals/pending` y admin:** por defecto (`mine=true`) el admin también ve solo las suyas; para todas, `?mine=false`.
- **Pendientes vencidas:** la API las oculta en cuanto vence `expires_at`, pero en BD siguen `pending` hasta el siguiente ciclo del scheduler, que las marca `expired`.
- `ServiceResult` almacena el error en `result.error.code` (NO `result.code`).
- `feature_set_id` es por bot, NO global. El bot pasa su propio `feature_set_id` al AnalyzeService.
- El bot `paused` ES activo (`is_active() = True`), pero no genera señales automáticas.
- Señales rechazadas siempre se persisten con `approved=False`.
- Dirección buy/sell se infiere: `entry > stop_loss` → buy; `entry < stop_loss` → sell. En spot una SELL ejecutada **cierra** la posición, no abre un corto ([M8](M08-ORDERS-EXECUTION.md)).
- **Admin y `GET /api/bots`:** sin filtros recibe **todos** los bots del sistema. En pantallas de usuario usar `useMyBotsQuery` (`?mine=true`), nunca `useBotsQuery()` a secas.
- **Compatibilidad en dos lados:** el front filtra conjuntos con `isFeatureSetCompatible` y el backend valida con `indicator_catalog.is_compatible`. Si cambia el formato de las reglas, actualizar ambos.
- **`llm_*` en NULL:** las señales rechazadas por régimen o reglas no consultan a la IA, y las anteriores al 2026-10-19 no lo tienen; el detalle oculta "Consulta a la IA" si `llm_provider` es `null`. `model_version` sigue sin usarse (reservada a modelos ML).
- **Decimales como `float`:** `_signal_to_dict` serializa precios y `confidence` con `float(...)`; el front los tipa como `number`.

## Tests

- `tests/bots/test_bot_entity.py` — 22 tests (máquina de estados, is_active, risk_params)
- `tests/bots/test_update_bot_status_service.py` — 16 tests (transiciones, timestamps, repo.commit)
- `tests/bots/test_generate_signal_service.py` — 17 tests (validaciones, dirección, campos); el 2026-10-19 se ajustó la llamada esperada a `analyze` (`risk_pct`, `as_of`)
- `tests/bots/test_signal_subscription_services.py` — 14 tests (listado público, `is_mine`/`is_subscribed`/conteo, privado → 404, propio, Telegram, idempotencia, dejar de seguir tras apagar)
- `tests/bots/test_generate_signal_shared_hook.py` — 7 tests (`notify_subscribers` solo con agente compartido y BUY/SELL aprobada, después del commit; fallo tragado)
- `tests/bots/test_shared_signal_notifier.py` — 10 tests del notificador de [M9](M09-ALERTS.md)
- Total del alcance original: 55 tests unitarios (+ 31 de señales compartidas). **Huecos:** propiedad, validaciones de `CreateBotService`/`UpdateBotService`, `execution_mode_rules`, decisión de ejecución, pendientes, ciclo del scheduler, rutas REST, hooks de alertas y de Telegram.

## Riesgos

- **Automático en live** envía órdenes reales sin una persona en medio; está apagado por defecto (`TRADING_LIVE_AUTO_ENABLED=false`) y además depende de `TRADING_LIVE_ENABLED` ([M8](M08-ORDERS-EXECUTION.md)).
- Coste de la IA: cada agente automático hace un análisis por vela cerrada; lo acotan el timeframe mínimo y el tope diario por usuario.
- Una señal manual ("Analizar ahora") se sigue generando con la última vela, aunque no esté cerrada.
- **Señales compartidas:** el envío a los suscriptores es síncrono (un `sendMessage` por persona, timeout 10 s) dentro del request de "Analizar ahora" o del ciclo del scheduler; con muchos suscriptores o Telegram lento, tarda. Si crece, pasarlo a una cola. Una señal compartida es información, no una recomendación personalizada: el texto lo dice, pero conviene revisarlo con quien lleve lo legal.

## Historial

- **2026-03** — Módulo completado: CRUD de bots con máquina de estados, `GenerateSignalService`, UI `/bots` y `/admin/bots`, 55 tests.
- **Posterior** — Hook post-commit de alertas ([M9](M09-ALERTS.md)).
- **2026-10-08** — API headless (/api), páginas migradas a React (frontend/).
- **2026-10-08** — **Agentes:** los bots pasan a llamarse agentes en la UI y son el punto de entrada (dashboard, asistente, detalle). Nombre (`bots.name`), propiedad en todas las rutas, validaciones de creación, regla del 1 % en el backend, `?mine=true`. La página "Agente de IA" se integra como "Analizar ahora".
- **2026-10-10** — Perpetuos TradFi bloqueados en live; `?symbol_id=` en `/agents/new`; seed `bots` con dos agentes demo.
- **2026-10-19** — Cada señal guarda servicio, modelo y latencia de la IA (`signals.llm_*`); sección "Consulta a la IA" en `signal-detail-sheet.tsx` (`llmProviderLabel`, `formatLatency` en `bots-labels.ts`).
- **2026-10-19** — Auditoría de seguridad: el agente pasa su `effective_risk_pct` a la IA; cambiar a live exige cuenta live (`BOT_MODE_ACCOUNT_MISMATCH`); rate limit en `POST /signals/generate`; `owner_scope` movido a `role_guard`.
- **2026-10-19** — **Modo de ejecución** Manual / Con aprobación / Automático (`bots.execution_mode`, `approval_ttl_minutes`), decisión por señal (`signals.decision_*`, `expires_at`, `candle_ts` UNIQUE; migración `f51e2dad9c13`), señales automáticas por vela cerrada en el scheduler, `GET /api/signals/pending`, aviso por Telegram en Con aprobación, UI (selector, badges, Aprobar/Descartar, tarjeta del dashboard).
- **2026-10-19** — Campo **Minutos para aprobar** (`ApprovalTtlField`) en la tarjeta del modo de ejecución (solo en Con aprobación). El ciclo de ejecución del scheduler suma la reconciliación de órdenes de [M8](M08-ORDERS-EXECUTION.md) antes de proteger posiciones.
- **2026-10-19** — Pestaña **Mercado** en el detalle del agente (`AgentMarketTab`: velas + indicadores de su símbolo/timeframe) con **Actualizar datos** (`SyncBotMarketDataService` → `POST /api/bots/{id}/market/sync`, reutiliza `FetchCandlesService` y `CalculateFeaturesService`). El agente concentra todo lo suyo: el menú del usuario pierde Órdenes, Símbolos, Velas e Indicadores, y el admin pierde Descargar velas y Calcular indicadores. El grupo admin "Operación" pasa a **Supervisión** con nombres que dicen el alcance (Todos los agentes, Todas las cuentas, Gestionar estrategias, Todas las órdenes, Todas las alertas) para no confundirlos con Mis agentes / Mis cuentas.
- **2026-10-20** — Fila **Precio** en `AgentCard` (`AgentPrice` + `useSymbolSnapshot`, movido desde el dashboard): último cierre, variación y régimen del mercado de cada agente, en el inicio.
- **2026-10-20** — Se retira la página "Mis agentes" (`pages/agents.tsx`): el inicio lista todos los agentes con el filtro por estado; `/agents` redirige a `/dashboard`.
- **2026-10-20** — Todos los agentes: columna **Dueño** (nombre y correo) y filtro por dueño.
- **2026-10-20** — **Señales compartidas por Telegram**: `bots.share_signals` + tabla `signal_subscriptions` (migración `c4a7ce763b72`), `GET /api/bots/shared`, `POST`/`DELETE /api/bots/{id}/subscription` (idempotentes; exigen Telegram; no se sigue un agente propio; privados → 404), hook `notify_subscribers` en `GenerateSignalService` → `SharedSignalNotifier` ([M9](M09-ALERTS.md)). Al apagar se conservan las suscripciones y deja de enviarse. UI: tarjeta **Compartir señales** en Configuración y sección **Agentes que comparten sus señales** en Track record. 31 tests nuevos.
- **2026-10-20** — **Paginación en el servidor** (Fase 4): `GET /api/bots` y `GET /api/signals` aceptan `page`/`page_size` opt-in (sin `page`, misma lista que antes); `GET /api/bots` suma los filtros `status`, `mode` y `user_id` (dueño, solo admin). `BotRepository.search/count` (`BotCriteria`), `SignalRepository.count_by_bot` y `offset` en `list_by_bot`; `ListBotsService.list_page`, `ListSignalsService.list_page` (contrato `Page`/`PageRequest` en `app/common/contracts/pagination.py`). Front: Todos los agentes y las pestañas Señales y Órdenes del agente piden página a página (`DataTable` con `pagination` + `useServerPagination`). La miga del detalle abierto por un admin desde Supervisión pasa a "Administración › Todos los agentes › <agente>". Tests: `tests/bots/test_list_bots_and_signals_pagination.py`, `tests/common/test_pagination.py`.
- **2026-10-20** — Pestaña **Mercado**: gráfico de precio de cierre (`market/components/price-line-chart.tsx`, SVG propio sin librerías, tipo `PriceLevel` en `market/lib/price-chart.ts`) con las líneas Entrada / SL / TP de la posición abierta; tooltip con apertura, máximo y mínimo; accesible con teclado (`role=slider`). La tabla de velas sigue debajo como vista con todos los valores.
- **2026-10-23** — Se retira el grupo **Supervisión** del menú: fuera "Todos los agentes" (`/#/admin/agents`, `pages/admin-agents.tsx`, `BotActionsMenu`, `listBotsPage`/`useBotsPageQuery`) y la redirección `/#/admin/bots`. Los agentes se revisan en su detalle; el staff llega a los de otros desde Administración → Fondo → **Agentes del fondo**, y la miga del detalle dice "Administración › Agentes del fondo". `GET /api/bots` (paginado y filtros) sigue igual en el backend.
- **2026-10-26** — **Live = mismo exchange que la cuenta:** `CreateBotService` y `UpdateBotService` (al pasar a live) devuelven `BOT_EXCHANGE_ACCOUNT_MISMATCH` (422) si el símbolo es de otro exchange que la cuenta. El asistente solo ofrece las cuentas live del exchange del símbolo y explica las ocultas. Respaldo en [M8](M08-ORDERS-EXECUTION.md) para los agentes ya creados (`ORDER_EXCHANGE_MISMATCH` en compras live).
