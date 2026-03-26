# Trading AI API — Memory

## Cómo iniciar una nueva sesión
Solo di: **"comenzamos Módulo X"** o **"continuamos donde quedamos"**.
MEMORY.md se carga automáticamente en cada sesión — ya tengo el contexto.
Si quieres compartir algo nuevo dilo directamente (ej: "instalé ccxt para exchanges").

## ⚠️ OBLIGATORIO AL INICIAR CUALQUIER SESIÓN
**Leer primero:** `/Users/codelabs/Sites/andrescruzn/www/trading-api/MODULES.md`
Este archivo es la fuente de verdad del proyecto — describe en lenguaje simple qué hace cada módulo, qué páginas tiene (usuario vs admin) y cuál es el estado actual (✅ completo / 📌 pendiente). Sin leerlo no se debe codear nada.

## Comandos
- Correr servidor: `source .venv/bin/activate && uvicorn app.main:app --reload`
- Correr tests: `source .venv/bin/activate && python -m pytest tests/<archivo_específico> -v`
- Ejecutar SQL en BD: `/Applications/MAMP/Library/bin/mysql80/bin/mysql -u root -proot trading_ai < archivo.sql`
- Shell MySQL: `/Applications/MAMP/Library/bin/mysql80/bin/mysql -u root -proot trading_ai`
- NUNCA correr pytest tests/ completo salvo que el usuario lo pida explícitamente
- ⚠️ TESTS GASTAN TOKENS: crear tests solo cuando el usuario lo pida explícitamente. No crearlos por defecto al terminar un módulo.

## Estado del proyecto (Mar 2026)
- ✅ M1 Auth completo: login password, login OTP, verify OTP, logout, rotate token, get_me, change_password
- ✅ M2 Market Data completo
- ✅ M3 Feature Engineering completo: feature sets CRUD + cálculo RSI/EMA/MACD/ATR/BB/vol_rel/regime
- ✅ M4 Accounts & Portfolio completo: CRUD cuentas, balances, cifrado Fernet, 36 tests pasando
- ✅ M5 Strategies completo: CRUD strategies + datasets, validación coherencia tipo↔régimen, UI usuario+admin
- ✅ M6 AI Agent / Models completo: multi-provider LLM, Prompt Maestro 4 fases, CRUD models+model_runs, 20 tests
- ✅ M7 Bots & Signals completo: CRUD bots + state machine, generate_signal con M6, 55 tests
- ✅ M8 Orders & Execution completo: PaperExecutor + LiveExecutor (ccxt), order+fill+position atómico
- ✅ M9 Alerts completo: 4 canales (email/telegram/webhook/desktop), hooks fire-and-forget en M7/M8
- ✅ M10 Billing & Managed Accounts completo: inversores, cuentas administradas, HWM, performance fee
- Web pages: /login, /dashboard, /profile, /market/symbols, /market/candles, /features, /portfolio, /strategies, /agent, /bots, /orders, /alerts
- Admin pages: /admin/exchanges, /admin/symbols, /admin/timeframes, /admin/candles/ingest, /admin/feature-sets, /admin/accounts, /admin/strategies, /admin/bots, /admin/orders, /admin/alerts, /admin/telegram, /admin/investors, /admin/managed-accounts, /admin/billing
- Investor pages: /investor/dashboard
- Security headers middleware — NUNCA usar onclick/onchange inline en HTML
- Todos los handlers de eventos van en JS vía addEventListener
- 107+ tests pasando (42 auth + 45 audit + 36 accounts + 20 agent + 55 bots + otros)
- pandas-ta 0.4.71b0 instalado en .venv (TA library M3)

## Bugs corregidos en M2 (importantes para no repetir)
- CSP no incluía /market/ ni /admin/ → bloqueaba CSS y JS → agregar prefijos a `_is_web_route()` en security_headers.py
- JWT no incluía role_id → admin pages redirigían al dashboard → los 3 servicios de login deben hacer `subject={"user_id": user.id, "role_id": user.role_id}`
- Botón "Nuevo" encimaba texto en móvil → usar clase `.page-header` (align-items: flex-start) en vez de `.flex.items-center`

