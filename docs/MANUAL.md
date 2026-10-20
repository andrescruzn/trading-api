# El sistema completo — Trading App

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

1.3.1 ¿Qué mercados puedo operar? (cripto, metales, materias primas, acciones)

Además de cripto, la app trae **perpetuos TradFi** de Binance y Bybit. Un perpetuo es un contrato
que sigue el precio de un activo real sin que lo compres de verdad: `XAU/USDT:USDT` sube y baja
como el oro, y se paga en USDT. Se reconocen por el `:USDT` al final.

| Clase | Ejemplos en la app | Qué sigue |
|---|---|---|
| Cripto | BTC/USDT, ETH/USDT, SOL/USDT… | La criptomoneda |
| Metal | XAU (oro), XAG (plata), XPT (platino), XPD (paladio), PAXG/USDT | El metal (PAXG es oro tokenizado en spot) |
| Materia prima | CL (petróleo WTI), NATGAS (gas natural), COPPER (cobre) | El precio del barril, del gas o del cobre |
| ETF | SPY (S&P 500), QQQ (Nasdaq 100) | El índice de la bolsa de EE. UU. |
| Acción | NVDA, TSLA, AAPL | La acción de la empresa |

Ventajas: abren 24/7 como la cripto y se descargan igual, así que los agentes funcionan sin cambios.
**Límite actual: los perpetuos solo se operan en modo paper.** En una cuenta real un perpetuo usa
contratos, apalancamiento y posiciones cortas, y la app aún no maneja eso: no te deja crear un
agente live sobre un perpetuo.

Forex (EUR/USD, USD/JPY) y los índices "de verdad" no están conectados: necesitan otro proveedor
de datos y un bróker. Ojo con `SPX/USDT:USDT` en Binance y Bybit: no es el S&P 500, es una memecoin.

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
1.5.1 ¿Qué es un conjunto de indicadores (Feature Set)?

Un conjunto de indicadores dice qué indicadores calcula un agente sobre las velas y cuáles lee la IA
para decidir. No es una estrategia: la estrategia pone las reglas ("RSI menor que 30"), y el conjunto
asegura que ese RSI exista.

¿Por qué hace falta? Porque las reglas de cada estrategia están escritas sobre indicadores. Una regla
como "EMA 20 por encima de EMA 50" no se puede evaluar si nadie calculó las EMA.

El sistema trae tres conjuntos listos (no hay que configurar nada):

  Completo   → todos los indicadores. Sirve para cualquier estrategia.
  Tendencia  → EMA 20/50/200, MACD, RSI, ATR y volumen relativo. Para estrategias que siguen tendencias.
  Rango      → RSI, bandas de Bollinger, MACD, ATR y volumen relativo. Para mercados laterales.

Al crear un agente solo aparecen los conjuntos que calculan todo lo que pide la estrategia elegida,
y el recomendado viene marcado. Por ejemplo, "RSI Mean Reversion" usa las bandas de Bollinger, así
que solo ofrece Rango y Completo.

¿Qué cambia elegir uno u otro? Con un conjunto más chico la IA recibe solo los datos que importan
para esa estrategia, sin ruido. Los periodos (RSI de 14, EMA de 20/50/200…) son los mismos en todos.

¿Qué mide cada indicador?

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

En conjunto estos indicadores le dan a la IA todo lo que necesita:
  ¿El mercado sube o baja?          → EMA
  ¿Está agotado el movimiento?      → RSI
  ¿Hay momentum?                    → MACD
  ¿Cuánto poner de Stop Loss?       → ATR
  ¿El precio está en extremos?      → Bollinger Bands
  ¿El movimiento tiene respaldo?    → Volumen relativo

Además, siempre se calcula el régimen de mercado (ver 1.6), porque toda estrategia lo usa como
primer filtro.

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
1.8 ¿Qué es un Agente (antes "Bot")?

Un agente es una estrategia funcionando sola sobre un símbolo. Es lo primero que se crea para operar
y lo que se ve en el inicio de la app.

Agente = Nombre + Símbolo + Estrategia + Conjunto de indicadores + Cuenta

El timeframe y el riesgo por operación los pone la estrategia; el modo (paper o live) lo pone la cuenta.

Ejemplo: el agente "BTC/USDT · EMA Trend Follower" vigila BTC/USDT en velas de 1h con la estrategia
EMA Trend Follower y el conjunto Tendencia, usando la cuenta de práctica de Andrés y arriesgando como
máximo el 1 % del capital por operación.

Mientras un agente está activo, el sistema descarga solo las velas de su símbolo y calcula sus
indicadores. Si no hay ningún agente activo, no se descarga nada.

(En el código y en la API se sigue llamando "bot". La "IA" es el modelo de lenguaje que el agente
consulta para confirmar cada operación.)

---
1.9 ¿Qué es una Señal (Signal)?

Cuando el agente analiza el mercado y sus reglas se cumplen, genera una señal:

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

