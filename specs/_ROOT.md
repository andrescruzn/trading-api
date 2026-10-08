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
- Orden de dependencias, archivos de infraestructura críticos y checklist de módulo nuevo: [más abajo](#orden-de-dependencias).
- Manual en lenguaje simple: [`MANUAL.md`](../MANUAL.md)
- Esquema de base de datos: `.claude/db_schema.sql`

### Cómo usar estas specs
- Al iniciar cada sesión: leer este archivo para saber en qué módulo estamos y luego la spec del módulo (se leen bajo demanda, no se importan en `CLAUDE.md`).
- **Leer la spec del módulo ANTES de codear** para no pisar lo anterior (tablas, archivos y endpoints están en su sección "Detalle técnico").
- Al terminar un módulo o una feature significativa: actualizar su spec (estado, entregables, avance, decisiones, mejoras), la tabla de arriba, `MANUAL.md` y `.claude/memory/MEMORY.md`.

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

- `templates.env.globals["sv"] = str(int(time.time()))` en `app/modules/web/routes.py`
- Todos los `<script src="...">` usan `?v={{ sv }}` — fuerza recarga tras reinicio del servidor
- Aplica a TODOS los templates (`base_app.html` incluido); el CSS también se versiona (`app.css?v={{ sv }}` en `base.html`)

---

## Archivos de infraestructura críticos (nunca romper)

| Archivo | Qué hace |
|---------|---------|
| `app/extensions/db/models_registry.py` | Importa TODOS los modelos ORM (side-effect). Al crear modelo nuevo → agregar aquí |
| `app/app_factory.py` | Registra middlewares + routers. Al crear router nuevo → agregar aquí |
| `app/modules/web/routes.py` | Páginas HTML. Al crear página nueva → agregar ruta aquí |
| `app/common/security/security_headers.py` | CSP. Al crear rutas web nuevas (`/market/`, `/admin/`, etc.) → agregar prefijo a `web_prefixes` |
| `app/extensions/db/session.py` | `get_db()` dependency de FastAPI |
| `app/common/contracts/service_result.py` | `ServiceResult[T]` — contrato de todos los servicios |
| `app/common/http/response_builder.py` | `build_list_response`, `build_created_response`, etc. |

---

## Checklist al crear un módulo nuevo

1. [ ] Crear `domain/` — entidades + interfaces repositorio
2. [ ] Crear `infrastructure/` — modelos ORM + impl repositorios
3. [ ] Registrar modelos ORM en `models_registry.py`
4. [ ] Crear `services/` — lógica, retorna ServiceResult
5. [ ] Crear `providers/` — Factory + `get_<modulo>_factory()`
6. [ ] Crear `rest/` — routes, schemas, error_messages por recurso
7. [ ] Registrar router(es) en `app_factory.py`
8. [ ] Si hay páginas web: agregar en `web/routes.py`
9. [ ] Si las páginas son nuevos prefijos (ej: `/features/`): agregar a `_is_web_route()` en `security_headers.py`
10. [ ] Crear templates HTML + JS en `static/js/<modulo>/`
11. [ ] Si hay seed: `seeds/seed_<modulo>.sql` (idempotente)

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
