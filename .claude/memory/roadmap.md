# Hoja de Ruta — Trading AI API

## Cómo usar este archivo
- Al iniciar cada sesión: leer este archivo para saber en qué módulo estamos.
- Al terminar cada módulo: marcar como ✅ COMPLETO y anotar lo que quedó hecho.
- Referencia de tablas: ver `.claude/db_schema.sql`

---

## ✅ Módulo 1 — Auth & Web UI (COMPLETO)
**Qué hace:** Autenticación, sesiones, roles, interfaz web.

Entregables:
- Login por password y por OTP (email)
- Dashboard con info del usuario y rol
- Cambiar contraseña (revoca sesión)
- Logout con cookie HTTP-only
- GET /users/me (perfil del usuario autenticado)
- Security headers middleware (CSP, X-Frame-Options, etc.)
- 42 tests unitarios pasando

Tablas usadas: `users`, `roles`

---

## ✅ Módulo 2 — Market Data (COMPLETO)
**Qué hace:** Conectar exchanges, registrar símbolos/timeframes, almacenar velas OHLCV.
**Sin este módulo no hay datos para analizar.**

Tablas: `exchanges`, `symbols`, `timeframes`, `candles`

Entregables:
- CRUD exchanges (Binance, Bybit, Kraken, etc.)
- CRUD symbols (BTC/USDT, ETH/USDT, etc.) asociados a un exchange
- CRUD timeframes (1m, 5m, 15m, 1h, 4h, 1d)
- Ingestión de velas OHLCV: manual (endpoint) y/o automática (scheduler)
- Endpoint: GET /candles?symbol=BTC/USDT&timeframe=1h&from=...&to=...
- Web UI: lista de símbolos, últimas velas en tabla
- Tests unitarios de los services

---

## ✅ Módulo 3 — Feature Engineering (COMPLETO)
**Qué hace:** Calcular indicadores técnicos sobre las velas para alimentar el agente.

Tablas: `candle_features`, `feature_sets`

Entregables:
- ✅ CRUD feature sets (nombre, versión, spec JSON)
- ✅ Cálculo de: RSI(14), ATR(14), EMA(20/50/200), MACD(12,26,9), Bollinger Bands(20,2), volumen relativo
- ✅ Detección de régimen de mercado: trend_up / trend_down / sideways (HH/HL swing analysis)
- ✅ POST /candle-features/calculate (admin) — bulk upsert
- ✅ GET /candle-features — consulta con filtros
- ✅ Web UI: /features (viewer) + /admin/feature-sets (gestión + calcular)
- ✅ TA library: pandas-ta 0.4.71b0
- ✅ Test unitarios (18 tests)

---

## ✅ Módulo 4 — Accounts & Portfolio (COMPLETO)
**Qué hace:** Gestionar cuentas de exchange y capital disponible del trader.

Tablas: `accounts`, `account_balances` (`portfolio_snapshots` → Módulo 7, requiere bot_id)

Entregables:
- ✅ CRUD cuentas (exchange + API key/secret cifrada con Fernet → `meta['enc_creds']`)
- ✅ Registro de balances por moneda (USDT, BTC, etc.) — snapshots inmutables
- ✅ Equity curve vía time series de `account_balances`
- ✅ Endpoints: GET/POST `/accounts`, GET/PUT `/accounts/{id}`, GET/POST `/accounts/{id}/balances`
- ✅ Cifrado simétrico: `CredentialsCipher` (Fernet, `CREDENTIALS_SECRET_KEY`)
- ✅ Web UI: `/accounts` (panel usuario) + `/admin/accounts` (vista admin)
- ✅ 36 tests unitarios pasando (list/get/create/update accounts + list/record balances)
- Test unitarios

---

## ✅ Módulo 5 — Strategies (COMPLETO)
**Qué hace:** Definir las reglas de entrada/salida del agente.

Tablas: `strategies`, `datasets`

Entregables:
- ✅ CRUD estrategias con config JSON (reglas, régimen requerido, timeframe, risk_pct)
- ✅ Tipos soportados: trend_following, mean_reversion
- ✅ Validación coherencia tipo/régimen (hint en vivo en UI + validación backend)
- ✅ Web UI: /strategies (viewer) + /admin/strategies (CRUD admin)
- ✅ API: GET/POST `/api/strategies`, GET/PUT `/api/strategies/{id}`
- ✅ Seed: 6 estrategias de ejemplo (`seeds/seed_strategies.sql`)
- Tests unitarios: pendientes (no solicitados)