Cómo es hoy en la app (octubre 2026):
  - Los pasos 4 y 5 dependen del modo del agente (ver 3.6): en Manual tú creas la orden; en
    Con aprobación la apruebas tú (en la app o en Telegram); en Automático sale sola.
  - Cuando la posición la abre una señal aprobada, queda protegida. En live el stop loss se deja
    como orden en el exchange y el take profit lo revisa el sistema cada minuto; en paper el
    sistema revisa los dos cada minuto (ver 3.6). Las órdenes que creas a mano no llevan esta
    protección.
  - El "portfolio snapshot" del paso 6 todavía no se guarda.

---
PARTE 3 — Módulos implementados y cómo usarlos

3.0 Cómo entrar a la aplicación
───────────────────────────────
La aplicación tiene dos partes que se encienden por separado:

  1. El servidor (la "API"): hace los cálculos y guarda los datos.
  2. La página web: lo que ves en el navegador. En desarrollo se enciende con `pnpm dev`
     y queda en http://localhost:5193 (el servidor tiene que estar encendido).

Las direcciones de la web llevan un "#" después del dominio. Por ejemplo:
  http://localhost:5193/#/login       → pantalla de inicio de sesión
  http://localhost:5193/#/dashboard   → panel principal

Para iniciar sesión no hay contraseña: escribes tu correo, te llega un código de 6 dígitos
y lo escribes antes de que venza (10 minutos). Si no te llegó o se venció, pide uno nuevo;
el código anterior deja de servir. Para frenar a quien intente adivinar códigos, cada correo
puede pedir 3 códigos y probar 5 cada 10 minutos; si se pasa, la pantalla dice cuánto esperar.
Además, después de 5 intentos fallidos con el mismo código, ese código deja de servir y hay que
pedir otro. Tu cuenta nunca se bloquea por esto.

Por seguridad, la pantalla nunca dice si un correo está registrado: siempre pasa al paso del
código y te avisa que, si el correo tiene una cuenta, te llegó un código. Así nadie puede
averiguar quién usa la app probando correos.

Por seguridad solo hay una sesión abierta por persona: si entras desde otro navegador, la
sesión anterior se cierra y la web te muestra "Tu sesión expiró" y te lleva al login.

Todo se navega desde el menú lateral: Inicio, Operar (mis agentes, alertas, mis cuentas),
Explorar (explorar mercados, estrategias) y, según tu rol, "Mi inversión" (inversores)
o "Administración" (administradores). En Administración, "Supervisión" muestra lo de todos los
usuarios: "Todos los agentes" son los mismos agentes del inicio, pero de todo el sistema.

Todo lo que pertenece a un agente se ve dentro del agente: sus señales, sus órdenes, sus
posiciones y los precios e indicadores de su mercado. No hay páginas sueltas de órdenes, velas o
indicadores porque esos datos solo existen para los agentes que creaste y están activos.

El inicio muestra todos tus agentes (con filtro Todos / Activos / Detenidos). Cada tarjeta trae
el último precio de su mercado, cuánto subió o bajó frente a la vela anterior y el régimen
(tendencia o rango). Si aún no tienes ninguno, te explica qué es un agente y te ofrece crear el
primero.

3.0.1 Módulo 2 — Explorar mercados (¿dónde crear un agente?)
─────────────────────────────────────────────────────────────
Las estrategias de tendencia ganan cuando el mercado se mueve con fuerza en una dirección y pierden
en mercados que van de lado. "Explorar mercados" (menú Explorar, `/#/market/explorer`) ordena todos
los mercados por la fuerza de su tendencia en velas diarias, para que elijas dónde vale la pena
poner un agente.

Qué mide cada columna:
- **Tendencia:** Alcista, Bajista o Lateral. Alcista = el precio está sobre su media de 50 días y
  esta sobre la de 200, con fuerza suficiente.
- **ADX:** qué tan fuerte es la tendencia, sin importar la dirección. Menos de 20 = sin tendencia;
  más de 25 = tendencia clara.
- **Eficiencia:** qué tan "limpio" fue el movimiento de los últimos 30 días. 100 % sería una línea
  recta; 10 % es puro zigzag.
- **Fuerza (0–100):** combina ADX y eficiencia. Es la columna que ordena la tabla.
- **30 días / 90 días:** cuánto subió o bajó el precio.
- **Volatilidad:** cuánto se mueve el precio en un día normal (ATR). Más volatilidad = stop loss
  más lejano = posición más pequeña con la regla del 1 %.

Ejemplo: el oro con ADX 32, eficiencia 45 % y +12 % en 90 días tiene fuerza ≈ 29 y sale arriba.
BTC con ADX 15 sale como Lateral aunque haya subido 3 %: no tiene fuerza.

Cómo usarlo:
1. Filtra por clase (metales, materias primas…) si quieres.
2. Elige un mercado alcista con fuerza alta y pulsa "Crear agente": el asistente se abre con ese
   mercado elegido. Para metales y TradFi hay una estrategia pensada para ellos: "Tendencia Metales" (4h).
3. Los mercados bajistas dicen "Solo observación": la app solo abre compras.