## Bugs corregidos en M3 (importantes para no repetir)
- pandas-ta genera `ATRr_14` (con 'r' minúscula), NO `ATR_14` — verificar siempre nombres de columnas con `df.columns` antes de usarlos en `dropna(subset=...)`
- pandas-ta genera `BBU_20_2.0_2.0` / `BBL_20_2.0_2.0` / `BBM_20_2.0_2.0` (doble `_2.0`), NO `BBU_20_2.0`
- Siempre verificar nombres exactos de columnas pandas-ta corriendo: `df.ta.<indicador>(append=True); print(df.columns)`
- Dropdowns de símbolos mostraban duplicados (BTC/USDT x2) → se agregó `exchange_name` a la entidad `Symbol` via JOIN en `list_all()` → ahora muestra `BTC/USDT (Binance)` y `BTC/USDT (Bybit)`

## M3 — Columnas exactas de pandas-ta (versión 0.4.71b0)
| Indicador | Columna generada |
|---|---|
| RSI(14) | `RSI_14` |
| EMA(20) | `EMA_20` |
| EMA(50) | `EMA_50` |
| EMA(200) | `EMA_200` |
| MACD line | `MACD_12_26_9` |
| MACD signal | `MACDs_12_26_9` |
| MACD hist | `MACDh_12_26_9` |
| ATR(14) | `ATRr_14` ← OJO: tiene 'r' minúscula |
| BB Upper | `BBU_20_2.0_2.0` ← OJO: doble `_2.0` |
| BB Mid | `BBM_20_2.0_2.0` |
| BB Lower | `BBL_20_2.0_2.0` |

## M6 — AI Agent / Models (completado por compañero)
- **LLM multi-provider:** openai, anthropic, xai (Grok), deepseek, gemini, ollama
- **LLMClientFactory:** crea el cliente según `LLM_PROVIDER` en settings
- **OpenAICompatibleClient:** cubre openai, xai, deepseek, gemini, ollama (un solo cliente)
- **AnthropicLLMClient:** cliente dedicado para Claude
- **Prompt Maestro 4 fases:** régimen → reglas → LLM entry/SL/TP → R/R ≥ 2.0
- **Fórmula de posición:** `position_size = (capital × risk_pct) / |entry − SL|`
- ORM: `MLModelORM` (tabla `models`), `ModelRunORM` (tabla `model_runs`)
- Template: `templates/agent/analyze.html` | JS: `static/js/agent/analyze.js`
- Settings LLM: `LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_TEMPERATURE`, `LLM_MAX_TOKENS`
- Settings agente: `AGENT_MIN_RR_RATIO` (default 2.0), `AGENT_MASTER_PROMPT`
- Endpoints: `POST /agent/analyze`, `GET/POST /api/models`, `GET/PUT /api/models/{id}`, `GET/POST /api/model-runs`, `POST /api/model-runs/{id}/finish`
- Routers en app_factory: `agent_router`, `models_router`, `model_runs_router`
- CSP: `/agent` ya está en `web_prefixes` de security_headers.py

## M2 — Nuevas funcionalidades
- `POST /candles/fetch` — descarga velas de exchange real via ccxt (Binance, Bybit, Kraken, Coinbase, Bitget, OKX)
- ccxt instalado en .venv, versión 4.4.96
- Paginación cliente-side (20 items/página) en todas las tablas: exchanges, symbols, timeframes, market/symbols
- CSS: `.page-header`, `.pagination`, `.pagination__info`, `.pagination__btns` en app.css

## Auditoría HTTP (app/common/audit/)
- Todo request HTTP queda auditado automáticamente via AuditMiddleware (BaseHTTPMiddleware)
- Tablas dinámicas por año: `http_audit_2026`, `http_audit_2027`... se crean solas en el primer request del año
- NON-BLOCKING: insert en hilo daemon — no afecta latencia del usuario
- Campos redactados: password, otp_code, token, access_token → "***REDACTED***" (clave se preserva)
- Rutas excluidas: /health, /static/, /favicon
- Usar `sqlalchemy.dialects.mysql.TIMESTAMP(fsp=6)` para columnas TIMESTAMP(6) en SQLAlchemy Core

