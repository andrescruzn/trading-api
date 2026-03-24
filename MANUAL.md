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
│  3. AI AGENT (LLM multi-provider)                               │
│     ──────────────────────────────                              │
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

---
PARTE 3 — Módulos implementados y cómo usarlos

3.1 Módulo 5 — Strategies (Estrategias)

Una estrategia es el conjunto de reglas que define cuándo el sistema debe considerar una operación.
Cada estrategia tiene:

- strategy_type: el "estilo" de trading
  · trend_following  → sigue la tendencia. Solo opera si el mercado hace máximos más altos (HH/HL).
  · mean_reversion   → apuesta a que el precio volverá a su promedio. Solo opera en mercado lateral.

- regime_required: el régimen de mercado que debe existir para activarse
  · trend_up    → el mercado sube (trend_following)
  · trend_down  → el mercado baja (trend_following)
  · sideways    → mercado lateral (mean_reversion)
  · null/vacío  → sin restricción de régimen

- timeframe_code: en qué marco temporal opera (ej: "1h", "4h", "1d")

- rules: lista de condiciones que deben cumplirse para generar una señal
  Ejemplo: [{"indicator": "rsi_14", "operator": "lt", "value": 30}]
  Significa: "el RSI de 14 períodos debe ser menor que 30"

- risk_pct: porcentaje del capital a arriesgar por operación (default: 0.01 = 1%)

Regla de coherencia (se valida automáticamente):
  trend_following + sideways → RECHAZADO (una estrategia de tendencia no opera en lateral)
  mean_reversion + trend_up  → RECHAZADO (una estrategia de reversión no opera en tendencia)

3.2 Módulo 5 — Datasets

Un dataset es un recorte de datos históricos (velas + features) para backtesting o entrenamiento:
- Referencia un símbolo, timeframe y rango de fechas
- Tiene un query_spec JSON que define cómo se construyó
- Se usará en futuros módulos (AI Agent, entrenamiento de modelos) para evaluar estrategias

---
3.3 Módulo 6 — AI Agent (Agente de IA)

El agente es el motor de decisión del sistema. Recibe una combinación de símbolo + timeframe + estrategia + cuenta y
devuelve un veredicto: APROBADA o RECHAZADA.

Internamente aplica el Prompt Maestro con 4 fases en secuencia:

  FASE 1 — Filtro de Régimen
  ──────────────────────────
  Compara el régimen actual del mercado (calculado en M3) con el régimen requerido por la estrategia.
  Si no coinciden → RECHAZADA al instante.

  Ejemplo:
    Estrategia requiere: trend_up
    Régimen actual:      sideways
    → RECHAZADA ("Régimen actual no coincide con el requerido")

  FASE 2 — Validación de Reglas
  ──────────────────────────────
  Evalúa cada regla de la estrategia contra las features calculadas.
  Si ALGUNA regla falla → RECHAZADA.

  Ejemplo de reglas:
    [{"indicator": "rsi_14", "operator": "lt", "value": 60}]
    → RSI de 14 períodos debe ser menor que 60

  Operadores soportados: lt (<), gt (>), lte (<=), gte (>=), eq (=)

  Si las reglas pasaron pero RSI actual = 72 → RECHAZADA ("rsi_14 lt 60 (actual: 72.00)")

  FASE 3 — LLM calcula Entry / Stop Loss / Take Profit
  ─────────────────────────────────────────────────────
  El agente llama al LLM configurado con el precio actual y el ATR.
  El LLM sugiere los niveles y Python ejecuta la fórmula de posición:

    position_size = (capital × risk_pct) / |entry − stop_loss|

  Ejemplo real:
    Capital:      $10,000
    risk_pct:     1% (0.01)
    Entry:        $95,500
    Stop Loss:    $94,250  (entry - ATR × 1.5)
    Take Profit:  $98,000  (entry + ATR × 3.0)

    position_size = ($10,000 × 0.01) / |$95,500 − $94,250|
                  = $100 / $1,250
                  = 0.08 BTC

  FASE 4 — Filtro Ratio R/R
  ──────────────────────────
  Calcula: rr_ratio = (take_profit - entry) / (entry - stop_loss)
  Si rr_ratio < 2.0 (configurable con AGENT_MIN_RR_RATIO) → RECHAZADA.

  Con los datos del ejemplo:
    rr_ratio = ($98,000 - $95,500) / ($95,500 - $94,250) = $2,500 / $1,250 = 2.0 ✓

  → APROBADA