Los datos se actualizan solos una vez al día. Un administrador puede pulsar "Actualizar datos"
para traerlos en el momento (tarda unos segundos por mercado la primera vez).

Importante: que un mercado haya tenido tendencia no garantiza que siga. El explorador sirve para
elegir dónde operar. Cada operación la sigue filtrando el agente con el régimen, la regla del 1 % y
el riesgo/beneficio mínimo de 2:1.

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
3.3 Módulo 6 — AI Agent (la IA que decide)

La IA es el motor de decisión del sistema. Recibe una combinación de símbolo + timeframe + estrategia + cuenta y
devuelve un veredicto: APROBADA o RECHAZADA. Solo ve los indicadores del conjunto del agente.

No tiene una página propia: se usa desde el detalle de cada agente con el botón "Analizar ahora"
(ver 3.4), o sola en cada vela cerrada para los agentes en modo Con aprobación o Automático
(ver 3.6). Para controlar el costo, cada persona puede pedir como máximo 6 análisis por minuto.

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

  Antes de calcular, Python revisa que los niveles de la IA tengan sentido. Si no, RECHAZADA:
    - En una compra el stop loss va por debajo de la entrada y el take profit por encima (en una
      venta, al revés). Si quedan del mismo lado → "Los niveles de la IA no son coherentes".
    - La entrada no puede alejarse del precio actual más de 1 ATR (si el conjunto no calcula
      ATR, más de 2 % del precio) → "La entrada que propuso la IA está demasiado lejos del
      precio actual". Así la IA no puede inventar un precio.
    - El riesgo usado nunca pasa del 1 %, aunque la estrategia o el agente pidan más.

  FASE 4 — Filtro Ratio R/R
  ──────────────────────────
  Calcula: rr_ratio = (take_profit - entry) / (entry - stop_loss)
  Si rr_ratio < 2.0 (configurable con AGENT_MIN_RR_RATIO) → RECHAZADA.

  Con los datos del ejemplo:
    rr_ratio = ($98,000 - $95,500) / ($95,500 - $94,250) = $2,500 / $1,250 = 2.0 ✓

  → APROBADA

Varias IAs que se turnan
────────────────────────
El agente no depende de una sola IA. Tiene una lista de servicios disponibles y los va
turnando: el primer análisis lo responde Groq, el siguiente Gemini (Google), el tercero
Nemotron 3 Ultra (en Ollama Cloud), y luego otra vez Groq…
Así se reparte el trabajo y ninguno llega a su límite de uso.

Si al que le toca el turno no responde (está caído, saturado o tarda demasiado), el sistema
le pasa la pregunta al siguiente sin que tú notes nada. Solo verás "No pudimos contactar a
la IA" si fallan todos.

Cada señal guarda qué IA la respondió, con qué modelo y cuánto tardó (por ejemplo
"Gemini · gemini-3.5-flash-lite · 4,1 s"); se ve en el detalle de la señal, en "Consulta a
la IA". El tiempo incluye la espera de los servicios que fallaron antes. Las señales que se
rechazan por régimen o por reglas no llegan a consultar a la IA, así que no lo muestran.

  Servicio    | Variables en .env
  ──────────────────────────────────────────────────
  groq        | GROQ_API_KEY, GROQ_MODEL
  gemini      | GEMINI_API_KEY, GEMINI_MODEL          (Google AI Studio)
  ollama      | OLLAMA_API_KEY, OLLAMA_MODEL          (Ollama Cloud; el más limitado: va de último)

  Configurar en .env:
    LLM_SERVICES=groq,gemini,ollama    (orden del turno)
    GROQ_API_KEY=...
    GEMINI_API_KEY=...
    OLLAMA_API_KEY=...
    LLM_TIMEOUT_SECONDS=60        (cuánto esperar antes de pasar al siguiente)

  Un servicio sin API key simplemente no entra en el turno.

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
3.4 Módulo 7 — Agentes y Señales (Bots & Signals)

Un agente es la pieza que automatiza todo y el punto de entrada de la app. Une un símbolo, una
estrategia, un conjunto de indicadores y una cuenta en una sola unidad que analiza el mercado.

Cómo crear un agente ("Crear agente" en el inicio):

  Paso 1 — ¿Qué quieres operar?
    Eliges el símbolo (por ejemplo BTC/USDT). Solo aparecen los que el sistema puede descargar solo.

  Paso 2 — ¿Cómo opera?
    Eliges la estrategia. Debajo aparecen solo los conjuntos de indicadores que le sirven, con el
    recomendado ya marcado. El timeframe y el riesgo vienen de la estrategia.

  Paso 3 — ¿Con qué dinero?
    Eliges una de tus cuentas; ves su saldo. Si no tienes ninguna, ahí mismo creas una cuenta de
    práctica (paper) con un capital inicial, por ejemplo 10.000 USDT.

  Paso 4 — Revisa y crea
    El sistema propone un nombre ("BTC/USDT · EMA Trend Follower") que puedes cambiar. Eliges
    qué hace el agente cuando la IA aprueba una operación: Manual (por defecto), Con aprobación
    o Automático (ver 3.6). Con "Iniciarlo al crear" marcado, el agente empieza a trabajar de
    inmediato.

