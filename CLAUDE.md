# Trading AI API

Backend de **trading asistido por IA**. El objetivo es quitar el sesgo emocional del trader: el sistema solo propone (y ejecuta) operaciones que pasan reglas objetivas.

**Qué hace, de punta a punta:** descarga velas OHLCV de exchanges (ccxt) → calcula indicadores y régimen de mercado → un agente LLM evalúa la operación contra la estrategia → un bot emite la señal (BUY/SELL/HOLD con entry/SL/TP) → se crea la orden (paper o live) → se disparan alertas → a los inversores con cuenta administrada se les cobra un performance fee.

**Reglas de negocio que el código debe respetar siempre:**
1. **Filtro de régimen:** tendencia (HH/HL) vs. rango lateral; cada estrategia declara en qué régimen opera.
2. **Regla del 1 %:** nunca arriesgar más del 1 % del capital por operación.
3. **Tamaño de posición:** `capital × %riesgo / |entrada − stop_loss|`.
4. **Riesgo/beneficio mínimo 2:1**; si no se cumple, la señal se rechaza (`approved = 0`).

Stack: Python 3.12 · FastAPI 0.128 · SQLAlchemy 2 (**síncrono**, PyMySQL) · MySQL 8 · Jinja2 (páginas web server-side) · ccxt 4.4 · LLM multi-provider (`LLM_PROVIDER` = openai | anthropic | xai | deepseek | gemini | ollama) · uv.

Explicación conceptual en lenguaje simple: [`MANUAL.md`](MANUAL.md). Setup técnico: [`README.md`](README.md).

## Specs: la fuente de verdad

**Antes de tocar código de un módulo, lee [`specs/_ROOT.md`](specs/_ROOT.md) y luego la spec del módulo.** Cada spec trae descripción, páginas (usuario vs admin), decisiones, avance, mejoras, mapa técnico (tablas, archivos, endpoints) y gotchas. No codear sin leerla.

| Módulo | Spec | Código |
|---|---|---|
| M1 — Auth & Web UI | [M01-AUTH.md](specs/M01-AUTH.md) | `app/modules/users`, `web`, `mailer` |
| M2 — Market Data | [M02-MARKET-DATA.md](specs/M02-MARKET-DATA.md) | `app/modules/market`, `scheduler` |
| M3 — Feature Engineering | [M03-FEATURE-ENGINEERING.md](specs/M03-FEATURE-ENGINEERING.md) | `app/modules/features` |
| M4 — Accounts & Portfolio | [M04-ACCOUNTS-PORTFOLIO.md](specs/M04-ACCOUNTS-PORTFOLIO.md) | `app/modules/accounts` |
| M5 — Strategies | [M05-STRATEGIES.md](specs/M05-STRATEGIES.md) | `app/modules/strategies` |
| M6 — AI Agent / Models | [M06-AI-AGENT.md](specs/M06-AI-AGENT.md) | `app/modules/agent` |
| M7 — Bots & Signals | [M07-BOTS-SIGNALS.md](specs/M07-BOTS-SIGNALS.md) | `app/modules/bots` |
| M8 — Orders & Execution | [M08-ORDERS-EXECUTION.md](specs/M08-ORDERS-EXECUTION.md) | `app/modules/orders` |
| M9 — Alerts | [M09-ALERTS.md](specs/M09-ALERTS.md) | `app/modules/alerts` |
| M10 — Billing & Managed Accounts | [M10-BILLING.md](specs/M10-BILLING.md) | `app/modules/billing` |

Inicio de sesión: el usuario dirá **"comenzamos Módulo X"** o **"continuamos donde quedamos"** → leer `_ROOT.md` + la spec correspondiente antes de proponer nada. Si hay algo nuevo en el entorno (p. ej. "instalé X"), lo dirá directamente.

## Skills: léelos antes de generar código

Viven en [`.claude/skills/`](.claude/skills/). Se cargan bajo demanda; carga el que corresponda **antes** de escribir, nunca después.

| Skill | Cuándo |
|---|---|
| [`backend-core`](.claude/skills/backend-core/SKILL.md) | Crear o modificar módulos, servicios, repositorios, providers. Estructura real del repo y reglas de capas |
| [`architecture`](.claude/skills/architecture/SKILL.md) | Decidir patrones (Repository, ServiceResult, Factory), SOLID, sub-modularización |
| [`api-standards`](.claude/skills/api-standards/SKILL.md) | Crear endpoints, respuestas, códigos de error, `error_messages.py` |
| [`code-style`](.claude/skills/code-style/SKILL.md) | Escribir cualquier archivo Python |
| [`database`](.claude/skills/database/SKILL.md) | SQL, seeds, migraciones, modelos ORM, consultar el esquema y los ENUMs |
| [`security`](.claude/skills/security/SKILL.md) | Auth, roles, inputs de usuario, credenciales, cookies, CSP |
| [`web-ui`](.claude/skills/web-ui/SKILL.md) | Páginas Jinja2, JS en `/static/`, CSS, CSP y cache-busting |
| [`testing`](.claude/skills/testing/SKILL.md) | Solo cuando el usuario pida tests |
| [`new-module`](.claude/skills/new-module/SKILL.md) | Checklist para crear un módulo o recurso nuevo de punta a punta |
| [`update-specs`](.claude/skills/update-specs/SKILL.md) | Al cerrar un módulo o feature significativa: actualizar spec, `_ROOT.md` y `MANUAL.md` |