LLM multi-provider
──────────────────
El agente no está atado a un solo proveedor de IA. Soporta:

  LLM_PROVIDER  | Servicio              | Notas
  ──────────────────────────────────────────────────────────
  openai        | OpenAI (GPT-4o, etc.) | Default
  anthropic     | Anthropic (Claude)    | Requiere API key
  xai           | xAI (Grok)            | API key de xAI
  deepseek      | DeepSeek              | Económico, bueno
  gemini        | Google Gemini         | API key de Google
  ollama        | Ollama local          | Sin costo, sin red

  Configurar en .env:
    LLM_PROVIDER=ollama
    LLM_MODEL=gemma3:4b
    LLM_API_KEY=           (vacío para ollama)

Modelos ML (tabla `models`)
───────────────────────────
El módulo también registra modelos de machine learning (xgboost, lightgbm, sklearn, nn) con su metadata:
nombre, versión, estado (active/deprecated/archived), URI del artefacto.
Esto prepara el sistema para el futuro entrenamiento y evaluación formal de modelos en el Módulo 7+.

Model Runs (tabla `model_runs`)
────────────────────────────────
Cada entrenamiento queda registrado como un "run": fecha de inicio, estado (running/success/failed),
métricas (accuracy, F1, etc.) y parámetros usados. Permite comparar versiones del mismo modelo.

---
3.4 Módulo 7 — Bots & Signals (Bots y Señales)

Un bot es la pieza que automatiza todo. Une una estrategia, un símbolo, un timeframe, una cuenta y
un feature set en una sola unidad que puede generar señales de trading de forma continua.

¿Qué es un Bot exactamente?

  Bot = Cuenta + Símbolo + Timeframe + Estrategia + Feature Set + Risk %

  Ejemplo: Bot #1 opera BTC/USDT en 1h usando la estrategia "Trend BTC v1.0", con el feature set
  "default v1.0.0", en la cuenta de Binance de Andrés, arriesgando máximo 1% del capital por operación.

Cada bot tiene su propio Feature Set porque distintos bots pueden necesitar diferentes conjuntos
de indicadores. Un bot de tendencia y uno de reversión pueden usar indicadores distintos.

Estados de un bot:

  stopped  → El bot está detenido (estado inicial)
  running  → El bot está activo generando señales
  paused   → El bot está pausado temporalmente (conserva su configuración)
  error    → El bot se detuvo por un error interno

Transiciones válidas (máquina de estados):

  stopped  → running            (iniciar el bot)
  running  → paused             (pausar temporalmente)
  running  → stopped            (detener)
  running  → error              (fallo interno)
  paused   → running            (reanudar)
  paused   → stopped            (detener desde pausa)
  error    → stopped            (resetear tras error)

No se puede saltar estados: por ejemplo, desde "error" no se puede pasar directamente a "running".
Primero hay que volver a "stopped" y luego a "running".

Regla importante: solo se puede editar un bot cuando está en estado "stopped". Si el bot está
running o paused, los cambios de configuración están bloqueados para evitar inconsistencias.

Señales y cómo se generan:

  1. El bot invoca al Agente de IA (M6) con su contexto:
     símbolo + timeframe + estrategia + cuenta + feature set del bot
  2. El Agente aplica el Prompt Maestro (4 fases: régimen → reglas → LLM → R/R)
  3. Si APROBADA → la señal tiene acción BUY o SELL + entry, SL, TP, position_size, rr_ratio
  4. Si RECHAZADA → la señal tiene acción HOLD, approved=False
  5. TODAS las señales se guardan en la BD, incluyendo las rechazadas (trazabilidad completa)

¿Cómo se infiere BUY vs SELL?

  El agente calcula entry y stop_loss. La relación entre ellos define la dirección:
  entry > stop_loss → BUY  (compra: ganas si el precio sube)
  entry < stop_loss → SELL (short: ganas si el precio baja)

features_hash:

  Cada señal guarda un SHA-256 del snapshot de indicadores que usó para tomarla.
  Esto permite auditar exactamente qué datos vio el agente cuando tomó la decisión.