## Dashboard — Stats + Chart (implementado Mar 2026)
- 4 tarjetas: BTC/USDT (gold), ETH/USDT (cyan), Mis cuentas (violeta), Estrategias (verde)
- Gráfica de línea BTC/USDT últimas 48 velas 1h — dibujada con Canvas API (sin CDN)
- Datos reales desde: `/api/strategies`, `/accounts`, `/symbols`, `/timeframes`, `/candles`, `/candle-features`

## Bug crítico de CSS cache (solucionado)
- `app.css` no tenía cache-busting → browser servía versión vieja tras cambios
- Solución: `<link rel="stylesheet" href="/static/css/app.css?v={{ sv }}">` en `base.html`
- Ahora TANTO el CSS como el JS se versionan en cada reinicio del servidor
- `sv` viene de `templates.env.globals["sv"] = str(int(time.time()))` en `web/routes.py`

## Bugs corregidos en M5 (importantes para no repetir)
- Route conflict: API router registrado antes que web router → GET `/strategies` devolvía JSON en vez de HTML → solución: prefijo API siempre como `/api/<recurso>`
- `build_list_response` retorna `{"data": [...array...]}` (NO `{"data": {"items": [...]}}`). Siempre usar: `Array.isArray(json.data) ? json.data : (json.data?.items || [])`
- `errorCode` en respuesta exitosa es 200/201, NUNCA 0 → usar `if (json.errorCode >= 400)` para detectar errores

## Convenciones clave
- `utc_now()` de `app.common.utils` — no usar `datetime.now(timezone.utc)` directo
- Jinja2 templates: `TemplateResponse(request, "template.html", {context})` (nuevo formato Starlette)
- Los skills están en `.claude/skills/` — leer antes de codear (ver main_instructions.md)
- CSP bloquea onclick inline → siempre usar addEventListener en archivos .js servidos desde /static/
- NUNCA usar `curl` para hacer login durante debugging — cambia `token_current_jti` e invalida la sesión activa del browser
- Cache-busting: sin `?v={{ sv }}` el browser sirve el JS viejo → agregar a TODOS los `<script>` nuevos

## Documentación del proyecto
- `MANUAL.md` (raíz) — explicación conceptual en lenguaje simple. Actualizar cuando se agreguen conceptos nuevos.
- `MODULES.md` (raíz) — estado de cada módulo (✅/📌) + páginas usuario vs admin. ← LEER AL INICIAR
- `README.md` (raíz) — setup técnico del proyecto

## ⚠️ OBLIGATORIO AL TERMINAR CUALQUIER MÓDULO
Al completar un módulo (o cualquier feature significativa) SIEMPRE actualizar AMBOS archivos:
1. **`MODULES.md`** — cambiar 📌 PENDIENTE → ✅ COMPLETO, agregar páginas y descripción
2. **`MANUAL.md`** — agregar sección explicativa en lenguaje simple del nuevo concepto/módulo

## Roles en BD
- role_id=1 → Usuario (user)
- role_id=2 → Administrador (admin)
- role_id=3 → Inversor (investor) — solo ve /investor/dashboard; settings.AUTH_INVESTOR_ROLE_ID = 3

## Hoja de ruta y mapa de módulos
- `MODULES.md` (raíz del proyecto) ← LEER AL INICIAR SESIÓN
- Ver `.claude/memory/roadmap.md` — detalle técnico de los 10 módulos
- Ver `.claude/memory/modules_map.md` — mapa detallado de tablas, archivos, endpoints y páginas por módulo ← LEER ANTES DE CODEAR
- Comprar/Vender está en el **Módulo 8 — Orders & Execution**
- ✅ M1 → ✅ M2 → ✅ M3 → ✅ M4 → ✅ M5 → ✅ M6 → ✅ M7 → ✅ M8 → ✅ M9 → ✅ M10 — todos completos

## Concepto del proyecto
Agente de Trading con IA que elimina el sesgo emocional. Toma decisiones basadas en:
1. Filtro de Régimen: tendencia (HH/HL) vs rango lateral
2. Validación de reglas de la estrategia
3. Matemática de posición: Capital × %Riesgo / (Entrada − StopLoss)
4. Ratio Riesgo/Beneficio mínimo 2:1
Regla del 1%: nunca arriesgar más del 1% del capital por operación.
LLM multi-provider (openai/anthropic/xai/deepseek/gemini/ollama) genera entry/SL/TP.

# currentDate
Today's date is 2026-03-24.
