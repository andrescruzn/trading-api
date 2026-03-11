# El sistema completo — Trading AI API

## ¿Qué hace este sistema en una frase?

Observa el mercado, calcula indicadores, consulta a una IA, y si la operación vale la pena, compra o vende automáticamente.

---
PARTE 1 — Conceptos de Trading que necesitas dominar

1.1 ¿Qué es una vela (candle)?

El precio de un activo (ej: Bitcoin) no es un solo número — cambia cada segundo. Para resumir eso en un período de tiempo usamos
velas OHLCV:

┌─────────────────────────────────────────────────┐
│  O = Open    → precio al ABRIR el período       │
│  H = High    → precio MÁS ALTO del período      │
│  L = Low     → precio MÁS BAJO del período      │
│  C = Close   → precio al CERRAR el período      │
│  V = Volume  → cuánto se negoció en ese período │
└─────────────────────────────────────────────────┘

Ejemplo real — vela de BTC/USDT en 1 hora:
ts:     2026-02-26 14:00:00
open:   95,000 USDT
high:   96,200 USDT
low:    94,800 USDT
close:  95,900 USDT
volume: 1,245.5 BTC

Eso significa: a las 2pm abrió en $95k, subió hasta $96.2k, bajó hasta $94.8k, y cerró en $95.9k.

---
1.2 ¿Qué es un Exchange?

Es la bolsa donde se compran y venden activos. Como Binance, Bybit, Kraken. El sistema puede conectarse a varios.

---
1.3 ¿Qué es un Symbol (par)?

Es lo que se negocia: BTC/USDT significa "compro Bitcoin pagando con USDT (dólar digital)". Cada symbol pertenece a un exchange.

---
1.4 ¿Qué es un Timeframe?

El período que representa cada vela:

- 1m = cada vela dura 1 minuto
- 1h = cada vela dura 1 hora
- 1d = cada vela dura 1 día

Un trader de largo plazo usa 1d. Uno de corto plazo usa 5m o 15m.

---
1.5 ¿Qué son los Indicadores Técnicos (features)?

Son cálculos matemáticos sobre las velas que ayudan a predecir hacia dónde va el precio. Ejemplos:

┌──────────────────┬─────────────────────────────────────────────────────────┬─────────────────────────────────────────────┐
│    Indicador     │                        Qué mide                         │                   Ejemplo                   │
├──────────────────┼─────────────────────────────────────────────────────────┼─────────────────────────────────────────────┤
│ EMA(20)          │ Promedio móvil de los últimos 20 cierres                │ Si precio > EMA → tendencia alcista         │
├──────────────────┼─────────────────────────────────────────────────────────┼─────────────────────────────────────────────┤
│ RSI              │ Si está sobrecomprado o sobrevendido (0-100)            │ RSI > 70 → puede caer pronto                │
├──────────────────┼─────────────────────────────────────────────────────────┼─────────────────────────────────────────────┤
│ MACD             │ Diferencia entre dos EMAs. Detecta cambios de tendencia │ Cruce alcista → señal de compra             │
├──────────────────┼─────────────────────────────────────────────────────────┼─────────────────────────────────────────────┤
│ Bollinger Bands  │ Rango estadístico del precio                            │ Precio toca banda inferior → rebote posible │
├──────────────────┼─────────────────────────────────────────────────────────┼─────────────────────────────────────────────┤
│ ATR              │ Volatilidad promedio por vela                           │ Útil para calcular Stop Loss                │
├──────────────────┼─────────────────────────────────────────────────────────┼─────────────────────────────────────────────┤
│ Volumen relativo │ Si el volumen actual es mayor al promedio               │ Volumen alto = movimiento real              │
└──────────────────┴─────────────────────────────────────────────────────────┴─────────────────────────────────────────────┘

---
1.5.1 ¿Qué es un Feature Set?

Un Feature Set es una etiqueta que agrupa y versiona un conjunto de indicadores. No es una estrategia — es simplemente un nombre para identificar qué indicadores se calcularon y con qué configuración.

Ejemplo del Feature Set que se crea en el sistema:

  Nombre:  default
  Versión: 1.0.0
  Spec:    {"rsi": true, "ema": [20, 50, 200], "macd": true, "atr": true, "bbands": true}