Páginas de la UI:
  /bots       → Panel de usuario: lista de bots, crear nuevo, start/pause/stop, ver señales
  /admin/bots → Vista admin: todos los bots del sistema con filtros de estado y modo

---
PARTE 4 — Viabilidad del negocio: Edge y Capital

4.1 ¿Qué es el "edge" y por qué es lo más importante?
───────────────────────────────────────────────────────
Un bot de trading bien construido NO garantiza ganancias por sí solo.
Lo que determina si el sistema gana o pierde dinero es el EDGE: la ventaja estadística
de las estrategias que le metes.

  Edge = Win Rate × Ganancia promedio  >  (1 - Win Rate) × Pérdida promedio

Ejemplo con una estrategia R/R 2:1 (ganas $200, pierdes $100):

  Win rate 45%:  0.45 × $200  −  0.55 × $100  =  $90 − $55  = +$35 por operación  ✓ tiene edge
  Win rate 30%:  0.30 × $200  −  0.70 × $100  =  $60 − $70  = −$10 por operación  ✗ sin edge

Con win rate de 30% el bot pierde dinero AUNQUE cumpla el filtro R/R 2:1.
El filtro R/R es condición necesaria pero no suficiente. Sin edge positivo, el bot
solo ejecuta pérdidas más ordenadamente.

4.2 ¿Cómo se mide el edge en este sistema?
────────────────────────────────────────────
El edge real se construye con el historial acumulado por los módulos:

  Módulo 7 — Signals:  registra cada señal BUY/SELL/HOLD con entry/SL/TP proyectados
  Módulo 8 — Orders:   registra si ganó o perdió, precio real de ejecución, comisión
  Tablas clave:        signals → orders → fills → positions

Con esos datos se pueden calcular:

  Métrica              Qué mide
  ─────────────────────────────────────────────────────────────────
  Win Rate             % de operaciones que terminaron en ganancia
  R/R real             Ganancia promedio / Pérdida promedio (real, no proyectado)
  Max Drawdown         Peor caída acumulada desde un pico de capital
  Sharpe Ratio         Retorno ajustado por riesgo (>1.0 es aceptable, >2.0 es bueno)
  Profit Factor        Suma de ganancias / Suma de pérdidas (>1.5 es viable)

Una estrategia es confiable cuando estos números se mantienen estables durante
al menos 3-6 meses en modo paper (simulado) antes de arriesgar capital real.

4.3 Capital inicial — ¿cuánto se necesita?
────────────────────────────────────────────
La Regla del 1% limita el riesgo por operación al 1% del capital total.
Esto protege de rachas de pérdidas pero también define el tamaño mínimo viable:

  Capital    Riesgo por op (1%)   ¿Es viable?
  ──────────────────────────────────────────────────────────────────────
  $500       $5 por operación     No — las comisiones se comen el edge
  $1,000     $10 por operación    Muy ajustado, solo para aprender
  $5,000     $50 por operación    Mínimo para validar en live con datos reales
  $10,000    $100 por operación   Razonable para demostrar resultados
  $50,000+   $500+ por operación  Donde empieza a ser negocio real

4.4 Hoja de ruta para validar el edge antes de arriesgar capital real
───────────────────────────────────────────────────────────────────────
Paso 1 — Paper trading (M7 + M8 en modo paper):
  Correr el sistema 3-6 meses con datos reales pero sin dinero.
  Los módulos registran cada señal, orden y resultado simulado.
  Objetivo: acumular 100+ operaciones por estrategia para estadísticas confiables.

Paso 2 — Analizar el historial:
  Calcular Win Rate, R/R real, Max Drawdown y Profit Factor del historial acumulado.
  Si los números son positivos y estables → la estrategia tiene edge verificado.

Paso 3 — Live con capital pequeño ($500-$2,000):
  Pasar a modo live con capital mínimo para verificar que el paper no mintió.
  El paper no tiene comisiones, slippage ni latencia reales — el live sí.
  Si los resultados live confirman el edge → escalar capital gradualmente.

Paso 4 — Escalar:
  Solo escalar capital si los resultados live son consistentes con el paper.
  La estrategia puede deteriorarse con el tiempo — revisar métricas mensualmente.

