Paso 1 — Verificar datos base (ya vienen con los seeds)                                                                           
                                         
  Entra a:
  - /admin/exchanges → debes ver Binance, Bybit, Kraken, etc.
  - /admin/symbols → debes ver BTC/USDT, ETH/USDT, XAU/USD, etc.
  - /admin/timeframes → debes ver 1m, 5m, 1h, 4h, 1d, etc.

  Si no aparecen, ejecuta los seeds de nuevo.

  ---
  Paso 2 — Cargar velas OHLCV

  Sin velas no hay features, sin features no hay señales.

  Ve a /admin/candles/ingest y usa el endpoint de fetch:
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
  Paso 4 — Crear una Cuenta de Trading

  Ve a /admin/accounts → Crear cuenta:

  ┌─────────────────┬───────────────────────────────────┐
  │      Campo      │  Valor recomendado para empezar   │
  ├─────────────────┼───────────────────────────────────┤
  │ Nombre          │ Paper BTC Binance                 │
  ├─────────────────┼───────────────────────────────────┤
  │ Exchange        │ Binance                           │
  ├─────────────────┼───────────────────────────────────┤
  │ Modo            │ paper (simulado, sin dinero real) │
  ├─────────────────┼───────────────────────────────────┤
  │ Moneda base     │ USDT                              │
  ├─────────────────┼───────────────────────────────────┤
  │ Capital inicial │ lo que quieras simular (ej: 1000) │
  └─────────────────┴───────────────────────────────────┘

  ---
  Paso 5 — Verificar Estrategias

  Ve a /admin/strategies → ya tienes 6 estrategias de ejemplo del seed. Elige una según tu objetivo:

  ┌────────────────────────┬─────────────────┬──────────────────────┐
  │       Estrategia       │      Tipo       │    Cuándo aplica     │
  ├────────────────────────┼─────────────────┼──────────────────────┤
  │ Trend Following BTC 4h │ trend_following │ mercado en tendencia │
  ├────────────────────────┼─────────────────┼──────────────────────┤
  │ Mean Reversion ETH 1h  │ mean_reversion  │ mercado lateral      │
  └────────────────────────┴─────────────────┴──────────────────────┘

  Si quieres crear una propia, define el JSON de parameters con strategy_type, regime_required, rules y risk_pct.

  ---
  Paso 6 — Crear un Bot

  Ve a /admin/bots → Crear bot:

  ┌─────────────┬───────────────────────────────────────────────────┐
  │    Campo    │                       Valor                       │
  ├─────────────┼───────────────────────────────────────────────────┤
  │ Account     │ la que creaste en paso 4                          │
  ├─────────────┼───────────────────────────────────────────────────┤
  │ Symbol      │ BTC/USDT (Binance)                                │
  ├─────────────┼───────────────────────────────────────────────────┤
  │ Timeframe   │ 1h                                                │
  ├─────────────┼───────────────────────────────────────────────────┤
  │ Strategy    │ Trend Following BTC 4h                            │
  ├─────────────┼───────────────────────────────────────────────────┤
  │ Feature Set │ el que creaste en paso 3                          │
  ├─────────────┼───────────────────────────────────────────────────┤
  │ Mode        │ paper                                             │
  ├─────────────┼───────────────────────────────────────────────────┤
  │ Risk params │ {"risk_pct": 0.01} (1% del capital por operación) │
  └─────────────┴───────────────────────────────────────────────────┘

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