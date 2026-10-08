# Trading App

Aplicación de **trading asistido por IA** (nombre temporal: **trading-app**). Este repo contiene la aplicación completa: API REST **headless** (FastAPI), frontend React (`frontend/`), jobs y base de datos. El objetivo es quitar el sesgo emocional del trader: el sistema solo propone (y ejecuta) operaciones que pasan reglas objetivas.

**Qué hace, de punta a punta:** descarga velas OHLCV de exchanges (ccxt) → calcula indicadores y régimen de mercado → un agente LLM evalúa la operación contra la estrategia → un bot emite la señal (BUY/SELL/HOLD con entry/SL/TP) → se crea la orden (paper o live) → se disparan alertas → a los inversores con cuenta administrada se les cobra un performance fee.

**Reglas de negocio que el código debe respetar siempre:**
1. **Filtro de régimen:** tendencia (HH/HL) vs. rango lateral; cada estrategia declara en qué régimen opera.
2. **Regla del 1 %:** nunca arriesgar más del 1 % del capital por operación.
3. **Tamaño de posición:** `capital × %riesgo / |entrada − stop_loss|`.
4. **Riesgo/beneficio mínimo 2:1**; si no se cumple, la señal se rechaza (`approved = 0`).

Stack backend: Python 3.12 · FastAPI 0.128 · SQLAlchemy 2 (**síncrono**, PyMySQL) · MySQL 8 · ccxt 4.4 · LLM multi-provider (`LLM_PROVIDER` = openai | anthropic | xai | deepseek | gemini | ollama) · uv. Jinja2 solo para las plantillas de correo.

Stack frontend: React 19 · Vite 8 · TypeScript 6 · TanStack Router (hash history) + TanStack Query · shadcn (`base-vega`, sobre Base UI) · Tailwind 4 · react-hook-form + zod 4 · npm.

Explicación conceptual en lenguaje simple: [`docs/MANUAL.md`](docs/MANUAL.md). Setup técnico: [`README.md`](README.md).

## Specs: la fuente de verdad

**Antes de tocar código de un módulo, lee [`specs/_ROOT.md`](specs/_ROOT.md) y luego la spec del módulo.** Cada spec trae descripción, páginas (usuario vs admin), decisiones, avance, mejoras, mapa técnico (tablas, archivos, endpoints) y gotchas. No codear sin leerla.

| Módulo | Spec | Código |
|---|---|---|
| M1 — Auth & Frontend | [M01-AUTH.md](specs/M01-AUTH.md) | `app/modules/users`, `mailer` · `frontend/` (`auth`, `app-shell`, `profile`, `dashboard`) |
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
| [`frontend`](.claude/skills/frontend/SKILL.md) | **Cualquier cambio en `frontend/`**: estructura, rutas, api → queries → mutations, formularios, tablas, diálogos, env |
| [`shadcn`](.claude/skills/shadcn/SKILL.md) | Añadir, componer o depurar componentes shadcn (`base-vega` / Base UI) |
| [`tailwind-css-patterns`](.claude/skills/tailwind-css-patterns/SKILL.md) | Layout y estilos con Tailwind 4 |
| [`typescript-advanced-types`](.claude/skills/typescript-advanced-types/SKILL.md) | Tipos genéricos o utilitarios complejos en el front |
| [`copy-ux-writer`](.claude/skills/copy-ux-writer/SKILL.md) | Cualquier texto que vea una persona: UI, `error_messages.py`, correos, Telegram |
| [`frontend-design`](.claude/skills/frontend-design/SKILL.md) | Pantallas nuevas con diseño propio (sin cambiar la paleta) |
| [`testing`](.claude/skills/testing/SKILL.md) | Solo cuando el usuario pida tests |
| [`new-module`](.claude/skills/new-module/SKILL.md) | Checklist para crear un módulo o recurso nuevo de punta a punta (backend + front) |
| [`update-specs`](.claude/skills/update-specs/SKILL.md) | Al cerrar un módulo o feature significativa: actualizar spec, `_ROOT.md` y `docs/MANUAL.md` |

## Comandos

Funcionan en macOS, Linux y Windows (Git Bash) gracias a `uv`:

