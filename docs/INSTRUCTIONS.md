Paso 1 — Verificar datos base (ya vienen con los seeds)                                                                           
                                         
  Entra a:
  - /admin/symbols → debes ver los símbolos de Binance (el único exchange de la plataforma)
  - /admin/symbols → debes ver BTC/USDT, ETH/USDT, XAU/USD, etc.
  - /admin/timeframes → debes ver 1m, 5m, 1h, 4h, 1d, etc.

  Si no aparecen, ejecuta los seeds de nuevo.

  ---
  Paso 2 — Cargar velas OHLCV

  Sin velas no hay features, sin features no hay señales.

  Lo normal: crea el agente e inícialo (el scheduler descarga solo) o pulsa
  "Actualizar datos" en su pestaña Mercado. Como admin, también por API:
  POST /candles/fetch
  {
    "symbol_id": 1,        ← id del símbolo (ej: BTC/USDT Binance)
    "timeframe_id": 6,     ← id del timeframe (ej: 1h)
    "limit": 500           ← cuántas velas hacia atrás
  }
  O desde Swagger /docs → POST /candles/fetch.

  ▎ Necesitas al menos 220 velas para que el cálculo de EMA200 sea confiable.

  ---
  Paso 3 — Crear un Feature Set

  Ve a /admin/feature-sets → Crear nuevo:
  {
    "name": "Indicadores Base",
    "version": "1.0.0",
    "spec": {
      "indicators": ["rsi_14", "ema_20", "ema_50", "ema_200", "macd", "atr_14", "bb", "vol_rel"],
      "regime": true
    }
  }
  Luego haz clic en Calcular para ese feature set, seleccionando el símbolo y timeframe que cargaste.

  ---
  Paso 4 — Dinero: billetera de Binance o monto simulado

  Ya no se crean cuentas (Mis cuentas se retiró el 2026-10-26). Hay dos caminos:
  - Agente demo (para empezar): no necesita nada; al crearlo escribes el monto simulado.
  - Agente real: pon BINANCE_API_KEY y BINANCE_API_SECRET en el .env del servidor (sin permiso
    de retiro), reinicia la API y revisa el saldo en Administración → Fondo → Billetera.

  ---
  Paso 5 — Verificar Estrategias

  Ve a Explorar → Estrategias (/#/strategies) → ya tienes 6 estrategias de ejemplo del seed. Elige una según tu objetivo:

  ┌────────────────────────┬─────────────────┬──────────────────────┐
  │       Estrategia       │      Tipo       │    Cuándo aplica     │
  ├────────────────────────┼─────────────────┼──────────────────────┤
  │ Trend Following BTC 4h │ trend_following │ mercado en tendencia │
  ├────────────────────────┼─────────────────┼──────────────────────┤
  │ Mean Reversion ETH 1h  │ mean_reversion  │ mercado lateral      │
  └────────────────────────┴─────────────────┴──────────────────────┘

  Si quieres crear una propia, define el JSON de parameters con strategy_type, regime_required, rules y risk_pct.

  ---
  Paso 6 — Crear un agente

  Ve a Agentes demo → Crear agente demo (o Inicio → Crear agente real):
  1. Símbolo: BTC/USDT.
  2. Estrategia y conjunto de indicadores (el recomendado viene marcado).
  3. Dinero: en demo, el monto a invertir (por ejemplo 10.000 USDT); en real, la billetera de
     Binance (su capital se le asigna desde Agentes del fondo).
  4. Nombre y modo de ejecución (Manual para empezar). El riesgo (1 %) lo pone la estrategia.

  ---
  Paso 7 — Iniciar el Bot y generar señales

  1. Ve a /bots → busca tu bot → clic Start
  2. Clic en Generar Señal — el agente IA analiza las features y decide BUY / SELL / HOLD
  3. Si la señal es APPROVED, ve a /orders → Nueva Orden basada en los precios sugeridos (entry, SL, TP)

  ---
  Resumen del flujo

  Seeds listos
      ↓
  Cargar velas (fetch 500 velas de BTC/USDT 1h)
      ↓
  Crear Feature Set + Calcular indicadores
      ↓
  Crear Account (paper)
      ↓
  Elegir/crear Estrategia
      ↓
  Crear Bot (account + symbol + strategy + feature_set)
      ↓
  Start Bot → Generar Señal → Crear Orden

  ---
  ¿Por cuál paso quieres que empecemos? ¿Tienes ya las velas cargadas o necesitas ayuda con el fetch?