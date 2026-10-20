# Trading AI — Índice de módulos

Una explicación simple de los 10 módulos del sistema, sin tecnicismos. Cada módulo tiene su propia spec.

## Estado del proyecto

| Módulo | Estado | Alcance | Madurez | Descripción |
|--------|--------|--------:|--------:|-------------|
| [M1 — Auth & Frontend](M01-AUTH.md) | ✅ Completo | 100 % | 84 % | Login solo por código OTP (con intentos máximos), sesiones JWT, roles, defensa CSRF por Origin, auditoría sin secretos, vínculo de Telegram, frontend React (shell, dashboard) |
| [M2 — Market Data](M02-MARKET-DATA.md) | ✅ Completo | 86 % | 67 % | Exchanges, símbolos (cripto + perpetuos TradFi: metales, materias primas, ETFs, acciones), velas OHLCV via ccxt, scheduler de ingesta (un solo líder por lock de MySQL) y explorador de tendencia |
| [M3 — Feature Engineering](M03-FEATURE-ENGINEERING.md) | ✅ Completo | 100 % | 82 % | RSI, ATR, EMA, MACD, Bollinger Bands, régimen; conjuntos por enfoque (Completo/Tendencia/Rango) |
| [M4 — Accounts & Portfolio](M04-ACCOUNTS-PORTFOLIO.md) | ✅ Completo | 100 % | 79 % | Cuentas de exchange (credenciales cifradas), balances, equity curve |
| [M5 — Strategies](M05-STRATEGIES.md) | ✅ Completo | 86 % | 70 % | Reglas de entrada/salida, backtesting sin IA, validación tipo/régimen, datasets |
| [M6 — AI Agent / Models](M06-AI-AGENT.md) | ✅ Completo | 100 % | 81 % | Prompt Maestro con pool de LLMs rotativo (Groq + Gemini + Ollama Cloud, con failover), salida del LLM validada, rate limit por usuario, modelos ML y model runs |
| [M7 — Bots & Signals](M07-BOTS-SIGNALS.md) | ✅ Completo | 100 % | 81 % | **Agentes** (bots en la UI): punto de entrada, asistente, señales BUY/SELL/HOLD con entry/SL/TP y **modo de ejecución** Manual / Con aprobación / Automático (señales automáticas por vela cerrada) |
| [M8 — Orders & Execution](M08-ORDERS-EXECUTION.md) | ✅ Completo | 100 % | 84 % | Órdenes paper/live (ccxt) con propiedad, RiskGate e idempotencia; señal → orden (aprobada o automática); SL nativo en el exchange en live + TP por ciclo del scheduler; protección SL/TP también en compras manuales y en compras que se ejecutan tarde; cancelar órdenes; reconciliación con el exchange; fills, posiciones; 350+ tests |
| [M9 — Alerts](M09-ALERTS.md) | ✅ Completo | 100 % | 58 % | Reglas de alerta, notificaciones email/Telegram/webhook (con guarda SSRF)/desktop; bot de Telegram por usuario para aprobar señales |
| [M10 — Billing & Managed Accounts](M10-BILLING.md) | ✅ Completo | 100 % | 75 % | Inversores, cuentas administradas, performance fee con HWM |
| **Promedio** | | **97 %** | **76 %** | |

- **Alcance** = entregables del plan original hechos / planificados. Las dos filas por debajo del 100 % (M2 y M5) son por los tests de services que el plan original listaba y nunca se escribieron.
- **Madurez** = estimación de qué tan lista para producción está cada pieza (rúbrica abajo). Es una opinión fundamentada en el repo, no una medición.

