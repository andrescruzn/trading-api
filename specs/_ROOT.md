# Trading AI — Índice de módulos

Una explicación simple de los 10 módulos del sistema, sin tecnicismos. Cada módulo tiene su propia spec.

## Estado del proyecto

| Módulo | Estado | Alcance | Madurez | Descripción |
|--------|--------|--------:|--------:|-------------|
| [M1 — Auth & Web UI](M01-AUTH.md) | ✅ Completo | 100 % | 88 % | Login password/OTP, sesiones JWT, roles, dashboard |
| [M2 — Market Data](M02-MARKET-DATA.md) | ✅ Completo | 86 % | 65 % | Exchanges, símbolos, timeframes, velas OHLCV via ccxt + scheduler de ingesta |
| [M3 — Feature Engineering](M03-FEATURE-ENGINEERING.md) | ✅ Completo | 100 % | 79 % | RSI, ATR, EMA, MACD, Bollinger Bands, régimen de mercado |
| [M4 — Accounts & Portfolio](M04-ACCOUNTS-PORTFOLIO.md) | ✅ Completo | 100 % | 79 % | Cuentas de exchange (credenciales cifradas), balances, equity curve |
| [M5 — Strategies](M05-STRATEGIES.md) | ✅ Completo | 86 % | 55 % | Reglas de entrada/salida, validación tipo/régimen, datasets |
| [M6 — AI Agent / Models](M06-AI-AGENT.md) | ✅ Completo | 100 % | 76 % | Prompt Maestro multi-provider LLM, modelos ML y model runs |
| [M7 — Bots & Signals](M07-BOTS-SIGNALS.md) | ✅ Completo | 100 % | 73 % | Bots automáticos, señales BUY/SELL/HOLD con entry/SL/TP |
| [M8 — Orders & Execution](M08-ORDERS-EXECUTION.md) | ✅ Completo | 100 % | 50 % | Órdenes paper/live (ccxt), fills, posiciones |
| [M9 — Alerts](M09-ALERTS.md) | ✅ Completo | 100 % | 50 % | Reglas de alerta, notificaciones email/Telegram/webhook/desktop |
| [M10 — Billing & Managed Accounts](M10-BILLING.md) | ✅ Completo | 100 % | 75 % | Inversores, cuentas administradas, performance fee con HWM |
| **Promedio** | | **97 %** | **69 %** | |

- **Alcance** = entregables del plan original hechos / planificados. Las dos filas por debajo del 100 % (M2 y M5) son por los tests de services que el plan original listaba y nunca se escribieron.
- **Madurez** = estimación de qué tan lista para producción está cada pieza (rúbrica abajo). Es una opinión fundamentada en el repo, no una medición.

