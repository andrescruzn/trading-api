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

## 📌 Módulo 5 — Strategies
**Qué hace:** Definir las reglas de entrada/salida del agente.

Tablas: `strategies`, `datasets`

Entregables:
- CRUD estrategias con config JSON (reglas, régimen requerido, timeframe, etc.)
- Tipos soportados: trend-following, mean-reversion
- Datasets de backtesting (historial de velas + features etiquetados)
- Validación: una estrategia de tendencia no aplica en régimen lateral (y viceversa)
- Web UI: editor de estrategias
- Test unitarios

---

## 📌 Módulo 6 — AI Agent / Models
**Qué hace:** El cerebro del sistema. Analiza datos y decide si una operación es válida.

Tablas: `models`, `model_runs`, `predictions`

**LLM: Ollama (local, en PC)**
- Ollama corre en localhost. No se usa API externa (ni Gemini ni GPT) por ahora.
- Modelos candidatos: `llama3`, `mistral`, `phi3` (configurar cuál usar en settings)
- Integración vía HTTP a `http://localhost:11434` (API REST de Ollama)
- Producción/nube: se añadirá en el futuro — por ahora solo entorno local

Prompt Maestro aplicado:
1. Filtro de Régimen → cancela si régimen no coincide con estrategia
2. Validación de reglas → cancela si falta UNA regla
3. Cálculo de posición → el LLM genera Python: Capital × %Riesgo / (Entrada − SL)
4. Ratio R/R → solo procede si ganancia proyectada >= 2× el riesgo
Salida: APROBADA / RECHAZADA + Entrada / SL / TP / Tamaño de posición

Entregables:
- Integración con Ollama (HTTP client → localhost:11434)
- El LLM genera código Python para matemática de posición (evitar alucinaciones)
- Registro de cada predicción con datos de entrada, salida y razón
- Endpoint: POST /agent/analyze { symbol, timeframe, strategy_id, account_id }
- Tests con respuestas mockeadas del LLM (sin levantar Ollama en CI)

---

## 📌 Módulo 7 — Bots & Signals
**Qué hace:** Instanciar estrategias corriendo automáticamente y generar señales.

Tablas: `bots`, `signals`

Entregables:
- Bot = cuenta + símbolo + estrategia + parámetros de riesgo
- CRUD bots (activar/pausar/detener)
- Señales generadas: BUY / SELL / HOLD con precio entrada, SL, TP, tamaño
- Filtro automático: señales con ratio R/R < 2:1 son RECHAZADAS automáticamente
- Regla del 1%: tamaño calculado para no arriesgar más del 1% del capital
- Web UI: panel de bots activos y señales recientes
- Tests de la lógica de filtrado

---

## 📌 Módulo 8 — Orders & Execution ← AQUÍ SE COMPRA Y SE VENDE
**Qué hace:** Ejecutar las órdenes en el exchange real. Es donde el dinero se mueve.

Tablas: `orders`, `fills`, `positions`

Entregables:
- Envío de órdenes al exchange vía API (market order, limit order, stop-limit)
- Tipos de orden: OPEN (compra/venta inicial), CLOSE (cierre de posición)
- Registro de fills: ejecución parcial o total, precio real, comisión
- Gestión de posiciones abiertas: P&L en tiempo real
- Cierre automático al llegar al Stop Loss o Take Profit
- Endpoint: POST /orders (ejecutar) | GET /positions (ver abiertas)
- Web UI: libro de órdenes, posiciones abiertas, historial de trades
- Tests con exchange mockeado (no tocar dinero real en tests)

Tipos de operaciones:
- Compra (LONG): entra comprando, cierra vendiendo
- Venta en corto (SHORT): entra vendiendo, cierra comprando (si el exchange lo permite)
- Stop Loss: cierre automático si el precio va en contra
- Take Profit: cierre automático al alcanzar la ganancia objetivo

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
```
