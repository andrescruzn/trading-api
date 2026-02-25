# Trading AI API — Memory

## Cómo iniciar una nueva sesión
Solo di: **"comenzamos Módulo X"** o **"continuamos donde quedamos"**.
MEMORY.md se carga automáticamente en cada sesión — ya tengo el contexto.
Si quieres compartir algo nuevo dilo directamente (ej: "instalé ccxt para exchanges").

## Comandos
- Correr servidor: `source .venv/bin/activate && uvicorn app.main:app --reload`
- Correr tests: `source .venv/bin/activate && python -m pytest tests/<archivo_específico> -v`
- Ejecutar SQL en BD: `/Applications/MAMP/Library/bin/mysql80/bin/mysql -u root -proot trading_ai < archivo.sql`
- Shell MySQL: `/Applications/MAMP/Library/bin/mysql80/bin/mysql -u root -proot trading_ai`
- NUNCA correr pytest tests/ completo salvo que el usuario lo pida explícitamente
- ⚠️ TESTS GASTAN TOKENS: crear tests solo cuando el usuario lo pida explícitamente. No crearlos por defecto al terminar un módulo.

## Estado del proyecto (Feb 2026)
- ✅ M1 Auth completo: login password, login OTP, verify OTP, logout, rotate token, get_me, change_password
- ✅ M2 Market Data completo (pendiente confirmar admin pages tras re-login)
- Web pages: /login, /dashboard (con panel admin), /profile, /market/symbols, /market/candles
- Admin pages: /admin/exchanges, /admin/symbols, /admin/timeframes, /admin/candles/ingest
- Security headers middleware — NUNCA usar onclick/onchange inline en HTML
- Todos los handlers de eventos van en JS vía addEventListener
- 87 tests pasando (42 auth + 45 audit)

## Bugs corregidos en M2 (importantes para no repetir)
- CSP no incluía /market/ ni /admin/ → bloqueaba CSS y JS → agregar prefijos a `_is_web_route()` en security_headers.py
- JWT no incluía role_id → admin pages redirigían al dashboard → los 3 servicios de login deben hacer `subject={"user_id": user.id, "role_id": user.role_id}`
- Botón "Nuevo" encimaba texto en móvil → usar clase `.page-header` (align-items: flex-start) en vez de `.flex.items-center`

## M2 — Nuevas funcionalidades
- `POST /candles/fetch` — descarga velas de exchange real via ccxt (Binance, Bybit, Kraken, Coinbase, Bitget, OKX)
- ccxt instalado en .venv, versión 4.5.40
- Paginación cliente-side (20 items/página) en todas las tablas: exchanges, symbols, timeframes, market/symbols
- CSS: `.page-header`, `.pagination`, `.pagination__info`, `.pagination__btns` en app.css

## Auditoría HTTP (app/common/audit/)
- Todo request HTTP queda auditado automáticamente via AuditMiddleware (BaseHTTPMiddleware)
- Tablas dinámicas por año: `http_audit_2026`, `http_audit_2027`... se crean solas en el primer request del año
- NON-BLOCKING: insert en hilo daemon — no afecta latencia del usuario
- Campos redactados: password, otp_code, token, access_token → "***REDACTED***" (clave se preserva)
- Rutas excluidas: /health, /static/, /favicon
- Usar `sqlalchemy.dialects.mysql.TIMESTAMP(fsp=6)` para columnas TIMESTAMP(6) en SQLAlchemy Core (NO el genérico TIMESTAMP(6) — no genera la precisión correcta en DDL MySQL)

## Convenciones clave
- `utc_now()` de `app.common.utils` — no usar `datetime.now(timezone.utc)` directo
- Jinja2 templates: `TemplateResponse(request, "template.html", {context})` (nuevo formato Starlette)
- Los skills están en `.claude/skills/` — leer antes de codear (ver main_instructions.md)
- CSP bloquea onclick inline → siempre usar addEventListener en archivos .js servidos desde /static/

## Roles en BD
- role_id=1 → Usuario (user)
- role_id=2 → Administrador (admin)

## Hoja de ruta y mapa de módulos
- Ver `memory/roadmap.md` — detalle de los 9 módulos con tablas, entregables y dependencias
- Ver `memory/modules_map.md` — mapa detallado de tablas, archivos, endpoints y páginas por módulo ← LEER ANTES DE CODEAR
- Comprar/Vender está en el **Módulo 8 — Orders & Execution**
- ✅ M1 completo (Auth + HTTP Audit) → ✅ M2 Market Data → 📌 M3 Feature Engineering es el siguiente

## LLM / Agente IA — Ollama (USAR EN TODOS LOS MÓDULOS)
- **Motor:** Ollama local — NO API externa
- **Endpoint:** `http://localhost:11434` (HTTP REST)
- **Modelo activo:** `gemma3:4b`
- **Scope:** solo local/PC — producción/nube se decide en el futuro
- **Cuándo usarlo:** en cualquier módulo que requiera análisis, generación de código dinámico, clasificación o decisiones (señales, features, posición, régimen de mercado, etc.)
- El LLM genera código Python para cálculos (evitar alucinaciones matemáticas directas)
- Integrar via HTTP REST: `POST http://localhost:11434/api/generate` con `{"model": "gemma3:4b", "prompt": "..."}`

## Concepto del proyecto
Agente de Trading con IA que elimina el sesgo emocional. Toma decisiones basadas en:
1. Filtro de Régimen: tendencia (HH/HL) vs rango lateral
2. Validación de reglas de la estrategia
3. Matemática de posición: Capital × %Riesgo / (Entrada − StopLoss)
4. Ratio Riesgo/Beneficio mínimo 2:1
Regla del 1%: nunca arriesgar más del 1% del capital por operación.
Los LLM (via Ollama local) generan código Python para los cálculos (evitar alucinaciones matemáticas).