Ejemplo con números: cuenta de práctica de 10.000 USDT y estrategia con riesgo de 1 % → cada
operación puede perder como máximo 100 USDT. Si la IA propone entrada en 95.500 y stop loss en
94.250, el tamaño de la posición es 100 / 1.250 = 0,08 BTC.

La página de cada agente:
  - Arriba: nombre (se puede cambiar), estado, modo, botones Iniciar / Pausar / Detener y
    "Analizar ahora".
  - "Preparando datos": aparece mientras se descargan las primeras velas y se calculan los
    indicadores (uno o dos minutos). La página se actualiza sola.
  - Pestañas: Señales, Órdenes (con "Nueva orden"), Posiciones (con las ejecuciones debajo),
    Mercado y Configuración (reglas de la estrategia y qué mide cada indicador).
  - Mercado: las últimas velas del símbolo y timeframe del agente y, en "Indicadores", lo que la
    IA lee de cada vela (RSI, EMA, MACD, régimen…). Puedes elegir cuántas velas ver (50 a 500).
    Mientras el agente está activo, los datos se actualizan solos. "Actualizar datos" los trae
    en ese momento (las últimas 500 velas del exchange y sus indicadores), también con el agente
    detenido; se puede usar hasta 3 veces por minuto.

"Analizar ahora" le pide a la IA que evalúe el mercado en ese momento. El resultado queda guardado
como señal (aprobada o rechazada) y se abre su detalle con los filtros que pasó o no pasó, y
qué IA respondió y cuánto tardó.

Estados de un agente:

  Detenido  → no hace nada (estado inicial)
  Activo    → descarga velas, calcula indicadores y se puede analizar
  Pausado   → conserva sus datos al día; se reanuda con "Reanudar"
  Error     → se detuvo por un fallo interno; hay que detenerlo y volver a iniciarlo

Transiciones válidas:

  Detenido → Activo           (iniciar)
  Activo   → Pausado          (pausar)
  Activo   → Detenido         (detener)
  Pausado  → Activo           (reanudar)
  Pausado  → Detenido         (detener desde pausa)
  Error    → Detenido         (resetear tras error)

Reglas que el sistema hace cumplir al crear un agente:
  - La cuenta tiene que ser tuya y estar activa.
  - El modo del agente es el de la cuenta (paper con paper, live con live).
  - El conjunto de indicadores tiene que calcular todo lo que pide la estrategia.
  - Nunca más del 1 % del capital por operación.

Cada persona solo ve y opera sus propios agentes. El nombre y el modo de ejecución se pueden
cambiar en cualquier momento (el modo, en la pestaña Configuración); el resto de la configuración
no (si quieres otra, crea otro agente).

Señales y cómo se generan:

  1. El agente consulta a la IA (M6) con su contexto:
     símbolo + timeframe + estrategia + cuenta + conjunto de indicadores
  2. La IA aplica el Prompt Maestro (4 fases: régimen → reglas → LLM → R/R)
  3. Si APROBADA → la señal tiene acción BUY o SELL + entry, SL, TP, position_size, rr_ratio
  4. Si RECHAZADA → la señal tiene acción HOLD, approved=False
  5. TODAS las señales se guardan, incluidas las rechazadas (trazabilidad completa)

Cuándo se generan:
  - Agente en modo Manual: solo cuando pulsas "Analizar ahora".
  - Agente en modo Con aprobación o Automático: solas, una por cada vela que cierra (ver 3.6).

¿Cómo se infiere BUY vs SELL?

  entry > stop_loss → BUY  (compra: ganas si el precio sube)
  entry < stop_loss → SELL (venta)

  Ojo: la app opera en spot, sin ventas en corto. Una señal SELL que se ejecuta vende lo que el
  agente tiene comprado (cierra la posición); si no tiene nada, no se ejecuta.

features_hash:

  Cada señal guarda una huella (SHA-256) de los indicadores que usó. Así se puede auditar
  exactamente qué datos vio la IA cuando tomó la decisión.

Páginas de la UI:
  /#/dashboard    → Inicio: todos tus agentes (filtro Todos / Activos / Detenidos) con estado,
                    símbolo, precio, estrategia y última señal
  /#/agents/new   → Asistente para crear un agente
  /#/agents/12    → Detalle del agente 12
  /#/admin/agents → Vista admin: todos los agentes del sistema con filtros de estado y modo

---
3.5 Módulo 8 — Orders & Execution (Órdenes y Ejecución)

Este es el módulo donde el dinero realmente se mueve. Cuando un bot genera una señal aprobada
(BUY o SELL), este módulo ejecuta la orden en el exchange.

¿Qué es una Orden?

  Una orden es la instrucción concreta para comprar o vender:

  Tipo market    → Ejecutar ahora al precio de mercado. Rápida pero sin control del precio.
  Tipo limit     → Ejecutar solo si el precio llega a X. Control de precio pero puede no ejecutarse.
  Tipo stop      → Activar una venta si el precio cae a X (Stop Loss automático).
  Tipo stop_limit → Igual que stop pero con precio límite adicional.