## Comandos

Funcionan en macOS, Linux y Windows (Git Bash) gracias a `uv`:

```bash
uv sync                                                    # instalar dependencias
uv run uvicorn app.main:app --reload                       # servidor de desarrollo (http://localhost:8000, Swagger en /docs)
uv run python -m pytest tests/<modulo>/test_<x>.py -v      # tests de UN archivo
```

- **NUNCA** correr `pytest tests/` completo salvo que el usuario lo pida.
- **No crear tests por defecto** (gastan tokens): solo cuando el usuario los pida.
- **NUNCA** hacer login con `curl` al depurar: rota `token_current_jti` e invalida la sesión del navegador.
- MySQL (CLI, seeds, migraciones): ver el skill `database`.

## Arquitectura en 30 segundos

Screaming Architecture: un paquete por dominio en `app/modules/<modulo>/`, cada uno con las mismas capas:

```
rest/<recurso>/      routes.py · schemas.py · error_messages.py   ← mensajes de UI, HTTP
providers/           <Modulo>ServiceFactory(session)              ← wiring / DI
services/<recurso>/  un servicio por caso de uso → ServiceResult[T]
domain/              entidades puras + contratos de repositorio
infrastructure/      modelos SQLAlchemy + SqlAlchemy<X>Repository
```

Transversal en `app/common/` (config, contracts, http, security, utils, audit, logging) y `app/extensions/db/` (engine, `get_db`, `models_registry`). Detalle completo en el skill `backend-core`.

## Reglas no negociables

1. Capas: `rest → services → domain ← infrastructure`. Domain no importa nada de FastAPI ni de SQLAlchemy.
2. Los servicios devuelven siempre `ServiceResult` (`ok(data)` / `fail(code="SCREAMING_SNAKE", http_status=...)`). **Nunca** lanzan excepciones de negocio ni definen textos de UI; los textos van en `rest/<recurso>/error_messages.py`.
3. Las rutas responden siempre con los helpers de `app.common.http` (`send`, `build_*_response`). En éxito `errorCode` = 200/201, nunca 0; los errores se detectan con `errorCode >= 400`.
4. Transacciones: el **servicio** es la frontera transaccional (`self._session.commit()`); los repositorios hacen `add`/`flush`, nunca `commit`.
5. Todo modelo ORM nuevo se registra en `app/extensions/db/models_registry.py`; todo router nuevo en `app/app_factory.py`.
6. No hardcodear IDs de rol: `settings.AUTH_USER_ROLE_ID`, `AUTH_ADMIN_ROLE_ID`, `AUTH_INVESTOR_ROLE_ID`.
7. Fechas con `utc_now()` de `app.common.utils`, nunca `datetime.now(...)` directo.
8. Precios, cantidades y balances: `DECIMAL(30,12)` en MySQL, `TIMESTAMP(6)` para fechas, `BIGINT` para IDs.
9. Páginas web: sin handlers inline (`onclick`…) por la CSP, y todo `<script>` nuevo lleva `?v={{ sv }}`. Detalle en `web-ui`.
10. Rutas REST que comparten nombre con una página web llevan prefijo `/api/<recurso>`.

## Cierre de sesión (obligatorio)

Al terminar un módulo o una feature significativa, ejecutar el skill [`update-specs`](.claude/skills/update-specs/SKILL.md): spec del módulo + tabla de `specs/_ROOT.md` + sección en `MANUAL.md`. Si quedó algo sin actualizar, avisar al usuario antes de cerrar.

## Mapa de la documentación

| Archivo | Para qué |
|---|---|
| `CLAUDE.md` | Este archivo: qué es el proyecto, reglas y dónde está cada cosa |
| [`specs/_ROOT.md`](specs/_ROOT.md) | Índice de módulos, estado, flujo, dependencias, mapa de páginas, prioridades |
| `specs/MNN-*.md` | Fuente de verdad de cada módulo |
| [`.claude/skills/`](.claude/skills/) | Cómo se escribe el código en este repo (bajo demanda) |
| [`.claude/db_schema.sql`](.claude/db_schema.sql) + [`migrations/`](migrations/) | Esquema de la BD (se consulta vía skill `database`, no se carga siempre) |
| [`MANUAL.md`](MANUAL.md) | Explicación para humanos, sin tecnicismos |
| [`README.md`](README.md) | Instalación y ejecución |