4.5 Rutas de negocio realistas
────────────────────────────────
Con el sistema completo (M1-M9) y un historial verificado de edge positivo:

  Ruta                        Descripción
  ────────────────────────────────────────────────────────────────────────────
  Capital propio              Operar con tu dinero usando estrategias validadas.
                              Requiere capital mínimo $5k-$10k para ser viable.

  SaaS para traders           Cobrar suscripción mensual por acceso al agente.
                              Requiere UI pulida + onboarding + soporte.
                              El diferencial es el historial de resultados reales.

  Señales como servicio       Vender las señales del agente a suscriptores.
                              Modelo Telegram/Discord/email con resultados auditados.
                              Clave: publicar el historial completo, no solo las ganadoras.

  White-label para fondos     Adaptar el sistema para un fondo de inversión pequeño.
                              Requiere track record + posiblemente registro regulatorio.

---
PARTE 5 — Módulo 10: Billing & Managed Accounts (El modelo de negocio)

5.1 ¿Qué es una Managed Account?
──────────────────────────────────
Es el modelo donde una persona (inversor) te entrega capital para que tú lo operes
con el sistema. Si el sistema genera ganancias, tú te quedas con un porcentaje
acordado de esas ganancias. Si pierde, no cobras nada.

Ejemplo real:
  Tu jefe aporta: $10,000 USD
  El bot opera durante un mes y genera: $800 de ganancia (8%)
  Tu performance fee (20%): $160
  Tu jefe recibe: $640 netos

  Si el bot pierde $200 ese mes → tú no cobras nada y el jefe absorbe la pérdida.

Esto alinea los intereses: solo ganas cuando el inversor gana.

5.2 ¿Qué es el High-Water Mark?
─────────────────────────────────
Es una protección para el inversor. Garantiza que no pagas fee dos veces sobre
el mismo capital.

Ejemplo sin High-Water Mark (injusto):
  Mes 1: capital $10,000 → gana $1,000 → cobras fee sobre $1,000 ✓
  Mes 2: capital $11,000 → pierde $500 → no cobras (correcto)
  Mes 3: capital $10,500 → gana $600 → cobras fee sobre $600 ← INJUSTO
  (en mes 3 el capital nunca superó el máximo de $11,000, pero cobras igual)

Con High-Water Mark (justo):
  Solo cobras fee cuando el capital supera su máximo histórico previo.
  En el ejemplo: mes 3 el capital llega a $11,100 → solo cobras fee sobre $100
  (el excedente sobre el máximo anterior de $11,000)

5.3 ¿Cómo funciona en el sistema? (Módulo 10)
───────────────────────────────────────────────
El Módulo 10 automatiza todo esto:

  1. Admin registra al inversor con su capital aportado y el fee_pct acordado (ej: 20%)
  2. El capital queda vinculado a una cuenta de trading del sistema
  3. El bot opera esa cuenta (M7 + M8 generan señales y ejecutan órdenes)
  4. Al cierre de cada período (semanal o mensual):
     - El sistema calcula el PnL neto del período
     - Aplica el High-Water Mark: solo hay fee si hay nuevos máximos
     - Calcula el fee: PnL_positivo × fee_pct
     - Registra la transacción en el historial
     - Envía el estado de cuenta por email al inversor
  5. El inversor puede ver su dashboard: capital, rendimiento, historial de fees

5.4 Roles del sistema (con M10)
─────────────────────────────────
  role_id=1 → Usuario      (trader, accede a sus cuentas y bots)
  role_id=2 → Administrador (gestiona todo: inversores, fees, estrategias)
  role_id=3 → Inversor      (solo ve su propio dashboard de rendimiento)

5.5 ¿Qué necesitas para lanzar esto?
──────────────────────────────────────
  Requisito técnico:   Módulos 7 y 8 funcionando (bots operando en live)
  Requisito legal:     Un contrato simple con el inversor que especifique el % de fee,
                       el período de cobro y las condiciones de retiro
  Requisito de confianza: 3-6 meses de historial paper verificable antes de pedirle
                          dinero real a alguien

La plataforma hace el cálculo automático y transparente — el inversor puede ver
cada operación que ejecutó el bot con su capital.