Ciclo de vida de una orden (máquina de estados):

  new → sent → filled         (ejecución completa)
  new → sent → partially_filled → filled  (ejecución parcial, luego completa)
  new → sent → canceled        (cancelada por el usuario)
  new → sent → rejected        (rechazada por el exchange)

¿Qué es un Fill (Ejecución)?

  Un fill es la confirmación de que una orden se ejecutó, total o parcialmente:
  - qty:   cuánto se compró/vendió realmente
  - price: precio real de la ejecución (puede diferir del precio solicitado)
  - fee:   comisión cobrada por el exchange

  Una orden market grande puede tener múltiples fills si se ejecuta en partes.

¿Qué es una Posición?

  Una posición es el estado actual de lo que tienes abierto en un símbolo:
  - qty:          cuánto tienes (ej: 0.08 BTC)
  - avg_price:    precio promedio de compra (Weighted Average Price)
  - realized_pnl: ganancia/pérdida acumulada de operaciones ya cerradas

  Si tienes 0 qty → posición cerrada (flat).

¿Cómo se calcula el avg_price (precio promedio)?

  Cada compra recalcula el precio promedio ponderado (WAP):
  nueva posición: 0.05 BTC @ $95,000
  compra más:     0.03 BTC @ $96,000
  avg_price nuevo = (0.05 × $95,000 + 0.03 × $96,000) / (0.05 + 0.03)
                  = ($4,750 + $2,880) / 0.08
                  = $95,375 por BTC

Paper mode vs Live mode:

  Cada bot opera en uno de dos modos:

  paper (simulado):
    · El fill se simula usando el precio de cierre de la última vela conocida
    · fee = 0 (sin comisión)
    · No se toca dinero real
    · Ideal para validar estrategias antes de arriesgar capital

  live (real):
    · La orden se envía al exchange real vía la librería ccxt
    · El fill contiene el precio y comisión reales del exchange
    · Usa las credenciales cifradas con Fernet almacenadas en la cuenta
    · Viene APAGADO en el servidor: hasta que el administrador lo active, toda orden live se
      rechaza con "Las órdenes en modo live están desactivadas".

  Qué pasa si el exchange no responde: la orden ya quedó guardada antes de enviarla. Si el
  exchange la rechaza, queda como "rechazada" en el historial. Si no llega respuesta (por
  ejemplo, se cae la red), la orden queda "enviada" y la app te pide no reintentarla, para no
  comprar dos veces. En live, el sistema la busca solo en el exchange durante los minutos
  siguientes y pone su estado al día (ver "La app se sincroniza con el exchange" en 3.6).

Regla de oro: siempre correr al menos 3 meses en paper mode antes de pasar a live.
Esto permite acumular 50-100+ operaciones y calcular métricas reales de la estrategia.