¿Qué significa el Spec (JSON)?

  "rsi": true
    → RSI (Relative Strength Index): mide si un activo está sobrecomprado o sobrevendido. Va de 0 a 100.
      Por encima de 70 = sobrecomprado (puede bajar pronto).
      Por debajo de 30 = sobrevendido (puede subir pronto).

  "ema": [20, 50, 200]
    → EMA (Exponential Moving Average): es el precio promedio de las últimas X velas. Muestra la tendencia.
      EMA 20  = promedio de las últimas 20 velas  → tendencia de corto plazo
      EMA 50  = promedio de las últimas 50 velas  → tendencia de mediano plazo
      EMA 200 = promedio de las últimas 200 velas → tendencia de largo plazo
      Cuando el precio está por encima de la EMA 200 → mercado alcista. Por debajo → bajista.

  "macd": true
    → MACD (Moving Average Convergence Divergence): mide la fuerza y dirección del movimiento.
      Cuando la línea MACD cruza hacia arriba → señal de compra.
      Cuando cruza hacia abajo → señal de venta.

  "atr": true
    → ATR (Average True Range): mide cuánto se mueve el precio en promedio por vela. Es la volatilidad.
      Si BTC tiene ATR de 500, significa que en promedio se mueve $500 por vela.
      Se usa principalmente para calcular el Stop Loss.

  "bbands": true
    → Bollinger Bands: tres líneas alrededor del precio (banda superior, media e inferior).
      Cuando el precio toca la banda superior → está caro, posible caída.
      Cuando toca la banda inferior → está barato, posible rebote.
      Bandas angostas = mercado tranquilo. Bandas anchas = mercado volátil.

En conjunto estos 5 indicadores le dan al agente de IA todo lo que necesita:
  ¿El mercado sube o baja?          → EMA
  ¿Está agotado el movimiento?      → RSI
  ¿Hay momentum?                    → MACD
  ¿Cuánto poner de Stop Loss?       → ATR
  ¿El precio está en extremos?      → Bollinger Bands

El Spec es solo documentación — es como una receta escrita que describe los ingredientes. El sistema
siempre calcula todos los indicadores disponibles independientemente de lo que diga el Spec.

¿Para qué sirve el Feature Set en la práctica?

  1. Calculas los indicadores de BTC/USDT 1h y los guardas bajo el nombre "default v1.0.0"
  2. En el futuro, el bot dice: "dame los indicadores de BTC/USDT 1h del feature set default"
  3. El agente de IA recibe esos datos ya calculados y toma su decisión

¿Necesitas crear varios Feature Sets?

No necesariamente. Con "default v1.0.0" puedes operar todos los símbolos y timeframes.
Solo crearías uno nuevo si en el futuro quisieras usar parámetros diferentes (ej: EMA de 10/30/100
en vez de 20/50/200) sin borrar los datos del feature set original.

---
1.6 ¿Qué es el Régimen de Mercado?

El mercado tiene dos estados fundamentales:

TENDENCIA (Trending)           LATERAL (Ranging)
─────────────────────          ─────────────────
    ↗ ↗ ↗ ↗                   ↗ ↘ ↗ ↘ ↗ ↘
El precio hace máximos         El precio rebota entre
y mínimos más altos (HH/HL)    dos niveles sin salir
─────────────────────          ─────────────────
Estrategia: seguir             Estrategia: comprar abajo,
la tendencia                   vender arriba

Crítico: Una estrategia de tendencia aplicada en mercado lateral pierde dinero. El sistema detecta esto automáticamente y cancela
  la operación si no coincide.

---
1.7 ¿Qué es una Estrategia?

Es un conjunto de reglas que definen cuándo entrar y salir del mercado. Ejemplos:

- Trend-following: "Compra cuando EMA(20) cruza EMA(50) hacia arriba Y el RSI < 60 Y el volumen es 1.5x el promedio"
- Mean-reversion: "Compra cuando el precio toca la banda inferior de Bollinger Y el RSI < 30"

Cada estrategia funciona mejor en un régimen específico.

---
1.8 ¿Qué es un Bot?

Un bot es una instancia de una estrategia funcionando automáticamente:

Bot = Estrategia + Símbolo + Timeframe + Cuenta + Parámetros de riesgo

Ejemplo: Bot #1 aplica la estrategia "Trend BTC" sobre BTC/USDT en timeframe 1h usando la cuenta de Binance de Andrés,
arriesgando máximo 1% del capital por operación.

---
1.9 ¿Qué es una Señal (Signal)?

Cuando el bot analiza el mercado y sus reglas se cumplen, genera una señal:

{
  "action": "buy",
  "confidence": 0.87,
  "entry_price": 95500,
  "stop_loss": 94000,
  "take_profit": 98500,
  "position_size": 0.05 BTC
}

Una señal NO ejecuta nada por sí sola. Primero pasa por filtros.

---
1.10 ¿Qué es el Ratio Riesgo/Recompensa (R/R)?

Antes de ejecutar, el sistema evalúa si vale la pena arriesgar:

Riesgo   = Entrada − Stop Loss   = $95,500 − $94,000 = $1,500
Ganancia = Take Profit − Entrada = $98,500 − $95,500 = $3,000

R/R = Ganancia / Riesgo = $3,000 / $1,500 = 2:1

Regla de oro del sistema: si R/R < 2:1, la señal se RECHAZA automáticamente.

---
1.11 La Regla del 1% (gestión de riesgo)

No importa cuánto capital tengas, nunca arriesgas más del 1% en una sola operación:

Capital: $10,000
Riesgo máximo (1%): $100

Stop Loss está a $1,500 del precio de entrada
→ Tamaño de posición = $100 / $1,500 = 0.0667 BTC

Si el precio cae $1,500 y se activa el Stop Loss,
pierdes exactamente $100 (1% del capital). Nada más.

---
1.12 ¿Qué son las Órdenes (Orders)?

Una orden es la instrucción real al exchange para comprar o vender:

┌────────────┬──────────────────────────────────────────────────────────────────┐
│    Tipo    │                             Qué hace                             │
├────────────┼──────────────────────────────────────────────────────────────────┤
│ Market     │ Compra/vende ahora al precio actual (ejecución inmediata)        │
├────────────┼──────────────────────────────────────────────────────────────────┤
│ Limit      │ Compra/vende solo si el precio llega a X (puede no ejecutarse)   │
├────────────┼──────────────────────────────────────────────────────────────────┤
│ Stop       │ Activa una venta de emergencia si el precio baja a X (Stop Loss) │
├────────────┼──────────────────────────────────────────────────────────────────┤
│ Stop-Limit │ Igual que stop, pero con precio límite                           │
└────────────┴──────────────────────────────────────────────────────────────────┘

---
1.13 ¿Qué son Fills y Positions?

- Fill: La confirmación de que una orden se ejecutó, con el precio real y la comisión cobrada. Una orden puede tener varios fills
  (ejecución parcial).
- Position: El estado actual de lo que tienes abierto. Si compraste 0.05 BTC y no lo has vendido, tienes una posición abierta de
0.05 BTC.

---
PARTE 2 — El flujo completo de extremo a extremo

Ahora conectemos todo en una secuencia lógica:

┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  1. MARKET DATA          Exchange (Binance)                     │
│     ─────────────        ─────────────────                      │
│     Descarga velas  ←──  BTC/USDT 1h OHLCV                     │
│     las guarda en DB                                            │
│           │                                                     │
│           ▼                                                     │
│  2. FEATURE ENGINEERING                                         │
│     ───────────────────                                         │
│     Calcula indicadores sobre las velas                         │
│     RSI=62, EMA20=95k, MACD=+150, régimen=TENDENCIA            │
│     Guarda en candle_features                                   │
│           │                                                     │
│           ▼                                                     │
│  3. AI AGENT (Ollama LLM)                                       │
│     ──────────────────────                                      │
│     Recibe: features + estrategia + cuenta                      │
│     Aplica Prompt Maestro:                                      │
│       ① ¿Régimen coincide con estrategia?  → SÍ ✓              │
│       ② ¿Todas las reglas se cumplen?      → SÍ ✓              │
│       ③ Calcula posición: $100/($95500-$94000) = 0.066 BTC     │
│       ④ ¿R/R >= 2:1?                       → SÍ ✓ (2.0)       │
│     Salida: APROBADA                                            │
│           │                                                     │
│           ▼                                                     │
│  4. BOT & SIGNALS                                               │
│     ─────────────                                               │
│     El bot recibe la aprobación                                 │
│     Genera señal: BUY BTC @ $95,500 | SL $94,000 | TP $98,500  │
│           │                                                     │
│           ▼                                                     │
│  5. ORDERS & EXECUTION                                          │
│     ──────────────────                                          │
│     Envía orden MARKET BUY 0.066 BTC a Binance                  │
│     Fill recibido: 0.066 BTC @ $95,520 (precio real)           │
│     Posición abierta registrada                                 │
│     Órdenes Stop Loss y Take Profit colocadas                   │
│           │                                                     │
│           ▼                                                     │
│  6. MONITORING                                                  │
│     ──────────                                                  │
│     Precio sube a $98,500 → Take Profit activado               │
│     Orden de venta ejecutada                                    │
│     Ganancia: ~$198 (2% del capital)                            │
│     Portfolio snapshot guardado                                 │
│           │                                                     │
│           ▼                                                     │
│  7. ALERTS                                                      │
│     ───────                                                     │
│     Email a Andrés: "Take Profit alcanzado en BTC/USDT"        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