Más detalle:
- Cada spec `MNN-*.md` es la **fuente de verdad de su módulo**: descripción, páginas, entregables, decisiones, avance, mejoras, detalle técnico (tablas, archivos, endpoints), gotchas y tests. (Reemplaza a los antiguos `ROADMAP.md` y `MODULES_MAP.md`.)
- Orden de dependencias y mapa de páginas: [más abajo](#orden-de-dependencias).
- Manual en lenguaje simple: [`MANUAL.md`](../docs/MANUAL.md)
- Esquema de base de datos: modelos ORM + `database/migrations/versions/` (ver skill [`database`](../.claude/skills/database/SKILL.md))

### Cómo usar estas specs
- Al iniciar cada sesión: leer este archivo para saber en qué módulo estamos y luego la spec del módulo (se leen bajo demanda, no se importan en `CLAUDE.md`).
- **Leer la spec del módulo ANTES de codear** para no pisar lo anterior (tablas, archivos y endpoints están en su sección "Detalle técnico").
- Al terminar un módulo o una feature significativa: skill [`update-specs`](../.claude/skills/update-specs/SKILL.md) (spec, tabla de arriba y `MANUAL.md`). Las convenciones de código viven en `CLAUDE.md` y `.claude/skills/`; los bugs y notas de cada módulo, en su spec.

---

## Flujo completo

```
[Módulo 2: Market Data]
   Precios históricos (velas OHLCV)
         ↓
[Módulo 3: Feature Engineering]
   Indicadores técnicos + Régimen de mercado
         ↓
[Módulo 4: Accounts ✅]  [Módulo 5: Strategies ✅]
   Capital disponible  +  Reglas de entrada/salida
         ↓                        ↓
         └──────────┬─────────────┘
                    ↓
         [Módulo 6: AI Agent]
         ¿La operación es buena?
         APROBADA / RECHAZADA
                    ↓
         [Módulo 7: Bots & Signals]
         Señal: BUY / SELL / HOLD
                    ↓
         Modo Manual / Con aprobación / Automático
                    ↓
         [Módulo 8: Orders & Execution]
         RiskGate → orden al exchange (paper o live)
         Stop Loss nativo en el exchange (live) / Take Profit por el scheduler
         Reconciliación de órdenes con el exchange
                    ↓
         [Módulo 9: Alerts]
         Notificaciones por email, Telegram o webhook
         (Telegram también para aprobar señales)
```

El [Módulo 1 (Auth)](M01-AUTH.md) protege el acceso a todo el sistema. Sin estar autenticado, no se puede usar ningún módulo.
El [Módulo 10 (Billing)](M10-BILLING.md) se apoya en el historial de órdenes y ejecuciones del [Módulo 8](M08-ORDERS-EXECUTION.md) para calcular el fee de performance.

### Estado real del flujo (verificado en el código el 2026-10-19)

El lazo está cerrado para los agentes que lo piden; **Manual sigue siendo el modo por defecto**. Hoy:

- **Scheduler ([M2](M02-MARKET-DATA.md)):** un solo proceso líder (lock de MySQL). Cada ciclo (60 s) actualiza velas y features de los agentes `running`/`paused` y después corre el **ciclo de ejecución** (`execution_cycle.py`).
- **Señales ([M7](M07-BOTS-SIGNALS.md)):**
  - **Manual:** a mano con "Analizar ahora" (`POST /api/signals/generate`).
  - **Con aprobación / Automático:** el scheduler genera **una señal por vela cerrada** para cada agente `running` (timeframe ≥ 15m, datos al día, tope diario por usuario). Una BUY/SELL aprobada por la IA queda **pendiente** hasta su vencimiento (60 min por defecto).
- **Aprobación:** en Con aprobación la persona aprueba o descarta desde la app (detalle de la señal o tarjeta del dashboard) o desde **Telegram** con botones ([M9](M09-ALERTS.md)). Solo una decisión gana (UPDATE condicional). Al aprobar se revalida al precio actual (R/R ≥ 2:1) y se recalcula la cantidad para mantener el 1 %.
- **Órdenes ([M8](M08-ORDERS-EXECUTION.md)):** en Automático la orden sale sola en el mismo ciclo; en Manual se crea con `POST /api/orders`. Toda orden pasa por el **RiskGate** (kill switch, live apagado por defecto, valor máximo por compra, drawdown máximo) y queda guardada antes de llamar al exchange.
- **Stop Loss / Take Profit:** la posición abierta desde una señal guarda su SL/TP. En **live** (con `ORDER_NATIVE_STOP_LOSS=true`, por defecto) el SL queda como **orden stop nativa en el exchange** (protege aunque la app esté caída) y el scheduler solo vigila el TP; antes de cualquier otra venta se cancela el SL nativo. En **paper**, o si el exchange no soporta el stop nativo, el scheduler cierra a mercado cuando una vela toca cualquiera de los dos. Sin OCO. Las posiciones de órdenes manuales no tienen protección automática.
- **Reconciliación ([M8](M08-ORDERS-EXECUTION.md)):** en cada ciclo el scheduler sincroniza con el exchange las órdenes live `sent`/`partially_filled` de los últimos 7 días: registra lo ejecutado después (límites, SL nativo disparado, parciales), adopta el estado del exchange y marca rechazada a los 10 min una orden "sin respuesta" que el exchange no conoce. Orden del ciclo: señales automáticas → caducar → reconciliar → proteger → Telegram.
- **Alertas ([M9](M09-ALERTS.md)):** se disparan solas con señales y órdenes (también rechazadas); las de precio solo con evaluación manual; `pnl` y `drawdown` no se evalúan.
- **Cancelar y proteger (2026-10-20):** las órdenes live abiertas se cancelan desde la app; las compras manuales a mercado pueden llevar SL/TP; una compra que se ejecuta tarde recibe su protección en la reconciliación y la señal se cierra cuando la orden termina.
- **Pendiente:** TP nativo / OCO en el exchange y **correr** la prueba en testnet (`scripts/testnet_check.py` + `docs/TESTNET.md`). M8 tiene tests unitarios completos (`tests/orders/`), pero sin un exchange real.

---

## Orden de dependencias
```
Módulo 1 (Auth)
    ↓
Módulo 2 (Market Data) ← sin datos no hay nada
    ↓
Módulo 3 (Features) ← necesita velas
    ↓
Módulo 4 (Accounts) ← paralelo con 3 si se quiere
    ↓
Módulo 5 (Strategies) ← necesita features + accounts
    ↓
Módulo 6 (AI Agent) ← necesita strategies + features
    ↓
Módulo 7 (Bots & Signals) ← necesita agent + strategies
    ↓
Módulo 8 (Orders & Execution) ← necesita signals + accounts
    ↓
Módulo 9 (Alerts) ← puede ir en paralelo con 7 u 8
    ↓
Módulo 10 (Billing) ← necesita historial de orders + fills de M8
```

---

## Prioridades transversales (síntesis de las "Posibles mejoras")

| # | Prioridad | Qué | Módulos |
|---|---|---|---|
| 1 | ~~Alta~~ → Baja | ~~Cerrar el lazo de automatización~~ **Resuelto en lo esencial (2026-10-19):** señales automáticas por vela cerrada, aprobación en app/Telegram, ejecución automática, SL nativo en el exchange en live + TP por ciclo, y reconciliación de órdenes con el exchange. **Queda:** TP nativo / OCO | [M7](M07-BOTS-SIGNALS.md), [M8](M08-ORDERS-EXECUTION.md), [M2](M02-MARKET-DATA.md) (scheduler) |
| 2 | **Alta** (parcial) | ~~Tests de órdenes y ejecución~~ **Hecho (2026-10-20):** `tests/orders/` cubre entidades, `LiveExecutor`, RiskGate, crear/cancelar, señales, protección, reconciliación y SL nativo (destaparon 6 bugs, corregidos). **Pendiente:** `execution_cycle`, `execution_mode_rules` y tests donde no hay ninguno: market, strategies, alerts | [M8](M08-ORDERS-EXECUTION.md), [M7](M07-BOTS-SIGNALS.md), [M2](M02-MARKET-DATA.md), [M5](M05-STRATEGIES.md), [M9](M09-ALERTS.md) |
| 3 | ~~Alta~~ ✅ | ~~Seguridad: validar URL del webhook (SSRF) y ampliar el rate limit~~ **Resuelto (2026-10-19):** guarda SSRF del webhook y rate limit por usuario en las rutas de la IA (además: propiedad en órdenes y en `/agent/analyze`, CSRF por Origin, auditoría sin secretos) | [M9](M09-ALERTS.md), [M1](M01-AUTH.md), [M6](M06-AI-AGENT.md) |
| 4 | Alta (parcial) | Salvaguardas para `live`. **Hecho:** tamaño máximo (`ORDER_MAX_NOTIONAL` / `max_notional`), kill switch, live apagado por defecto, drawdown máximo, idempotencia (`client_order_id`), reconciliación con el exchange y SL nativo (2026-10-19). Cancelar órdenes desde la API/UI (2026-10-20). **Pendiente:** correr la prueba en testnet (`scripts/testnet_check.py` + `docs/TESTNET.md`) antes del primer peso real | [M8](M08-ORDERS-EXECUTION.md) |
| 5 | Media (parcial) | Scheduler: **lock hecho** (un solo líder con `GET_LOCK`); sigue recomendado sacarlo a un proceso aparte. Pendiente el relleno de huecos de velas | [M2](M02-MARKET-DATA.md) |
| 6 | Media | Sincronizar balances con el exchange y derivar `closing_equity` de ellos; registrar cobros del fee | [M4](M04-ACCOUNTS-PORTFOLIO.md), [M10](M10-BILLING.md) |
| 7 | ~~Media~~ ✅ | ~~Backtesting~~ **Hecho (2026-10-20):** backtesting sin IA (`POST /api/backtests`, página Backtesting) con las mismas reglas y métricas que los agentes reales | [M5](M05-STRATEGIES.md) |

### Hoja de ruta de ingresos (propuesta, nada de esto está implementado)

| # | Prioridad | Qué | Módulos |
|---|---|---|---|
| 8 | ~~Alta~~ ✅ (parcial) | ~~Métricas y track record~~ **Hecho (2026-10-20):** pestaña **Rendimiento** del agente (`GET /api/performance?bot_id=`: win rate, P&L, R/R real, profit factor, drawdown, operaciones cerradas) y página **Track record** para usuarios con sesión (`GET /api/performance/strategies`, anónimo y en retornos %). **Pendiente:** `portfolio_snapshots` (curva de capital con el valor de la cuenta) sigue sin escribirse | [M7](M07-BOTS-SIGNALS.md), [M8](M08-ORDERS-EXECUTION.md), [M4](M04-ACCOUNTS-PORTFOLIO.md) |
| 9 | ~~Alta~~ ✅ | ~~Backtesting~~ **Hecho (2026-10-20)**, ver prioridad 7. Sobre historia del exchange (no sobre `datasets`, que siguen sin UI) | [M5](M05-STRATEGIES.md), [M2](M02-MARKET-DATA.md) |
| 10 | ~~Media~~ (parcial) | **Registro por invitación** hecho (2026-10-20, `POST /api/users`). Planes SaaS con pasarela: descartados por ahora |  [M1](M01-AUTH.md), [M10](M10-BILLING.md) |
| 11 | ~~Media~~ ✅ | ~~Señales como servicio~~ **Hecho (2026-10-20):** el dueño comparte las señales de su agente y otros lo siguen por Telegram (sin ejecutar nada) | [M9](M09-ALERTS.md), [M7](M07-BOTS-SIGNALS.md) |
| 12 | ~~Media~~ ✅ (parcial) | **Hecho (2026-10-20):** equity sugerido desde balances, comisiones cobradas/condonadas, extracto CSV, aportes y retiros. **Pendiente:** balances sincronizados con el exchange (hoy se registran a mano) | [M10](M10-BILLING.md), [M4](M04-ACCOUNTS-PORTFOLIO.md) |
| 13 | Baja | Marketplace de estrategias / copy-trading (más adelante, con track record verificado) | [M5](M05-STRATEGIES.md), [M7](M07-BOTS-SIGNALS.md) |

> **Nota legal:** gestionar dinero de terceros (cuentas gestionadas con comisión de desempeño) y vender señales de trading pagas puede estar regulado según el país (asesoría de inversión, gestión de portafolios, licencias). Validarlo con un abogado antes de lanzar cualquiera de las rutas 10–13. Este documento no es asesoría legal.

---

## Arquitectura de presentación (global)

Desde el 2026-10-08 la API es **headless**: FastAPI no renderiza vistas (se eliminaron `app/modules/web`, `app/templates` y `app/static`). Todas las rutas REST viven bajo `/api` (salvo `/health`) y todo error sale con el envelope `{msg, errorCode, data}`. La UI es un frontend React en [`frontend/`](../frontend/) (Vite + TanStack Router/Query + shadcn); convenciones en el skill [`frontend`](../.claude/skills/frontend/SKILL.md).

---

## Mapa de páginas (frontend React)

Hash routing: la URL real es `/#/<ruta>`. Cada ruta vive en `frontend/src/routes/` y su página en `frontend/src/modules/<modulo>/pages/`.

| Rol | Páginas |
|---|---|
| Público | `/login` |
| Usuario (y demás roles) | `/dashboard` (inicio = lista de agentes), `/agents/new`, `/agents/:id`, `/alerts`, `/portfolio`, `/strategies`, `/track-record`, `/backtest`, `/market/explorer` (`/agents`, `/bots`, `/agent`, `/orders`, `/features` y `/market/candles` redirigen a `/dashboard`; `/market/symbols` a `/market/explorer`) |
| Admin (`_app/admin/*`) | `/admin/exchanges`, `/admin/symbols`, `/admin/timeframes`, `/admin/feature-sets`, `/admin/users`, `/admin/accounts`, `/admin/strategies`, `/admin/agents`, `/admin/orders`, `/admin/alerts`, `/admin/telegram`, `/admin/investors`, `/admin/managed-accounts`, `/admin/billing` |
| Inversor (`_app/investor/*`) | `/investor/dashboard` |

Comprar/Vender vive en el [Módulo 8 — Orders & Execution](M08-ORDERS-EXECUTION.md).

Cambios del 2026-10-19 (nuevas piezas dentro de páginas existentes y reorganización del menú):
- `/agents/:id`: pestaña **Mercado** (velas e indicadores del agente, con **Actualizar datos** para descargar y recalcular a pedido). Órdenes, Símbolos, Velas e Indicadores dejan de ser páginas del usuario, y el admin pierde Descargar velas y Calcular indicadores (los endpoints siguen por API) — [M7](M07-BOTS-SIGNALS.md), [M2](M02-MARKET-DATA.md), [M3](M03-FEATURE-ENGINEERING.md), [M8](M08-ORDERS-EXECUTION.md).
- `/dashboard`: tarjeta **Señales por aprobar** (aprobar/descartar; solo aparece si hay pendientes) — [M7](M07-BOTS-SIGNALS.md).
- `/agents/new` (paso 4) y `/agents/:id` (pestaña Configuración): selector **Cuando la IA aprueba una operación** (Manual / Con aprobación / Automático); detalle de señal con Aprobar / Descartar y columna **Ejecución** en Señales — [M7](M07-BOTS-SIGNALS.md).
- `/agents/:id` → Posiciones: "Protección automática: SL · TP" y, en live, "El stop loss está como orden en el exchange." — [M8](M08-ORDERS-EXECUTION.md).
- `/agents/:id` → Configuración, en modo Con aprobación: campo **Minutos para aprobar** — [M7](M07-BOTS-SIGNALS.md).
- Menú de usuario (todas las páginas): **Conectar Telegram** (diálogo) — [M1](M01-AUTH.md) / [M9](M09-ALERTS.md).

En la UI los bots se llaman **agentes** y son el punto de entrada: el inicio es la lista de agentes (con filtro por estado) y el menú se organiza en **Operar** (Alertas, Mis cuentas) y **Explorar** (Explorar mercados, Estrategias). Todo lo que depende de un agente (órdenes, posiciones, velas, indicadores) vive dentro de su detalle, porque esos datos solo existen para agentes creados y activos. En Administración, el grupo **Supervisión** reúne las vistas de solo lectura de todos los usuarios con nombres que dicen su alcance (Todos los agentes, Todas las cuentas, Todas las órdenes, Todas las alertas), cada una con columna y filtro de **Dueño**; **Configuración** reúne lo que el admin define para el sistema (Usuarios —con el cambio de rol—, Gestionar estrategias, Telegram). En código, tablas y API siguen siendo `bot`.

---

## Archivos de infraestructura críticos (nunca romper)

Listado y cuándo tocar cada uno: skill [`backend-core`](../.claude/skills/backend-core/SKILL.md) → "Archivos de infraestructura críticos".

---

## Checklist al crear un módulo nuevo

Checklist completo (BD → domain → infra → services → providers → REST → frontend → docs): skill [`new-module`](../.claude/skills/new-module/SKILL.md). Al cerrar: skill [`update-specs`](../.claude/skills/update-specs/SKILL.md).

---

## Rúbrica de madurez

La **madurez** de cada módulo es la media de cuatro ejes (0–100):

| Eje | 100 significa… |
|---|---|
| Funcionalidad | Cubre el objetivo del módulo en producción, sin carencias conocidas |
| Tests | Servicios y rutas cubiertos; 0 = sin tests |
| Seguridad / robustez | Auth, ownership, validación de entradas y manejo de errores completos |
| Operación | Automatizada, configurable, con seeds/migraciones, observable |

Los números son una **estimación** y deben revisarse cuando cambie el módulo (se anota la evidencia en la sección "Avance" de cada spec).

## Plantilla de spec (`specs/MNN-*.md`)

Cada spec sigue las mismas secciones, en este orden:

1. Título `# Módulo N — Nombre ✅/📌` + enlace al índice
2. **Ficha** (estado, avance, madurez, tablas, dependencias, prefijo API, última revisión)
3. **Descripción** (en palabras simples + qué hace) · **Páginas** (usuario vs admin) · **Entregables**
4. **Decisiones de diseño** (decisión · motivo · alternativa descartada)
5. **Avance** (alcance + madurez con evidencia) · **Posibles mejoras** (prioridad y esfuerzo) · **Fuera de alcance y pendientes conocidos**
6. **Detalle técnico** (tablas, ORM, repos, servicios, endpoints, páginas, settings) · **Gotchas críticos** · **Tests**
7. **Riesgos** · **Historial**

---

## ⚠️ Nota importante — El sistema no garantiza ganancias por sí solo

El bot ejecuta las reglas de las estrategias con disciplina perfecta. Pero la rentabilidad depende del **edge** (ventaja estadística) de esas estrategias.

**¿Qué es el edge?**
Una estrategia tiene edge cuando el historial de operaciones muestra que las ganancias superan las pérdidas de forma consistente. Se mide con: Win Rate, R/R real, Profit Factor y Max Drawdown.

**¿Cómo se valida el edge en este sistema?**
1. Correr el sistema en **modo paper** ([M7](M07-BOTS-SIGNALS.md) + [M8](M08-ORDERS-EXECUTION.md) sin dinero real) durante 3-6 meses
2. Acumular 100+ operaciones por estrategia
3. Calcular métricas reales del historial (`signals` → `orders` → `fills`)
4. Solo pasar a live si los números son consistentemente positivos

**Capital mínimo para operar en live:**
- $5,000 → mínimo para que la Regla del 1% genere operaciones con tamaño real
- $10,000 → razonable para demostrar resultados
- $50,000+ → donde empieza a ser negocio real

Ver [`MANUAL.md`](../docs/MANUAL.md) Parte 4 para explicación completa de edge, capital y rutas de negocio.