Páginas de la UI:
  /#/agents/12    → Pestañas Órdenes y Posiciones del agente 12; "Nueva orden" abre un formulario
                    para crear una orden manual (/#/orders ahora lleva al inicio)
  /#/admin/orders → Vista admin: todas las órdenes del sistema con filtros de lado, estado y tipo

---
3.6 Modos de ejecución: Manual, Con aprobación y Automático (Módulos 7 y 8)
─────────────────────────────────────────────────────────────────────────────
Cada agente tiene un modo que decide qué pasa cuando la IA aprueba una operación. Lo eliges al
crear el agente (paso 4 del asistente) y lo puedes cambiar cuando quieras en la pestaña
Configuración del agente, aunque esté activo.

  Modo             Cuándo analiza                       Qué pasa si la IA aprueba
  ──────────────────────────────────────────────────────────────────────────────────────────
  Manual           Solo cuando pulsas "Analizar ahora"  Nada más: tú decides si creas la orden
  (por defecto)                                         desde la pestaña Órdenes
  Con aprobación   Solo, cada vez que cierra una vela   La señal queda "Por aprobar". Te avisa
                                                        en la app y en Telegram; tú la apruebas
                                                        o la descartas antes de que venza
  Automático       Solo, cada vez que cierra una vela   La orden sale sola, con stop loss y take
                                                        profit automáticos

Cosas que conviene saber de los modos automáticos (Con aprobación y Automático):
  - El agente tiene que estar Activo. Pausado conserva sus datos, pero no busca entradas solo.
  - Analizan la última vela CERRADA, nunca la que todavía se está formando.
  - Una sola señal por vela: aunque pasen varios ciclos, no se repite.
  - Necesitan un timeframe de 15 minutos o más (analizar cada minuto saldría muy caro en IA).
  - Si las velas vienen atrasadas (más de dos velas sin datos), el agente no decide con datos
    viejos: espera.
  - Hay un tope de análisis automáticos por persona y día (96 por defecto), por el costo de la IA.
  - Automático con dinero real (cuenta live) viene apagado: solo funciona si el administrador lo
    habilita. Al elegir Automático, la app siempre te pide confirmar.

Cómo aprobar una señal
  1. Cuando la IA aprueba una operación de un agente Con aprobación, la señal aparece en la
     tarjeta "Señales por aprobar" del inicio y en la pestaña Señales del agente (columna
     Ejecución: "Por aprobar"). Si conectaste Telegram, también te llega un mensaje.
  2. Abre la señal: ves entrada, stop loss, take profit, riesgo/beneficio y cuánto falta para que
     venza ("Vence en 45 min"). Por defecto tienes 60 minutos; puedes cambiarlo en el campo
     "Minutos para aprobar" (ver abajo).
  3. Pulsa Aprobar o Descartar (los mismos botones en la app y en Telegram). En una cuenta live
     la app te pide confirmar otra vez.
  4. Si nadie decide a tiempo, la señal queda "Vencida" y no se ejecuta nunca tarde.
  5. Si apruebas desde la app y desde Telegram a la vez, solo cuenta la primera decisión.

Qué revisa el sistema justo al aprobar (ejemplo con números)
  Entre que se genera la señal y la apruebas puede pasar un rato y el precio se mueve. Por eso,
  al aprobar, el sistema vuelve a hacer las cuentas con el último precio conocido (el cierre de
  la última vela):

  Señal original:   entrada $100 · stop loss $95 · take profit $115
  Cuenta:           $1.000 → riesgo 1 % = $10 por operación
  Tamaño original:  $10 / ($100 − $95) = $10 / $5 = 2 unidades
  Riesgo/beneficio: ($115 − $100) / ($100 − $95) = 15 / 5 = 3:1

  Caso A — al aprobar el precio está en $101:
    Nuevo tamaño:      $10 / ($101 − $95) = $10 / $6 ≈ 1,67 unidades
                       (compra un poco menos para que el riesgo siga siendo $10)
    Riesgo/beneficio:  ($115 − $101) / ($101 − $95) = 14 / 6 ≈ 2,33:1  → cumple el 2:1
    Resultado:         la orden se envía con 1,67 unidades

  Caso B — al aprobar el precio ya está en $112:
    Riesgo/beneficio:  ($115 − $112) / ($112 − $95) = 3 / 17 ≈ 0,18:1  → no cumple el 2:1
    Resultado:         NO se ejecuta. La señal queda "No ejecutada" y su detalle dice "Por qué
                       no se ejecutó": el precio se movió y la operación ya no cumple el
                       riesgo/beneficio mínimo de 2:1.

  Tampoco se ejecuta si el precio ya está por debajo del stop loss o por encima del take profit,
  ni si el agente ya tiene una posición abierta (no se suman compras sobre compras).

Cuánto tiempo tienes para aprobar ("Minutos para aprobar")
  1. Abre el agente y ve a la pestaña Configuración.
  2. Con el modo Con aprobación elegido, aparece el campo "Minutos para aprobar".
  3. Escribe un número entero entre 1 y 1.440 (24 horas) y pulsa Guardar.
  4. Si lo dejas vacío y guardas, el agente vuelve a usar el valor por defecto del servidor
     (60 minutos si el administrador no lo cambió).
  El tiempo cuenta desde que se genera la señal. Si nadie la aprueba ni la descarta antes, la
  señal vence y no se ejecuta.

Conectar Telegram (para aprobar desde el celular)
  1. En el menú de tu usuario (al pie de la barra lateral), elige "Conectar Telegram".
  2. Pulsa "Generar enlace" y luego "Abrir Telegram". El enlace sirve una sola vez y vence en
     10 minutos.
  3. En Telegram, pulsa Iniciar en el chat del bot. El bot te confirma que el chat quedó
     vinculado.
  4. Vuelve a la app y pulsa "Ya lo vinculé". El menú dirá "Telegram conectado".
  Para dejar de recibir mensajes, abre el mismo diálogo y pulsa "Desvincular".
  Si el administrador no ha configurado el bot de Telegram, la app te lo dice al generar el enlace.

  Cada mensaje trae la acción, el símbolo, entrada, stop loss, take profit, riesgo/beneficio,
  tamaño, el agente y la hora límite para decidir (hora de Bogotá), con los botones Aprobar y
  Descartar. Al pulsar uno, el mensaje se actualiza con el resultado.

Las protecciones (se aplican a toda orden: manual, aprobada o automática)
  - Interruptor general: el administrador puede detener el envío de todas las órdenes de golpe.
    Mientras esté apagado no sale ninguna, ni siquiera los cierres por stop loss o take profit
    (en live, el stop loss que ya está puesto en el exchange sí se ejecuta).
  - Live apagado por defecto: hasta que el administrador lo active, solo se ejecutan órdenes
    paper.
  - Máximo por orden: una compra no puede valer más de un tope (por defecto $10.000; cada agente
    puede fijar uno menor). Si lo supera: "La orden supera el valor máximo permitido por
    operación".
  - Pérdida máxima del agente: si el agente tiene configurado un drawdown máximo y lo alcanza,
    pasa a estado Error y deja de abrir operaciones hasta que lo revises.
  - Las ventas para cerrar o reducir una posición no se frenan por el máximo por orden ni por
    la pérdida máxima: reducir riesgo siempre se puede.
  - Stop loss y take profit automáticos: cuando la posición la abre una señal, se cierra sola
    al tocar uno de los dos niveles, aunque el agente esté pausado o detenido. En Posiciones
    verás "Protección automática: SL … · TP …". Cómo funciona depende del modo:
      · Live: el stop loss queda puesto en el exchange como una orden de venta que se activa
        sola al llegar al nivel. Protege aunque la app o el servidor estén apagados. En
        Posiciones verás además "El stop loss está como orden en el exchange.". El take profit
        no queda en el exchange: el sistema revisa el precio cada minuto y vende cuando la vela
        lo toca.
      · Paper: el sistema revisa los dos niveles cada minuto. Si una misma vela toca los dos, se
        asume lo peor (el stop loss).
    Si el exchange no admite el stop loss como orden, la posición sigue protegida igual que en
    paper: el sistema revisa el stop loss cada minuto.
  - Para no vender dos veces: antes de cualquier otra venta de esa posición (el take profit, una
    venta manual o una señal de venta) el sistema retira el stop loss del exchange. Si no puede
    retirarlo (por ejemplo, porque ya se ejecutó), no vende y te dice: "El stop loss de esta
    posición está en el exchange y no se pudo cancelar (puede que ya se haya ejecutado). Espera
    unos minutos a que se sincronice."
  - Vencimiento de las señales: una señal por aprobar que nadie decide a tiempo vence y no se
    ejecuta.
  - Una señal = una orden: la misma señal no se puede ejecutar dos veces.
  - Regla del 1 %: la IA recibe el riesgo del agente, nunca más del 1 % del capital.

  Ejemplo con números (live): compras 0,02 BTC a $60.000 con stop loss en $58.800 y take profit
  en $62.400 (riesgo $24, beneficio $48: 2:1).
    · Si el precio cae a $58.800, el exchange vende los 0,02 BTC él solo, aunque el servidor de
      la app esté apagado. Cuando la app vuelve, registra la venta y la posición queda cerrada.
    · Si el precio sube a $62.400, en el siguiente minuto la app retira el stop loss del
      exchange y vende a mercado.

  La app se sincroniza con el exchange (solo live)
  Cada minuto la app consulta en el exchange las órdenes live que siguen abiertas y pone al día
  su estado, sin que tengas que hacer nada:
  - Órdenes que se ejecutaron después: por ejemplo, una orden límite que quedó esperando y se
    llenó una hora más tarde, o el stop loss que disparó el exchange. La app registra la
    ejecución y actualiza la posición.
  - Ejecuciones parciales: si una orden se llena por partes, la app suma solo lo nuevo, sin
    contar dos veces lo que ya tenía. Si el resto se cancela o vence en el exchange, la orden
    queda cancelada con lo que sí se ejecutó.
  - Órdenes que nunca llegaron: si al enviar una orden no hubo respuesta y, 10 minutos después,
    el exchange no la conoce, la app la marca rechazada con el motivo "La orden no llegó al
    exchange." (si el agente tiene una regla de alerta de tipo error, te avisa).
  Revisa las órdenes de la última semana. Si falla la red, lo intenta otra vez al minuto
  siguiente.

  Probar en una testnet antes de usar dinero real
  Una testnet es una copia del exchange con dinero de juguete: el exchange trata las órdenes
  como reales, pero no se mueve dinero de verdad. Sirve para comprobar que todo el circuito live
  funciona (compra, stop loss en el exchange, take profit, sincronización) antes de arriesgar
  capital.
  1. Crea una cuenta en la testnet del exchange (por ejemplo, la testnet de spot de Binance) y
     genera allí una API key y su secret. Las claves de la testnet no sirven en el exchange
     real, ni las reales en la testnet.
  2. El administrador pone LIVE_USE_SANDBOX=true y activa live (TRADING_LIVE_ENABLED=true) en
     el servidor. Ojo: mientras LIVE_USE_SANDBOX esté en true, todas las cuentas live van a la
     testnet.
  3. En Mis cuentas, crea una cuenta live del mismo exchange con las claves de la testnet.
  4. Crea un agente con esa cuenta y opera como siempre. Revisa en la testnet que aparezca el
     stop loss como orden y que la app registre lo que pase.
  5. Para pasar a dinero real, el administrador vuelve a poner LIVE_USE_SANDBOX=false y tú usas
     una cuenta con las claves reales.
  No todos los exchanges tienen testnet: si el que eliges no la tiene, la orden queda
  rechazada.

  Límites que hay que conocer:
  - El take profit (y, en paper, también el stop loss) se revisa una vez por minuto: no es una
    orden puesta en el exchange. En un movimiento brusco el cierre puede quedar más lejos del
    nivel, y si el servidor está apagado nadie lo vigila. En live, el stop loss sí sigue en el
    exchange.
  - Si en live compras a mano más cantidad sobre una posición protegida, el stop loss del
    exchange cubre solo la cantidad que había cuando se puso.
  - En paper, el cierre por stop loss o take profit se simula al precio de cierre de la última
    vela, no al precio exacto del nivel.

Nota de seguridad
  - Cada persona solo puede ver y operar sus propios agentes, órdenes y posiciones.
  - Quien tenga tu celular con Telegram abierto puede aprobar tus señales: si lo pierdes,
    desvincula Telegram desde la app.
  - Empieza siempre en paper. Usa Automático en live solo después de meses de historial paper
    que muestren que la estrategia tiene edge (ver Parte 4). El sistema aplica reglas; no
    garantiza ganancias.

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
PARTE 4.5 — Módulo 9: Alerts (Sistema de Notificaciones)
════════════════════════════════════════════════════════

El sistema opera 24/7 tomando decisiones automáticas. Sin alertas, el trader no sabe
qué está pasando a menos que esté mirando la pantalla constantemente. El Módulo 9
resuelve esto: te avisa automáticamente cuando ocurre algo relevante.

4.5.1 ¿Qué es una regla de alerta?
───────────────────────────────────
Una regla de alerta define QUÉ vigilar y POR DÓNDE notificar:

  Componente    Qué define
  ──────────────────────────────────────────────────────────────────────────────
  rule_type     El tipo de evento a monitorear (precio, señal, P&L, drawdown, error)
  rule_spec     Los parámetros concretos (umbral, símbolo, bot, etc.)
  channels      Los canales de entrega (email, telegram, webhook, desktop)

4.5.2 Tipos de reglas disponibles
───────────────────────────────────
  Tipo       Ejemplo de uso
  ──────────────────────────────────────────────────────────────────────────────
  signal     "Avísame cuando el bot #3 genere una señal BUY"
  price      "Avísame si BTC/USDT cae por debajo de $80,000"
  pnl        "Avísame si el P&L del bot baja del -5% en el día"
  drawdown   "Avísame si el drawdown acumulado supera el 10%"
  error      "Avísame si cualquier bot entra en estado de error"

4.5.3 Canales de entrega
──────────────────────────
El sistema soporta 4 canales simultáneos:

  Canal     Cómo funciona
  ──────────────────────────────────────────────────────────────────────────────
  Email     Envía un correo HTML usando el servidor SMTP configurado
  Telegram  Manda un mensaje al chat de Telegram del sistema (requiere TELEGRAM_BOT_TOKEN).
            Aparte, cada persona puede conectar su propio chat para aprobar señales (ver 3.6).
  Webhook   Hace un HTTP POST a una URL externa (Slack, Discord, IFTTT, etc.). Por seguridad
            la URL tiene que empezar por https:// y apuntar a un servicio público de internet.
  Desktop   Notificación nativa del sistema operativo (macOS, Windows, Linux)

4.5.4 Disparadores automáticos (hooks)
──────────────────────────────────────
Las alertas se disparan automáticamente desde los módulos clave:

  Evento                             Qué evalúa
  ──────────────────────────────────────────────────────────────────────────────
  GenerateSignalService (M7)         Evalúa reglas tipo 'signal' post-señal aprobada
  CreateOrderService (M8)            Evalúa reglas de orden tras cada orden, también si el
                                     exchange la rechazó
  POST /api/alerts/evaluate (manual) Evalúa reglas tipo 'price' para un símbolo

El despacho es fire-and-forget: si falla una alerta, NO se cancela la señal u orden.
Las alertas son informativas — nunca bloquean el flujo de trading.

4.5.5 Historial de eventos
───────────────────────────
Cada vez que se dispara una regla, se crea un AlertEvent con:
  - título y mensaje descriptivo
  - severidad (info / warning / critical)
  - estado de entrega (pending / sent / failed)
  - el payload completo del contexto (signal_id, precio, etc.)

Esto crea un log de auditoría de todas las notificaciones enviadas.

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
     - (Pendiente, todavía no implementado: enviar el estado de cuenta por correo al inversor)
  5. El inversor puede ver su dashboard: capital, rendimiento, historial de fees

  Hoy el cierre del período lo hace el administrador a mano desde /#/admin/billing, escribiendo
  el capital final (closing_equity); el sistema no lo calcula solo ni envía ningún correo.

5.4 Roles del sistema (con M10)
─────────────────────────────────
  role_id=1 → Usuario      (trader, accede a sus cuentas y bots)
  role_id=2 → Administrador (gestiona todo: inversores, fees, estrategias)
  role_id=3 → Inversor      (además ve "Mi inversión": su propio dashboard de rendimiento en /#/investor/dashboard)

5.5 ¿Qué necesitas para lanzar esto?
──────────────────────────────────────
  Requisito técnico:   Módulos 7 y 8 funcionando (bots operando en live)
  Requisito legal:     Un contrato simple con el inversor que especifique el % de fee,
                       el período de cobro y las condiciones de retiro
  Requisito de confianza: 3-6 meses de historial paper verificable antes de pedirle
                          dinero real a alguien

La plataforma hace el cálculo automático y transparente — el inversor puede ver
cada operación que ejecutó el bot con su capital.