Más detalle:
- Cada spec `MNN-*.md` es la **fuente de verdad de su módulo**: descripción, páginas, entregables, decisiones, avance, mejoras, detalle técnico (tablas, archivos, endpoints), gotchas y tests. (Reemplaza a los antiguos `ROADMAP.md` y `MODULES_MAP.md`.)
- Orden de dependencias y mapa de páginas: [más abajo](#orden-de-dependencias).
- Manual en lenguaje simple: [`MANUAL.md`](../MANUAL.md)
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
         [Módulo 8: Orders & Execution]
         Orden enviada al exchange
         Stop Loss / Take Profit automáticos
                    ↓
         [Módulo 9: Alerts]
         Notificaciones por email o webhook
```

El [Módulo 1 (Auth)](M01-AUTH.md) protege el acceso a todo el sistema. Sin estar autenticado, no se puede usar ningún módulo.
El [Módulo 10 (Billing)](M10-BILLING.md) se apoya en el historial de órdenes y ejecuciones del [Módulo 8](M08-ORDERS-EXECUTION.md) para calcular el fee de performance.

### Estado real del flujo (verificado en el código el 2026-10-07)

El diagrama de arriba describe el objetivo. Hoy:

- **Scheduler ([M2](M02-MARKET-DATA.md)):** actualiza velas y features de los bots `running`/`paused`, pero **no genera señales ni órdenes**.
- **Señales ([M7](M07-BOTS-SIGNALS.md)):** se generan **a mano** con `POST /api/signals/generate`.
- **Órdenes ([M8](M08-ORDERS-EXECUTION.md)):** se crean con `POST /api/orders`; no existe un paso automático "señal aprobada → orden".
- **Stop Loss / Take Profit:** la señal los calcula, pero **no hay ejecución automática** de SL/TP tras la entrada.
- **Alertas ([M9](M09-ALERTS.md)):** se disparan solas con señales y órdenes; las de precio solo con evaluación manual; `pnl` y `drawdown` no se evalúan.

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
| 1 | Alta | Cerrar el lazo de automatización: señales automáticas por vela → orden desde la señal → SL/TP automáticos | [M7](M07-BOTS-SIGNALS.md), [M8](M08-ORDERS-EXECUTION.md), [M2](M02-MARKET-DATA.md) (scheduler) |
| 2 | Alta | Tests donde no hay ninguno: market, strategies, **orders**, alerts | [M2](M02-MARKET-DATA.md), [M5](M05-STRATEGIES.md), [M8](M08-ORDERS-EXECUTION.md), [M9](M09-ALERTS.md) |
| 3 | Alta | Seguridad: validar URL del webhook (SSRF) y ampliar el rate limit (hoy solo en auth) | [M9](M09-ALERTS.md), [M1](M01-AUTH.md), [M6](M06-AI-AGENT.md) |
| 4 | Alta | Salvaguardas para `live`: tamaño máximo, cancelación y reconciliación con el exchange | [M8](M08-ORDERS-EXECUTION.md) |
| 5 | Media | Scheduler fuera del proceso web (o con *lock*) y relleno de huecos de velas | [M2](M02-MARKET-DATA.md) |
| 6 | Media | Sincronizar balances con el exchange y derivar `closing_equity` de ellos; registrar cobros del fee | [M4](M04-ACCOUNTS-PORTFOLIO.md), [M10](M10-BILLING.md) |
| 7 | Media | Backtesting para validar el edge antes de pasar a live | [M5](M05-STRATEGIES.md) |

---

## Cache-busting JS (global)

Todo `<script>` (y el CSS) lleva `?v={{ sv }}`; `sv` cambia en cada reinicio del servidor. Reglas completas en el skill [`web-ui`](../.claude/skills/web-ui/SKILL.md).

---

## Mapa de páginas web

| Rol | Páginas |
|---|---|
| Usuario | `/login`, `/dashboard`, `/profile`, `/market/symbols`, `/market/candles`, `/features`, `/portfolio`, `/strategies`, `/agent`, `/bots`, `/orders`, `/alerts` |
| Admin | `/admin/exchanges`, `/admin/symbols`, `/admin/timeframes`, `/admin/candles/ingest`, `/admin/feature-sets`, `/admin/accounts`, `/admin/strategies`, `/admin/bots`, `/admin/orders`, `/admin/alerts`, `/admin/telegram`, `/admin/investors`, `/admin/managed-accounts`, `/admin/billing` |
| Inversor | `/investor/dashboard` |

Comprar/Vender vive en el [Módulo 8 — Orders & Execution](M08-ORDERS-EXECUTION.md).

---

## Archivos de infraestructura críticos (nunca romper)

Listado y cuándo tocar cada uno: skill [`backend-core`](../.claude/skills/backend-core/SKILL.md) → "Archivos de infraestructura críticos".

---

## Checklist al crear un módulo nuevo

Checklist completo (BD → domain → infra → services → providers → REST → web → docs): skill [`new-module`](../.claude/skills/new-module/SKILL.md). Al cerrar: skill [`update-specs`](../.claude/skills/update-specs/SKILL.md).

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

Ver [`MANUAL.md`](../MANUAL.md) Parte 4 para explicación completa de edge, capital y rutas de negocio.
