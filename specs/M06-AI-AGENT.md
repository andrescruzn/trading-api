# Módulo 6 — AI Agent / Models (Agente de IA) ✅ COMPLETO

← [Índice de módulos](_ROOT.md)

## Ficha

| Campo | Valor |
|---|---|
| Estado | ✅ Completo |
| Avance (alcance original) | 100 % — 13/13 entregables |
| Madurez (estimada) | 76 % — ver [Avance](#avance) |
| Tablas | `models`, `model_runs` (R/W); `strategies`, `accounts`, `account_balances`, `candles`, `candle_features`, `symbols`, `timeframes` (R) |
| Depende de | [M2](M02-MARKET-DATA.md), [M3](M03-FEATURE-ENGINEERING.md), [M4](M04-ACCOUNTS-PORTFOLIO.md), [M5](M05-STRATEGIES.md) |
| Lo usan | [M7](M07-BOTS-SIGNALS.md) (`GenerateSignalService` instancia el `AnalyzeService`) |
| Prefijo API | `/api/agent`, `/api/models`, `/api/model-runs` |
| Frontend | `frontend/src/modules/agent` |
| Última revisión | 2026-10-08 |

## Descripción

**En palabras simples:** Es el cerebro. Toma todo lo que saben los otros módulos y decide si una operación es buena o mala.

**Qué hace:**
1. Revisa en qué régimen está el mercado (tendencia o rango) — si no coincide con la estrategia, cancela
2. Valida que se cumplan todas las reglas de la estrategia — si falta una, cancela
3. Consulta al LLM para calcular los niveles de entrada, Stop Loss y Take Profit; Python ejecuta la fórmula de posición: `Capital × risk_pct / |entrada − SL|`
4. Verifica que la ganancia proyectada sea al menos el doble del riesgo (ratio 2:1 configurable) — si no, cancela
5. Da un veredicto final: **APROBADA** o **RECHAZADA**, con todos los detalles de la operación

**Tecnología:** Soporta múltiples proveedores de LLM: OpenAI, Anthropic (Claude), xAI (Grok), DeepSeek, Gemini y Ollama (local). El proveedor se configura con la variable de entorno `LLM_PROVIDER`.

## Páginas

Hash routing: la URL real es `/#/<ruta>`.

**Páginas — Usuario (cualquier usuario autenticado):**
- `/#/agent` — "Agente de IA": panel de análisis: selecciona símbolo, timeframe, estrategia y cuenta, lanza el análisis y ve el resultado (APROBADA/RECHAZADA con entry, SL, TP, tamaño de posición y resumen de indicadores)

**Páginas — Administrador (solo admin):**
- No hay página admin específica en este módulo; la gestión de modelos ML se hace vía API

## Entregables

Tablas: `models`, `model_runs` (predictions → Module 7, requiere bot_id)

Entregables:
- ✅ Multi-provider LLM: openai, anthropic, gemini, xai (Grok), deepseek, ollama
- ✅ LLMClientFactory: crea el cliente correcto según LLM_PROVIDER en settings
- ✅ OpenAICompatibleClient: cubre openai, xai, deepseek, gemini, ollama (un solo cliente)
- ✅ AnthropicLLMClient: cliente dedicado para Claude
- ✅ Prompt Maestro con 4 fases determinísticas + LLM para entry/SL/TP
- ✅ Fórmula de posición en Python: Capital × risk_pct / |entry − SL|
- ✅ Filtro R/R configurable (AGENT_MIN_RR_RATIO, default 2.0)
- ✅ AGENT_MASTER_PROMPT configurable en settings (con default robusto)
- ✅ CRUD modelos ML (tabla `models`): list, get, create, update
- ✅ CRUD model_runs (tabla `model_runs`): list, create, finish
- ✅ `POST /api/agent/analyze` — Prompt Maestro completo
- ✅ Web UI: `/#/agent` — Página de análisis con formulario y resultado visual (React desde 2026-10-08)
- ✅ 20 tests unitarios pasando (LLM 100% mockeado, sin llamadas reales)

## Decisiones de diseño

| Decisión | Motivo | Alternativa descartada |
|---|---|---|
| Prompt Maestro en **4 fases**: régimen → reglas → LLM → R/R; las fases 1, 2 y 4 son **determinísticas** en Python | El LLM no decide si se opera, solo propone niveles; los filtros son reproducibles y auditables | Dejar que el LLM decida todo |
| El LLM solo propone **entry / SL / TP**; el tamaño de posición lo calcula Python: `Capital × risk_pct / \|entry − SL\|` | Los LLM fallan en aritmética; el riesgo (regla del 1 %) no puede depender de ellos | Pedir el tamaño de posición al LLM |
| Un único `OpenAICompatibleClient` para openai, xai, deepseek, gemini y ollama; cliente dedicado `AnthropicLLMClient` para Claude | Esos cinco proveedores comparten la API de OpenAI; menos código y se cambia de proveedor con una variable | Un cliente por proveedor |
| `LLMClientFactory.create(settings)` se llama **por request** | Respeta cambios de configuración en caliente | Cliente singleton al arrancar |
| Ratio R/R mínimo configurable (`AGENT_MIN_RR_RATIO`, 2.0 por defecto) | Cada despliegue ajusta su umbral sin tocar código | Constante en el código |
| `AGENT_MASTER_PROMPT` configurable por variable de entorno, con un valor por defecto robusto | Iterar el prompt sin redeploy | Prompt embebido |
| `POST /api/agent/analyze` devuelve **200 siempre** (APROBADA o RECHAZADA) | Un rechazo es un resultado de negocio válido, no un error HTTP | 4xx para rechazos |
| `regime_required = null` acepta cualquier régimen | Estrategias agnósticas al régimen | Régimen siempre obligatorio |
| La respuesta del LLM se parsea tolerando que venga envuelta en un bloque de código markdown; un fallo de parseo se registra | Los modelos suelen envolver el JSON en markdown | Exigir JSON puro |
| Tests con el LLM **100 % mockeado** | Rápidos, deterministas y sin coste ni red | Llamadas reales en CI |
| `predictions` diferida a [M7](M07-BOTS-SIGNALS.md) | Requiere `bot_id` | Predicciones sin bot |

## Avance

| Métrica | Valor | Evidencia |
|---|---|---|
| Alcance original | **100 %** (13/13) | Multi-provider, 4 fases, fórmula de posición, filtro R/R, CRUD de modelos/runs, endpoint y UI |
| Madurez | **≈ 76 %** | Funcionalidad 85 · Tests 75 · Seguridad 75 · Operación 70 |

- **Funcionalidad (85):** `models` / `model_runs` son un registro (CRUD); **no hay entrenamiento ni inferencia ML** y `predictions` no se usa.
- **Tests (75):** 20 tests de `AnalyzeService` con LLM mockeado; sin tests de `LLMClientFactory`, clientes ni REST.
- **Seguridad (75):** `LLM_API_KEY` solo por entorno; sin límite de uso sobre un endpoint que consume LLM de pago, y `POST /api/agent/analyze` **no verifica que `account_id` pertenezca al usuario** (cualquier usuario autenticado puede analizar con el capital de otra cuenta).
- **Operación (70):** configurable por entorno; sin reintentos, *timeouts* ni *fallback* de proveedor documentados.

## Posibles mejoras

| Prioridad | Mejora | Esfuerzo |
|---|---|---|
| Alta | Control de propiedad en `POST /api/agent/analyze`: rechazar (403/404) si `account_id` no es del usuario y no es admin (hoy la ruta solo exige token y `AnalyzeService` no recibe `user_id`) | S |
| Alta | Rate limit / cuota por usuario en `/api/agent/analyze` (cada llamada cuesta dinero y tiempo de LLM) | S |
| Alta | Validar la coherencia numérica de la salida del LLM (valores positivos, SL del lado correcto de `entry`, `entry` cercano al último cierre) y cubrirlo con tests | S |
| Alta | Persistir cada análisis (prompt, respuesta, versión del modelo) para auditoría y para medir el edge; la tabla `predictions` existe y no se usa | M |
| Media | *Timeout*, reintentos con *backoff* y proveedor de *fallback* en `LLMClientFactory` | M |
| Media | Cachear el análisis por `(símbolo, timeframe, vela, estrategia)` para no repetir llamadas dentro de la misma vela | S |
| Media | Tests de `LLMClientFactory`, de los dos clientes (con HTTP mockeado) y de las rutas REST | M |
| Baja | UI admin para `models` / `model_runs` (hoy solo API) | S |
| Baja | Prompts versionados por estrategia | M |

## Fuera de alcance y pendientes conocidos

- Entrenamiento/inferencia de modelos ML (`xgboost`/`lightgbm`/`sklearn`/`nn`): las tablas existen, no el pipeline.
- `predictions` (tabla sin modelo ORM ni servicio).
- UI para gestionar modelos ML (solo API).

## Detalle técnico

### Tablas en BD
| Tabla | Acción | Nota |
|-------|--------|------|
| `models` | WRITE | Modelos ML registrados (xgboost/lightgbm/sklearn/nn) |
| `model_runs` | WRITE | Ejecuciones de entrenamiento con métricas y params |
| `strategies` | READ | Para resolver estrategia en Prompt Maestro |
| `accounts` | READ | Para obtener capital disponible |
| `account_balances` | READ | Balance más reciente (base_currency) |
| `candles` | READ | Última vela del símbolo/timeframe |
| `candle_features` | READ | Últimas features calculadas del feature_set |
| `symbols` | READ | Para validar symbol_id |
| `timeframes` | READ | Para validar timeframe_id |

### Tablas que NO toca
- `predictions` (requiere bot_id de Módulo 7, diferida a ese módulo)
- `bots`, `signals`, `orders`, `users`, `roles`

### Modelos ORM (`app/modules/agent/infrastructure/`)
| Archivo | Clase ORM | Tabla |
|---------|-----------|-------|
| `ml_model_model.py` | `MLModelORM` | `models` |
| `model_run_model.py` | `ModelRunORM` | `model_runs` |

Registrados en: `app/extensions/db/models_registry.py`

### Dominio (`app/modules/agent/domain/`)
| Archivo | Contenido |
|---------|-----------|
| `analysis_result.py` | `AnalysisResult` + `RuleCheckDetail` — valor de retorno del Prompt Maestro |
| `ml_model_entity.py` | `MLModel` entity (types: xgboost/lightgbm/sklearn/nn) |
| `model_run_entity.py` | `ModelRun` entity (statuses: running/success/failed) |
| `ml_model_repository.py` | ABC interface `MLModelRepository` |
| `model_run_repository.py` | ABC interface `ModelRunRepository` |

### Repositorios
| Domain (interfaz) | Infrastructure (impl) |
|-------------------|-----------------------|
| `domain/ml_model_repository.py` | `infrastructure/ml_model_repository_impl.py` |
| `domain/model_run_repository.py` | `infrastructure/model_run_repository_impl.py` |

### LLM Clients (`app/modules/agent/llm/`)
| Archivo | Clase | Cubre |
|---------|-------|-------|
| `llm_client.py` | `LLMClient` (ABC) | Interfaz: `complete(system, user) -> str` |
| `openai_compatible_client.py` | `OpenAICompatibleClient` | openai, xai (Grok), deepseek, gemini, ollama |
| `anthropic_client.py` | `AnthropicLLMClient` | anthropic (Claude) |
| `llm_factory.py` | `LLMClientFactory` | Crea el cliente según `LLM_PROVIDER` en settings |

**Tabla de base_url por provider:**
- openai → `None` (usa default de la librería)
- xai → `https://api.x.ai/v1`
- deepseek → `https://api.deepseek.com`
- gemini → `https://generativelanguage.googleapis.com/v1beta/openai/`
- ollama → `http://localhost:11434/v1` (api_key="ollama")

### Servicios (`app/modules/agent/services/`)
| Subdir | Servicios |
|--------|-----------|
| `agent/` | `analyze_service.py` — Prompt Maestro (4 fases) |
| `models/` | `list_models_service.py`, `get_model_service.py`, `create_model_service.py`, `update_model_service.py` |
| `model_runs/` | `list_model_runs_service.py`, `create_model_run_service.py`, `finish_model_run_service.py` |

### Prompt Maestro — 4 fases (`AnalyzeService.analyze`)
1. **Fase 1 — Régimen:** `strategy.parameters.regime_required` vs `features.regime`. Si no coincide → RECHAZADA. `None` = acepta cualquier régimen.
2. **Fase 2 — Reglas:** evalúa cada `{indicator, operator, value}` contra features. Si ALGUNA falla → RECHAZADA.
3. **Fase 3 — LLM:** genera entry/SL/TP. Python calcula `position_size = (capital × risk_pct) / |entry − SL|`.
4. **Fase 4 — R/R:** `(TP − entry) / (entry − SL) >= AGENT_MIN_RR_RATIO` (default 2.0). Si no → RECHAZADA.

### Provider (`app/modules/agent/providers/agent_provider.py`)
- `AgentServiceFactory` — instancia repos propios + borrowed de strategies, accounts, features, market
- `LLMClientFactory.create(settings)` se llama por request (respeta cambios de config en runtime)

### Endpoints REST
| Método | Ruta | Auth | Nota |
|--------|------|------|------|
| POST | `/api/agent/analyze` | token (sin control de propiedad de `account_id`) | Prompt Maestro — retorna 200 siempre (APPROVED o REJECTED) |
| GET | `/api/models` | token | Lista modelos ML; filtro: `?status=active` |
| POST | `/api/models` | admin | Crea modelo ML |
| GET | `/api/models/{id}` | token | Detalle de modelo |
| PUT | `/api/models/{id}` | admin | Actualiza modelo (status/artifact_uri/meta) |
| GET | `/api/model-runs` | token | Lista runs; requiere `?model_id=X` |
| POST | `/api/model-runs` | admin | Crea run (status=running) |
| POST | `/api/model-runs/{id}/finish` | admin | Finaliza run (success/failed + metrics) |

Routers registrados en `app/app_factory.py` (dentro de `api_routers`, con `prefix=settings.API_PREFIX`; los routers declaran `/agent`, `/models`, `/model-runs`):
```python
from app.modules.agent.rest import agent_router, models_router, model_runs_router
```

### Frontend (`frontend/src/modules/agent/`)
| Ruta | Archivo de ruta | Página / componentes |
|-----|----------|----|
| `/#/agent` | `routes/_app/agent.lazy.tsx` | `pages/analyze.tsx` (`AgentAnalyzePage`) + `components/analysis-result-panel.tsx` |

- API: `api/agent.api.ts` (`api.post('/agent/analyze')`; el `/api` lo pone `VITE_API_URL`); mutation `hooks/use-agent-mutations.ts`; etiquetas `lib/agent-labels.ts`.
- Selects de símbolo, timeframe, estrategia y cuenta con las queries de `market`, `strategies` y `accounts` (muestran nombres, no IDs).
- `models` / `model_runs` siguen sin UI.

### Settings LLM/Agent (en `app/common/config/settings.py`)
```python
LLM_PROVIDER      # openai | anthropic | xai | deepseek | gemini | ollama (default: openai)
LLM_MODEL         # nombre del modelo (default: gpt-4o)
LLM_API_KEY       # clave del provider
LLM_BASE_URL      # override base_url (opcional)
LLM_TEMPERATURE   # (default: 0.1)
LLM_MAX_TOKENS    # (default: 1024)
AGENT_MIN_RR_RATIO  # ratio R/R mínimo (default: 2.0)
AGENT_MASTER_PROMPT # prompt del sistema configurable (env var)
```

## Gotchas críticos

- **Defaults del proveedor:** `LLM_PROVIDER=openai` y `LLM_MODEL=gpt-4o` si no se configuran. Para usar IA local hay que fijar `LLM_PROVIDER=ollama` y el modelo (p. ej. `gemma3:4b`, como indica `CLAUDE.md`) en `.env`.
- `POST /api/agent/analyze` responde 200 también cuando la operación es **RECHAZADA**: mirar el veredicto en `data`, no el código HTTP.
- **Hueco de seguridad:** `POST /api/agent/analyze` no comprueba que la cuenta (`account_id`) pertenezca al usuario; el front solo ofrece las cuentas propias, pero la API acepta cualquier ID (ver Posibles mejoras).
- `regime_required = None` acepta cualquier régimen (fase 1 no filtra).
- El `AnalyzeService` lo reutiliza [M7](M07-BOTS-SIGNALS.md) a través de `BotServiceFactory._build_analyze_service()`; un cambio de firma aquí rompe la generación de señales.

## Tests

- `tests/agent/test_analyze_service.py` — 20 tests unitarios, LLM 100% mockeado
  - `TestAnalyzeDataLoading` (6), `TestRegimeFilter` (3), `TestRulesValidation` (3)
  - `TestLLMIntegration` (4), `TestRRFilter` (2), `TestPositionSizing` (1), `TestFullApprovedPath` (1)
- **Huecos:** `LLMClientFactory`, `OpenAICompatibleClient`, `AnthropicLLMClient`, servicios de `models` / `model_runs` y rutas REST.

## Riesgos

- **Coste y latencia:** cada análisis es una llamada a un LLM de pago (salvo Ollama).
- **Salida no determinista:** el LLM propone niveles de precio; los filtros R/R y la fórmula de posición acotan el riesgo, pero un entry/SL absurdo pasaría si respeta el ratio.
- **Privacidad:** el contexto de mercado y el capital se envían al proveedor externo configurado.

## Historial

- **2026-03** — Módulo completado por un compañero: multi-provider, Prompt Maestro 4 fases, CRUD `models` / `model_runs`, UI `/agent`, 20 tests.
- **Posterior** — Panel de error y mejor manejo de errores en la página de análisis (commit `d8b2e43`).
- **2026-10-08** — API headless (/api), páginas migradas a React (frontend/).