---

## ✅ Módulo 6 — AI Agent / Models (COMPLETO)
**Qué hace:** El cerebro del sistema. Analiza datos con IA y decide si una operación es válida.

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
- ✅ POST /agent/analyze — Prompt Maestro completo
- ✅ Web UI: /agent — Página de análisis con formulario y resultado visual
- ✅ 20 tests unitarios pasando (LLM 100% mockeado, sin llamadas reales)

---

## ✅ Módulo 7 — Bots & Signals (COMPLETO)
**Qué hace:** Instanciar estrategias corriendo automáticamente y generar señales.

Tablas: `bots`, `signals`

Entregables:
- ✅ Bot = cuenta + símbolo + estrategia + feature_set + parámetros de riesgo
- ✅ CRUD bots (start/pause/stop) con máquina de estados en domain entity
- ✅ Cada bot tiene su propio `feature_set_id` (migración m07b)
- ✅ Señales: BUY / SELL / HOLD con entry, SL, TP, position_size, rr_ratio (migración m07a)
- ✅ Señales rechazadas persisten con approved=False (trazabilidad completa)
- ✅ features_hash: SHA-256 del snapshot de features para auditoría
- ✅ Web UI: /bots (usuario) + /admin/bots (admin)
- ✅ 55 tests unitarios pasando (bot entity, status transitions, signal generation)

---

## ✅ Módulo 8 — Orders & Execution (COMPLETO)
**Qué hace:** Ejecutar las órdenes en el exchange real. Es donde el dinero se mueve.

Tablas: `orders`, `fills`, `positions`

Entregables:
- ✅ Domain: Order entity (state machine), Fill entity, Position entity (WAP + P&L)
- ✅ Infrastructure: ORM models + repository impls para orders, fills, positions
- ✅ Execution (Strategy Pattern): PaperExecutor (simula con última vela) + LiveExecutor (ccxt real)
- ✅ Services: list_orders, get_order, create_order, list_fills, list_positions
- ✅ CreateOrderService: valida bot, selecciona executor según bot.mode, crea order+fill+position en transacción atómica
- ✅ Provider: OrderServiceFactory con repos propios + borrowed de M7/M2/M4
- ✅ REST: POST /orders, GET /orders, GET /orders/{id}, GET /fills, GET /positions
- ✅ Web UI usuario: /orders con tabs Órdenes/Posiciones/Ejecuciones + modal crear orden
- ✅ Web UI admin: /admin/orders con filtros por lado/estado/tipo + modal fills
- ✅ LiveExecutor: integración completa ccxt + Fernet credentials

---

## 📌 Módulo 9 — Alerts
**Qué hace:** Notificar cuando ocurren eventos importantes.

Tablas: `alert_rules`, `alert_events`

Entregables:
- Reglas configurables: precio rompe nivel, P&L supera/baja umbral, señal generada
- Canales: email (SMTP ya configurado), webhook (URL externa)
- Historial de alertas disparadas
- Web UI: gestión de alertas
- Test unitarios

---

## 📌 Módulo 10 — Billing & Managed Accounts
**Qué hace:** Modelo de negocio. Inversores aportan capital, el bot lo opera, y el sistema
cobra automáticamente un porcentaje de las ganancias (performance fee).

Tablas nuevas: `investors`, `managed_accounts`, `billing_periods`, `fee_transactions`

Modelo de negocio: Managed Account
- Inversor deposita capital en una cuenta del sistema
- Bot opera ese capital con las estrategias configuradas
- Al cierre del período: si hay PnL positivo → se calcula y registra la performance fee
- Si hay pérdida → no se cobra (High-Water Mark opcional para proteger al inversor)

Entregables:
- CRUD inversores (nombre, email, capital aportado, fee_pct configurado)
- Cálculo automático de performance fee al cerrar período (diario/semanal/mensual)
- High-Water Mark: solo cobrar fee sobre nuevos máximos de capital (evitar cobrar 2 veces)
- Estado de cuenta por inversor: capital, ganancias brutas, fee cobrado, neto inversor
- Historial de fee_transactions auditables
- Email automático al inversor al cierre de período
- Web UI admin: panel de inversores + fees acumulados
- Web UI inversor: dashboard con rendimiento y estado de cuenta

Roles necesarios:
- role_id=3 → investor (nuevo rol, solo ve su propio dashboard)
- role_id=2 → admin (gestiona todos los inversores y fees)

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