```bash
uv sync                                                    # instalar dependencias
uv run uvicorn app.main:app --reload                       # servidor de desarrollo (http://localhost:8000, Swagger en /docs)
uv run python -m pytest tests/<modulo>/test_<x>.py -v      # tests de UN archivo
uv run alembic revision --autogenerate -m "mNN ..."        # generar migración desde los modelos
uv run alembic upgrade head                                # aplicar migraciones pendientes
uv run python -m database.seeds [nombre ...]                        # datos iniciales (idempotente; --list para ver)

npm install                                                # dependencias del front (raíz del repo)
npm run dev                                                # front en http://localhost:5193 (proxy /api → :8000)
npm run check-types                                        # tsr generate + tsc -b (verificación del front)
npm run build                                              # build de producción → frontend/dist
```

- En desarrollo corren **dos procesos**: la API (`uvicorn`, :8000) y el front (`npm run dev`, :5193). El front llama a `/api/*` y Vite lo reenvía a la API (mismo origen → la cookie de sesión funciona sin CORS).
- Variables del front en **`.env_frontend`** (copiar de `.env_frontend.example`), nunca en el `.env` del backend.

- **NUNCA** correr `pytest tests/` completo salvo que el usuario lo pida.
- **No crear tests por defecto** (gastan tokens): solo cuando el usuario los pida.
- **NUNCA** hacer login con `curl` al depurar: rota `token_current_jti` e invalida la sesión del navegador.
- **Comandos `uv` / `python` / `npm` de alto impacto los ejecuta el usuario, no el agente.** Esto incluye: `uv sync`, `uv add`/`uv remove`, `uv lock`, `npm install`/`npm add`/`npx shadcn add`, levantar el servidor o `npm run dev`, scripts o seeds que escriban en la BD, cualquier comando `alembic` que toque la BD (`revision --autogenerate`, `upgrade`, `downgrade`, `stamp`, `check`), jobs que llamen a exchanges o al LLM (coste/órdenes reales), y la suite de tests completa. El agente debe darle el comando exacto (sugiriendo el prefijo `! <comando>` para que la salida llegue a la conversación) y **esperar su respuesta** antes de continuar. Ante la duda sobre si un comando es de alto impacto, tratarlo como tal.
- MySQL (CLI), migraciones con Alembic y seeds en Python (`database/seeds/<dominio>.py`): ver el skill `database`. El esquema lo definen los modelos ORM; todo cambio va en una revisión de `database/migrations/versions/`.

### Migraciones (Alembic)

Flujo para cualquier cambio de esquema. Los comandos los ejecuta el usuario:

1. El agente crea o modifica el modelo en `app/modules/<modulo>/infrastructure/` (y lo registra en `models_registry.py` si es nuevo).
2. **Generar:** `uv run alembic revision --autogenerate -m "mNN descripcion"` → crea un archivo en `database/migrations/versions/` con `upgrade()` y `downgrade()`.
3. **Revisar el archivo generado antes de aplicarlo** (lo hace el agente):
   - en tablas nuevas incluye CHECKs, comentarios y defaults del modelo; en tablas existentes **no** detecta CHECKs añadidos/quitados ni cambios de `server_default`: añadirlos a mano (`op.create_check_constraint(...)`, `op.alter_column(...)`);
   - quitar operaciones no deseadas (`drop_index`, `modify_type`… sobre tablas que no se tocaron);
   - completar `MOTIVO:` en el docstring y dejar un `downgrade()` real.
4. **Aplicar:** `uv run alembic upgrade head`.

Útiles: `alembic upgrade head --sql` (ver el SQL sin ejecutar) · `alembic current` (revisión aplicada) · `alembic downgrade -1` (deshacer la última) · `alembic check` (¿modelos y BD coinciden?).

Si `alembic check` muestra diferencias que no vienen del cambio actual, la revisión generada las incluirá todas: primero hay que alinear los modelos con la BD real (la BD manda) y después generar.

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

La API es **headless**: todas las rutas REST viven bajo `settings.API_PREFIX` (`/api`), salvo `/health`; ningún endpoint devuelve HTML ni redirige a páginas. Todo error (incluidos 401, 404, 422 y 429) sale con el envelope `{msg, errorCode, data}` y `msg` en español listo para la UI.

## Frontend (`frontend/`)

SPA React que consume la API. Las configs viven en la raíz del repo (`package.json`, `vite.config.ts`, `tsr.config.json`, `tsconfig*.json`, `components.json`); el código en `frontend/`:

```
frontend/
  index.html · public/
  src/
    main.tsx · app.tsx · router.ts (hash history: /#/bots) · index.css (tokens de color — no cambiar la paleta)
    routeTree.gen.ts          generado (no editar)
    routes/                   rutas finas: solo conectan URL → página
      _auth/login · _app.tsx (shell autenticado) · _app/<pagina> · _app/admin/* (rol admin) · _app/investor/* (rol investor)
    modules/
      ui/                     primitivas shadcn (Base UI)
      shared/                 api-client, envelope, DataTable, OptionSelect, StatCard, format, layouts
      app-shell/              sidebar (navSections), nav-user, breadcrumb
      auth/ · profile/ · dashboard/
      market/ · features/ · accounts/ · strategies/ · agent/ · bots/ · orders/ · alerts/ · billing/   (uno por módulo M2–M10)
        api/<x>.api.ts · hooks/use-<x>-queries.ts · hooks/use-<x>-mutations.ts · lib/ · components/ · pages/
```

Sesión: cookie HttpOnly (`credentials: 'include'`), sin tokens en JS. Roles por `role_code` (`user` | `admin` | `investor`). Detalle y checklist de página nueva en el skill `frontend`.

## Reglas no negociables

1. Capas: `rest → services → domain ← infrastructure`. Domain no importa nada de FastAPI ni de SQLAlchemy.
2. Los servicios devuelven siempre `ServiceResult` (`ok(data)` / `fail(code="SCREAMING_SNAKE", http_status=...)`). **Nunca** lanzan excepciones de negocio ni definen textos de UI; los textos van en `rest/<recurso>/error_messages.py`.
3. Las rutas responden siempre con los helpers de `app.common.http` (`send`, `build_*_response`). En éxito `errorCode` = 200/201, nunca 0; los errores se detectan con `errorCode >= 400`.
4. `session.commit()` **solo en la capa repositorio** (base `SqlAlchemyRepository`). Los servicios no reciben `Session`: al final del caso de uso llaman `self._repo.commit()`, y si algo falla a mitad, `self._repo.rollback()`. Todos los repos de un request comparten sesión, así que un commit confirma todo de forma atómica.
5. Todo modelo ORM nuevo se registra en `app/extensions/db/models_registry.py`; todo router nuevo en `app/app_factory.py`.
6. No hardcodear IDs de rol: `settings.AUTH_USER_ROLE_ID`, `AUTH_ADMIN_ROLE_ID`, `AUTH_INVESTOR_ROLE_ID`.
7. Fechas con `utc_now()` de `app.common.utils`, nunca `datetime.now(...)` directo.
8. Precios, cantidades y balances: `DECIMAL(30,12)` en MySQL, `TIMESTAMP(6)` para fechas, `BIGINT` para IDs.
9. FastAPI no renderiza vistas: ni Jinja2 para páginas, ni `StaticFiles`, ni redirects a páginas. Toda UI va en `frontend/` (skill `frontend`).
10. Toda ruta REST vive bajo `/api` (prefijo global en `app_factory.py`): los routers declaran `prefix="/<recurso>"`, **sin** `/api`.
11. Front: datos siempre por `api/<x>.api.ts` + TanStack Query (nunca `fetch` directo), los textos de error vienen del backend (`error_messages.py`), solo tokens de color de `index.css`.

## Cierre de sesión (obligatorio)

Al terminar un módulo o una feature significativa, ejecutar el skill [`update-specs`](.claude/skills/update-specs/SKILL.md): spec del módulo + tabla de `specs/_ROOT.md` + sección en `docs/MANUAL.md`. Si quedó algo sin actualizar, avisar al usuario antes de cerrar.

## Mapa de la documentación

| Archivo | Para qué |
|---|---|
| `CLAUDE.md` | Este archivo: qué es el proyecto, reglas y dónde está cada cosa |
| [`specs/_ROOT.md`](specs/_ROOT.md) | Índice de módulos, estado, flujo, dependencias, mapa de páginas, prioridades |
| `specs/MNN-*.md` | Fuente de verdad de cada módulo |
| [`frontend/`](frontend/) + skill `frontend` | Código y convenciones del front React |
| [`.claude/skills/`](.claude/skills/) | Cómo se escribe el código en este repo (bajo demanda) |
| [`database/migrations/versions/`](database/migrations/versions/) + modelos ORM (`app/modules/*/infrastructure/*_model.py`) | Esquema de la BD (se consulta vía skill `database`, no se carga siempre) |
| [`docs/MANUAL.md`](docs/MANUAL.md) | Explicación para humanos, sin tecnicismos |
| [`README.md`](README.md) | Instalación y ejecución (API + front) |
