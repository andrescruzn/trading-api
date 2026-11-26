# Módulo 6 — AI Agent / Models (Agente de IA) ✅ COMPLETO

← [Índice de módulos](_ROOT.md)

## Ficha

| Campo | Valor |
|---|---|
| Estado | ✅ Completo |
| Avance (alcance original) | 100 % — 13/13 entregables (+ 4 de la auditoría de 2026-10-19) |
| Madurez (estimada) | 81 % — ver [Avance](#avance) |
| Tablas | `models`, `model_runs` (R/W); `strategies`, `accounts`, `account_balances`, `candles`, `candle_features`, `symbols`, `timeframes` (R) |
| Depende de | [M2](M02-MARKET-DATA.md), [M3](M03-FEATURE-ENGINEERING.md), [M4](M04-ACCOUNTS-PORTFOLIO.md), [M5](M05-STRATEGIES.md) |
| Lo usan | [M7](M07-BOTS-SIGNALS.md) (`GenerateSignalService` instancia el `AnalyzeService`; también el scheduler para las señales automáticas) |
| Prefijo API | `/api/agent`, `/api/models`, `/api/model-runs` |
| Frontend | Sin módulo propio desde 2026-10-08: se usa desde el detalle de cada agente ([M7](M07-BOTS-SIGNALS.md), "Analizar ahora") |
| Última revisión | 2026-10-19 (propiedad, rate limit y validación de la salida del LLM) |

## Descripción

**En palabras simples:** Es el cerebro. Toma todo lo que saben los otros módulos y decide si una operación es buena o mala.

**Qué hace:**
1. Revisa en qué régimen está el mercado (tendencia o rango) — si no coincide con la estrategia, cancela
2. Valida que se cumplan todas las reglas de la estrategia — si falta una, cancela
3. Consulta al LLM para calcular los niveles de entrada, Stop Loss y Take Profit; Python comprueba que tengan sentido (SL y TP a lados opuestos de la entrada, entrada cerca del precio actual) y ejecuta la fórmula de posición: `Capital × risk_pct / |entrada − SL|`, con `risk_pct` nunca mayor al 1 %
4. Verifica que la ganancia proyectada sea al menos el doble del riesgo (ratio 2:1 configurable) — si no, cancela
5. Da un veredicto final: **APROBADA** o **RECHAZADA**, con todos los detalles de la operación

**Tecnología:** Usa un **pool de servicios LLM** que se van rotando (hoy Groq, Gemini de Google AI Studio y Nemotron 3 Ultra en Ollama Cloud). Cada análisis lo atiende el servicio al que le toca el turno; si falla, se prueba el siguiente en la misma petición. Los servicios y su orden se configuran con `LLM_SERVICES`.

## Páginas

Hash routing: la URL real es `/#/<ruta>`.

**Páginas — Usuario (cualquier usuario autenticado):**
- No tiene página propia. La antigua `/#/agent` (análisis puntual sin bot) redirige al inicio (`/#/dashboard`): el análisis se lanza con **Analizar ahora** en el detalle de cada agente ([M7](M07-BOTS-SIGNALS.md)), que llama a `POST /api/signals/generate` y guarda el resultado como señal. En la UI el LLM se nombra "la IA" ("agente" es el bot).

**Páginas — Administrador (solo admin):**
- No hay página admin específica en este módulo; la gestión de modelos ML se hace vía API

## Entregables

Tablas: `models`, `model_runs` (predictions → Module 7, requiere bot_id)

Entregables:
- ✅ Pool de servicios LLM (Groq, Gemini, Ollama Cloud) con rotación round-robin y failover — reemplaza el multi-provider de `LLM_PROVIDER` (2026-10-19)
- ✅ LLMClientFactory: arma el pool según `LLM_SERVICES` (omite servicios sin API key)
- ✅ Un cliente por servicio con el SDK oficial de cada proveedor: `GroqLLMClient` (`groq`), `GeminiLLMClient` (`google-genai`), `OllamaLLMClient` (`ollama`); con `timeout` y sin reintentos del SDK
- ✅ RotatingLLMClient: turno compartido por proceso + failover al siguiente servicio
- ✅ Prompt Maestro con 4 fases determinísticas + LLM para entry/SL/TP
- ✅ Fórmula de posición en Python: Capital × risk_pct / |entry − SL|
- ✅ Filtro R/R configurable (AGENT_MIN_RR_RATIO, default 2.0)
- ✅ AGENT_MASTER_PROMPT configurable en settings (con default robusto)
- ✅ CRUD modelos ML (tabla `models`): list, get, create, update
- ✅ CRUD model_runs (tabla `model_runs`): list, create, finish
- ✅ `POST /api/agent/analyze` — Prompt Maestro completo
- ✅ Web UI: análisis desde el detalle de cada agente ("Analizar ahora"); la página `/#/agent` se retiró el 2026-10-08
- ✅ Cada análisis registra qué servicio y modelo respondieron y cuánto tardó (`LLMCompletion` → `AnalysisResult.llm_*` → columnas `signals.llm_*`) (2026-10-19)
- ✅ 20 tests unitarios pasando (LLM 100% mockeado, sin llamadas reales)
- ✅ (2026-10-19) **Propiedad de la cuenta** en `POST /api/agent/analyze` (`owner_id`; cuenta ajena → `AGENT_ACCOUNT_NOT_FOUND`)
- ✅ (2026-10-19) **Rate limit por usuario** (`AGENT_ANALYSES_PER_MINUTE`) en `/api/agent/analyze` y `/api/signals/generate`
- ✅ (2026-10-19) **Validación de la salida del LLM**: niveles coherentes (`INCONSISTENT_LEVELS`), entrada cerca del precio (`ENTRY_TOO_FAR`), JSON estricto, `confidence` en [0, 1], precios finitos y > 0
- ✅ (2026-10-19) Parámetros `risk_pct` (acotado al 1 %) y `as_of` (analizar una vela concreta); tamaño de posición y R/R en `Decimal`

## Decisiones de diseño

| Decisión | Motivo | Alternativa descartada |
|---|---|---|
| Prompt Maestro en **4 fases**: régimen → reglas → LLM → R/R; las fases 1, 2 y 4 son **determinísticas** en Python | El LLM no decide si se opera, solo propone niveles; los filtros son reproducibles y auditables | Dejar que el LLM decida todo |
| El LLM solo propone **entry / SL / TP**; el tamaño de posición lo calcula Python: `Capital × risk_pct / \|entry − SL\|` | Los LLM fallan en aritmética; el riesgo (regla del 1 %) no puede depender de ellos | Pedir el tamaño de posición al LLM |
| **Pool de servicios con rotación round-robin + failover** (`RotatingLLMClient`), con Groq, Gemini y Ollama Cloud | Reparte la carga entre capas gratuitas/baratas y sus rate limits; si un servicio cae o devuelve 429 el análisis no falla | Un solo proveedor con `LLM_PROVIDER` (esquema anterior, retirado el 2026-10-19) |
| **SDK oficial por proveedor** (`groq`, `google-genai`, `ollama`), un `LLMClient` por servicio, registrado en el catálogo `LLM_SERVICE_CATALOG` (`client_cls`) | Cada SDK usa la API nativa: Gemini recibe el prompt como `system_instruction`, Ollama separa el razonamiento (`message.thinking`) del JSON; sin depender de capas de compatibilidad con OpenAI | Un único `OpenAICompatibleClient` con `base_url` por servicio (se usó al inicio del pool; retirado el 2026-10-19 junto con el paquete `openai`) |
| Turno de rotación **a nivel de proceso** (contador de módulo con `threading.Lock`) | El cliente se crea por request y lo comparten endpoints sync (threadpool) y scheduler | Turno en la instancia (siempre empezaría por el primero) |
| Pool por defecto `groq,gemini,ollama`; sin Cerebras ni OpenRouter | Cerebras dejó de tener capa gratuita; la de OpenRouter es muy limitada (~50 peticiones/día sin créditos) y `openrouter/free` cambia de modelo en cada llamada | Mantenerlos en el pool |
| `GEMINI_MODEL=gemini-3.5-flash-lite` por defecto | Cuota gratuita suficiente (15 RPM, 250K tokens de entrada/min, 500 peticiones/día) y razona mejor que 3.1 Flash-Lite; con Groq alternando cubre ~1000 análisis/día | `gemini-3.6-flash` (poca cuota gratis), `gemini-3-flash-preview` (lo puede retirar Google), Gemma 4 31B (razona peor) |
| Ollama Cloud con `nemotron-3-ultra`, de último en la rotación | Es el modelo gratuito más capaz de su catálogo (47.7 en el índice de Artificial Analysis frente a 36.0 de Nemotron 3 Super y 33.3 de gpt-oss-120b); va de último porque la capa gratuita es la más limitada (1 petición a la vez, cuota mensual por tiempo de GPU) | `nemotron-3-super` (gasta 4–5× menos cuota pero razona peor), `gpt-oss:120b` |
| `LLM_TIMEOUT_SECONDS` por defecto 60 (antes 30) | `nemotron-3-ultra` (550B, razona antes de responder) puede pasar de 30 s; con 30 caducaría siempre y gastaría cuota sin respuesta | Timeout por servicio (más configuración) |
| `LLM_MAX_TOKENS` por defecto 4096 (antes 1024) | En Gemini 3 los tokens de razonamiento cuentan contra `max_tokens`; con 1024 el JSON puede llegar vacío o cortado | Desactivar el razonamiento por servicio (requiere parámetros propios de Gemini) |
| `max_retries=0` en el SDK + `LLM_TIMEOUT_SECONDS` (30 s) | El failover sustituye a los reintentos: ante un 429 se pasa al siguiente servicio en vez de esperar | Reintentos del SDK con backoff |
| `complete()` devuelve un `LLMCompletion` (texto + `provider`, `model`, `latency_ms`, `failed_providers`), no un `str` | El servicio/modelo que respondió solo lo conoce el pool; así llega al `AnalysisResult` sin estado compartido en el cliente | Atributo `last_call` en el cliente (estado mutable) o medir solo en `AnalyzeService` (no sabría quién respondió) |
| La latencia guardada es la de la **consulta completa** (incluye los servicios que fallaron antes); los que fallaron van en `failed_providers` | Es lo que esperó el usuario; con `failed_providers` se distingue un servicio lento de un failover | Solo la latencia del servicio que respondió |
| `LLMClientFactory.create(settings)` se llama **por request** | Respeta cambios de configuración en caliente (el turno de rotación no se pierde: vive en el módulo) | Cliente singleton al arrancar |
| Ratio R/R mínimo configurable (`AGENT_MIN_RR_RATIO`, 2.0 por defecto) | Cada despliegue ajusta su umbral sin tocar código | Constante en el código |
| `risk_pct` del análisis = el del **agente** si se pasa ([M7](M07-BOTS-SIGNALS.md) pasa `effective_risk_pct`), si no el de la estrategia; siempre acotado a (0, 1 %] (`_effective_risk_pct`; inválido, NaN o ≤ 0 → 1 %) | Regla del 1 % aplicada en el servidor aunque la estrategia o el agente digan otra cosa | Usar siempre el de la estrategia (antes) |
| **Coherencia de niveles** tras el LLM: compra → SL < entrada < TP; venta → TP < entrada < SL; si no, `REJECTED` con `INCONSISTENT_LEVELS` | El filtro R/R usa distancias: un TP del lado equivocado lo pasaba | Confiar en el LLM |
| **Entrada cerca del precio:** distancia entre entrada y último cierre ≤ `AGENT_MAX_ENTRY_ATR_DISTANCE` × ATR(14) (1,0 por defecto), o 2 % del precio si el conjunto no calcula ATR; si no, `REJECTED` con `ENTRY_TOO_FAR` | Evita precios inventados por el LLM | Sin límite |
| Estos rechazos son resultados de negocio (200 + `REJECTED`), no errores HTTP | Igual que régimen, reglas y R/R; la señal queda guardada | 4xx |
| **JSON estricto:** `json.loads(parse_constant=...)` rechaza `NaN`/`Infinity`; la respuesta debe ser un objeto; precios finitos y > 0 (`_positive_price`); `confidence` fuera de [0, 1] → `null`; `reasoning` ≤ 1000 caracteres | Un `NaN` o un texto donde va un número no debe llegar al cálculo de la posición | Aceptar lo que devuelva `json.loads` |
| Tamaño de posición y R/R calculados con `Decimal` (se devuelven como `float`) | Sin errores de coma flotante en la fórmula del riesgo | `float` en todo el cálculo |
| Cuenta ajena → `AGENT_ACCOUNT_NOT_FOUND` (404), igual que una inexistente | No revela saldos ni qué cuentas existen | 403 |
| Rate limit **por usuario** (`user:<id>`, en memoria) en las dos rutas que llaman al LLM | Cada análisis es una llamada de pago; el scheduler no pasa por las rutas y tiene su propio tope diario ([M7](M07-BOTS-SIGNALS.md)) | Por IP (se comparte detrás de un NAT) |
| Parámetro `as_of`: analiza la vela (y sus features) con `ts ≤ as_of` | El scheduler decide con la última vela **cerrada**, no con la que está en formación | Analizar siempre la última |
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
| Madurez | **≈ 81 %** | Funcionalidad 85 · Tests 70 · Seguridad 90 · Operación 80 |

- **Funcionalidad (85):** `models` / `model_runs` son un registro (CRUD); **no hay entrenamiento ni inferencia ML** y `predictions` no se usa.
- **Tests (70):** 20 tests de `AnalyzeService` con LLM mockeado; sin tests de las validaciones nuevas (`INCONSISTENT_LEVELS`, `ENTRY_TOO_FAR`, JSON estricto, propiedad, tope de `risk_pct`) ni de `LLMClientFactory`, `RotatingLLMClient`, clientes o REST.
- **Seguridad (90):** las API keys (`GROQ_API_KEY`, `GEMINI_API_KEY`, `OLLAMA_API_KEY`) solo por entorno; `POST /api/agent/analyze` comprueba que la cuenta sea del usuario (antes exponía el saldo de cuentas ajenas); rate limit por usuario; salida del LLM validada antes de calcular la posición. El rate limit vive en memoria (por proceso).
- **Operación (80):** pool con rotación, *failover* entre servicios y *timeout* por llamada; log de arranque con los servicios activos; umbrales configurables (`AGENT_MAX_ENTRY_ATR_DISTANCE`, `AGENT_ANALYSES_PER_MINUTE`). Sin *circuit breaker* (un servicio caído se sigue probando en su turno) ni métricas por servicio.

## Posibles mejoras

| Prioridad | Mejora | Esfuerzo |
|---|---|---|
| Alta | Tests de las validaciones de la salida del LLM (`INCONSISTENT_LEVELS`, `ENTRY_TOO_FAR`, `NaN`/`Infinity`, `confidence`), de la propiedad de la cuenta y del tope de `risk_pct` | S |
| Alta | Persistir cada análisis (prompt, respuesta, versión del modelo) para auditoría y para medir el edge; la tabla `predictions` existe y no se usa | M |
| Media | *Circuit breaker* en el pool: sacar temporalmente un servicio tras N fallos seguidos (hoy se reintenta en cada turno y suma su *timeout*) | S |
| Media | Métricas por servicio (latencia media, tasa de fallos) a partir de `signals.llm_*` y `reasons.llm.failed_providers` | S |
| Media | Cachear el análisis por `(símbolo, timeframe, vela, estrategia)` para no repetir llamadas dentro de la misma vela (las automáticas ya son una por vela; "Analizar ahora" no) | S |
| Media | Rate limit compartido entre procesos (Redis): hoy cada worker cuenta por separado | S |
| Media | Tests de `LLMClientFactory`, `RotatingLLMClient` (rotación y failover con clientes mock), los tres clientes (SDK mockeado) y rutas REST | M |
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
| `llm_client.py` | `LLMClient` (ABC), `LLMCompletion`, `elapsed_ms` | Interfaz: `complete(system, user) -> LLMCompletion` (`text`, `provider`, `model`, `latency_ms`, `failed_providers`); cada cliente mide su llamada con `time.perf_counter()` |
| `llm_services.py` | `LLMServiceSpec`, `LLM_SERVICE_CATALOG` | Catálogo: nombre, base_url y qué settings dan API key y modelo |
| `groq_client.py` | `GroqLLMClient` | Groq con SDK `groq`: `chat.completions.create`, `max_completion_tokens`, `max_retries=0` |
| `gemini_client.py` | `GeminiLLMClient` | Gemini con SDK `google-genai`: `models.generate_content`, prompt en `system_instruction`, `max_output_tokens`, timeout en ms, `HttpRetryOptions(attempts=1)` |
| `ollama_client.py` | `OllamaLLMClient` | Ollama Cloud con SDK `ollama`: host `https://ollama.com` + `Authorization: Bearer`, `options={temperature, num_predict}`; devuelve `message.content` (el razonamiento va aparte en `message.thinking`) |
| `rotating_client.py` | `RotatingLLMClient` | Pool: round-robin (turno por proceso) + failover; devuelve el `LLMCompletion` del que respondió con `latency_ms` de la consulta completa y `failed_providers`; si fallan todos, `LLMCallError(provider="pool")` |
| `llm_factory.py` | `LLMClientFactory` | `create()` arma el pool según `LLM_SERVICES`; `describe()` lista los servicios activos (log de arranque en `app_factory._lifespan`) |

**Catálogo de servicios:**
- groq → `GroqLLMClient` · `GROQ_API_KEY` · `GROQ_MODEL` (default `moonshotai/kimi-k2-instruct-0905`)
- gemini → `GeminiLLMClient` · `GEMINI_API_KEY` · `GEMINI_MODEL` (default `gemini-3.5-flash-lite`)
- ollama → `OllamaLLMClient` (host `https://ollama.com`) · `OLLAMA_API_KEY` · `OLLAMA_MODEL` (default `nemotron-3-ultra`)

### Servicios (`app/modules/agent/services/`)
| Subdir | Servicios |
|--------|-----------|
| `agent/` | `analyze_service.py` — Prompt Maestro (4 fases) |
| `models/` | `list_models_service.py`, `get_model_service.py`, `create_model_service.py`, `update_model_service.py` |
| `model_runs/` | `list_model_runs_service.py`, `create_model_run_service.py`, `finish_model_run_service.py` |

### Prompt Maestro — 4 fases (`AnalyzeService.analyze`)
1. **Fase 1 — Régimen:** `strategy.parameters.regime_required` vs `features.regime`. Si no coincide → RECHAZADA. `None` = acepta cualquier régimen.
2. **Fase 2 — Reglas:** evalúa cada `{indicator, operator, value}` contra features. Si ALGUNA falla → RECHAZADA.
3. **Fase 3 — LLM:** genera entry/SL/TP. Python valida que sean números finitos y > 0 (`AGENT_LLM_MISSING_PRICES` 502 si no), que sean coherentes (`INCONSISTENT_LEVELS`) y que la entrada esté a ≤ `AGENT_MAX_ENTRY_ATR_DISTANCE` × ATR(14) del último cierre, o a ≤ 2 % sin ATR (`ENTRY_TOO_FAR`); después calcula en `Decimal` `position_size = (capital × risk_pct) / |entry − SL|`, con `risk_pct` acotado al 1 %.
4. **Fase 4 — R/R:** `(TP − entry) / (entry − SL) >= AGENT_MIN_RR_RATIO` (default 2.0). Si no → RECHAZADA.

Firma: `analyze(symbol_id, timeframe_id, strategy_id, account_id, feature_set_id, owner_id=None, risk_pct=None, as_of=None)`. `owner_id` lo pasa la ruta (`write_scope`; la ruta exige super admin); `risk_pct` y `as_of` los pasa [M7](M07-BOTS-SIGNALS.md).

Los resultados posteriores a la fase 3 (`LLM_REJECTED`, `INCONSISTENT_LEVELS`, `ENTRY_TOO_FAR`, `RR_RATIO_TOO_LOW`, `APPROVED`) llevan `llm_provider`, `llm_model`, `llm_latency_ms` y `llm_failed_providers`; `to_dict()` los expone en `"llm"` (`null` si no se llamó al LLM). Los errores `AGENT_LLM_PARSE_ERROR` y `AGENT_LLM_MISSING_PRICES` los incluyen en `meta`.

### Provider (`app/modules/agent/providers/agent_provider.py`)
- `AgentServiceFactory` — instancia repos propios + borrowed de strategies, accounts, features, market
- `LLMClientFactory.create(settings)` se llama por request (respeta cambios de config en runtime)

### Endpoints REST
| Método | Ruta | Auth | Nota |
|--------|------|------|------|
| POST | `/api/agent/analyze` | token (la cuenta debe ser del usuario; admin: cualquiera) | Prompt Maestro — retorna 200 siempre (APPROVED o REJECTED); rate limit `AGENT_ANALYSES_PER_MINUTE` por usuario (429) |
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

### Frontend
- Se eliminó `frontend/src/modules/agent` (página `analyze.tsx`, `analysis-result-panel.tsx`, api y labels). `routes/_app/agent.tsx` solo redirige a `/dashboard`.
- El análisis se usa desde `bots/components/analyze-now-button.tsx` ([M7](M07-BOTS-SIGNALS.md)); el resultado se ve en `signal-detail-sheet.tsx`.
- `POST /api/agent/analyze` sigue disponible en la API (sin UI).
- `models` / `model_runs` siguen sin UI.

### Settings LLM/Agent (en `app/common/config/settings.py`)
```python
LLM_SERVICES        # orden de rotación, CSV (default: "groq,gemini,ollama")
GROQ_API_KEY        # sin key → groq se omite del pool
GROQ_MODEL          # default: moonshotai/kimi-k2-instruct-0905
GEMINI_API_KEY      # Google AI Studio; sin key → gemini se omite del pool
GEMINI_MODEL        # default: gemini-3.5-flash-lite
OLLAMA_API_KEY      # Ollama Cloud; sin key → ollama se omite del pool
OLLAMA_MODEL        # default: nemotron-3-ultra
LLM_TIMEOUT_SECONDS # timeout por llamada antes del failover (default: 60)
LLM_TEMPERATURE     # compartido por todos los servicios (default: 0.1)
LLM_MAX_TOKENS      # compartido por todos los servicios (default: 4096)
AGENT_MIN_RR_RATIO  # ratio R/R mínimo (default: 2.0)
AGENT_MASTER_PROMPT # prompt del sistema configurable (env var)
AGENT_MAX_ENTRY_ATR_DISTANCE # N × ATR(14) máximo entre entrada y último cierre (default: 1.0)
AGENT_ANALYSES_PER_MINUTE    # análisis por usuario y minuto en /agent/analyze y /signals/generate (default: 6)
```

## Gotchas críticos

- **Pool vacío:** si ningún servicio de `LLM_SERVICES` tiene API key, la app arranca igual (warning `[llm] ningún servicio LLM configurado`) y cada análisis devuelve `AGENT_LLM_CALL_FAILED` (502). Ya no existen `LLM_PROVIDER` / `LLM_MODEL` / `LLM_API_KEY` / `LLM_BASE_URL` ni los clientes de Anthropic/Ollama.
- **Turno por proceso:** con varios workers de uvicorn cada uno lleva su propio turno; la rotación es aproximada, no estricta entre workers.
- **Failover suma latencia:** si el servicio del turno se cuelga, el análisis espera hasta `LLM_TIMEOUT_SECONDS` (60 s) antes de probar el siguiente.
- **El failover solo cubre errores de llamada** (red, 429, 5xx, timeout). Un JSON inválido sigue siendo `AGENT_LLM_PARSE_ERROR` y no pasa al siguiente servicio.
- **Gemini y `LLM_MAX_TOKENS`:** Gemini 3.x razona antes de responder y esos tokens cuentan contra `max_tokens`. Síntoma: `AGENT_LLM_PARSE_ERROR` con respuesta vacía o JSON cortado solo cuando responde gemini → causa: `LLM_MAX_TOKENS` bajo (p. ej. 1024 de un `.env` antiguo) → solución: 4096 o más.
- **Modelo de Gemini retirado o renombrado:** el síntoma es un 404 de gemini en el log y el failover pasando a groq → ajustar `GEMINI_MODEL`.
- **Capa gratuita de Gemini:** 500 peticiones/día y 15 RPM con `gemini-3.5-flash-lite`; al agotarse responde 429 y el failover pasa a Groq. Además, Google puede usar el contenido enviado para mejorar sus productos (el capital y el contexto de mercado salen del sistema); en la capa de pago no.
- **Ollama Cloud free:** una sola petición a la vez y una cuota mensual medida por tiempo de GPU; `nemotron-3-ultra` es de los modelos que más la gastan. Si dos análisis coinciden o se agota la cuota, Ollama responde con error y el failover pasa a Groq. Si la cuota se acaba muy rápido, cambiar a `OLLAMA_MODEL=nemotron-3-super`.
- **Nombre del modelo en Ollama Cloud:** por API directa se usa el nombre de `https://ollama.com/api/tags` (`nemotron-3-ultra`), **sin** el sufijo `:cloud` de la app/CLI local; con `:cloud` da 404.
- `POST /api/agent/analyze` responde 200 también cuando la operación es **RECHAZADA**: mirar el veredicto en `data`, no el código HTTP.
- **Solo los indicadores del conjunto:** el prompt y `features_snapshot` incluyen solo las claves presentes en las features (las del conjunto del bot, ver [M3](M03-FEATURE-ENGINEERING.md)). Si a una regla de la estrategia le falta su indicador, el análisis falla con `AGENT_FEATURE_SET_INCOMPATIBLE` (422) en vez de rechazar la regla en silencio.
- ~~**Hueco de seguridad:** `POST /api/agent/analyze` no comprobaba la propiedad de `account_id`~~ — resuelto el 2026-10-19 (`owner_id` → `AGENT_ACCOUNT_NOT_FOUND`).
- **El prompt dice el riesgo real:** la línea `Risk/Trade` del mensaje al LLM usa el `risk_pct` efectivo (acotado), no el de la estrategia.
- **`ENTRY_TOO_FAR` en mercados muy tranquilos:** con un ATR pequeño y `AGENT_MAX_ENTRY_ATR_DISTANCE=1.0`, una entrada razonable pero algo alejada se rechaza; subir el multiplicador si pasa seguido.
- **Llamada desde M7:** `GenerateSignalService` llama a `analyze` con `risk_pct` y `as_of`; los mocks deben esperarlos (ver `tests/bots/test_generate_signal_service.py`).
- `regime_required = None` acepta cualquier régimen (fase 1 no filtra).
- **Mocks de `LLMClient`:** `complete()` devuelve un `LLMCompletion`, no un `str`. Un mock con `return_value = '{...}'` rompe con `AttributeError: 'str' object has no attribute 'text'` (ver `make_service` en `tests/agent/test_analyze_service.py`).
- El `AnalyzeService` lo reutiliza [M7](M07-BOTS-SIGNALS.md) a través de `BotServiceFactory._build_analyze_service()`; un cambio de firma aquí rompe la generación de señales.

## Tests

- `tests/agent/test_analyze_service.py` — 20 tests unitarios, LLM 100% mockeado
  - `TestAnalyzeDataLoading` (6), `TestRegimeFilter` (3), `TestRulesValidation` (3)
  - `TestLLMIntegration` (4), `TestRRFilter` (2), `TestPositionSizing` (1), `TestFullApprovedPath` (1)
- **Huecos:** `LLMClientFactory`, `RotatingLLMClient`, `GroqLLMClient`, `GeminiLLMClient`, `OllamaLLMClient`, servicios de `models` / `model_runs` y rutas REST.

## Riesgos

- **Coste y latencia:** cada análisis es una llamada a un LLM externo; los *rate limits* de las capas gratuitas de Groq, Gemini y Ollama Cloud son el motivo del pool.
- **Salida no determinista:** el LLM propone niveles de precio; la coherencia de niveles, la distancia máxima al precio, el filtro R/R y la fórmula de posición acotan el riesgo, pero dentro de esos márgenes el LLM sigue eligiendo dónde poner el SL y el TP.
- **Privacidad:** el contexto de mercado y el capital se envían a los servicios externos del pool.

## Historial

- **2026-03** — Módulo completado por un compañero: multi-provider, Prompt Maestro 4 fases, CRUD `models` / `model_runs`, UI `/agent`, 20 tests.
- **Posterior** — Panel de error y mejor manejo de errores en la página de análisis (commit `d8b2e43`).
- **2026-10-08** — API headless (/api), páginas migradas a React (frontend/).
- **2026-10-08** — El prompt usa solo los indicadores del conjunto; nuevo error `AGENT_FEATURE_SET_INCOMPATIBLE`. Se retira la página `/#/agent`: el análisis vive en cada agente ("Analizar ahora").
- **2026-10-19** — Pool de servicios LLM con rotación round-robin y failover (Groq + Gemini + Ollama Cloud) reemplaza el multi-provider de `LLM_PROVIDER`; se retira `AnthropicLLMClient`; un cliente por proveedor con su SDK oficial (`groq`, `google-genai`, `ollama`; se retira `openai`), `LLM_TIMEOUT_SECONDS` (60 s), sin reintentos del SDK y `LLM_MAX_TOKENS` 4096. Cerebras (sin capa gratuita) y OpenRouter (capa gratuita muy limitada) se probaron y se quitaron el mismo día.
- **2026-10-19** — `complete()` devuelve `LLMCompletion` (servicio, modelo, latencia, servicios fallidos); el `AnalysisResult` y la señal de [M7](M07-BOTS-SIGNALS.md) los guardan.
- **2026-10-19** — Auditoría de seguridad: propiedad de la cuenta en `/agent/analyze` (antes exponía saldos ajenos), rate limit por usuario (`AGENT_ANALYSES_PER_MINUTE`) en `/agent/analyze` y `/signals/generate`, `risk_pct` acotado al 1 %, rechazos `INCONSISTENT_LEVELS` y `ENTRY_TOO_FAR` (`AGENT_MAX_ENTRY_ATR_DISTANCE`), JSON estricto, `confidence` en [0, 1], posición y R/R en `Decimal`, parámetro `as_of` para las señales automáticas.
