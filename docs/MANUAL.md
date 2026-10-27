# El sistema completo — Trading App

## ¿Qué hace este sistema en una frase?

Observa el mercado, calcula indicadores, consulta a una IA, y si la operación vale la pena, compra o vende automáticamente.

**Horas:** el sistema guarda todo en hora universal (UTC), pero en la app, en Telegram y en el extracto del fondo verás siempre la **hora de Colombia** (UTC-5), estés donde estés. Una vela que cierra a las 15:00 UTC aparece como 10:00 a. m.

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

Es la bolsa donde se compran y venden activos. La plataforma trabaja con uno solo: **Binance**.
Ahí está la billetera con el dinero de todos y ahí se operan todos sus mercados: criptomonedas,
metales, materias primas, ETFs y acciones.

---
1.3 ¿Qué es un Symbol (par)?

Es lo que se negocia: BTC/USDT significa "compro Bitcoin pagando con USDT (dólar digital)". Todos
los symbols son de Binance: los precios que lee la app y las órdenes que envía salen del mismo
mercado, así que la entrada, el stop loss y el take profit se calculan con los precios del lugar
donde de verdad se compra.

1.3.1 ¿Qué mercados puedo operar? (cripto, metales, materias primas, acciones)

Además de cripto, la app trae **perpetuos TradFi** de Binance. Un perpetuo es un contrato
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

Con dinero real (live), un perpetuo se opera así:
  - Solo comprando: el agente compra y luego vende para cerrar. No apuesta a la baja (no abre
    "cortos").
  - Sin apalancamiento (1x) y con margen aislado: la posición nunca vale más que el dinero que
    pones, y una pérdida no toca el resto de la billetera.
  - Desde la billetera de Futuros de Binance (es distinta de la de Spot). Un super admin pasa a
    mano los USDT de Spot a Futuros; si no hay margen suficiente, la compra se rechaza con un
    aviso.
  - Un solo agente live por perpetuo: Binance junta en una sola posición todo lo que se opera en
    ese símbolo.
  - El funding: cada pocas horas Binance cobra o paga un pequeño monto a quien tiene la posición
    abierta (es lo que mantiene el precio del contrato pegado al del activo real). La app lo
    registra y lo suma al resultado del agente; lo ves en Rendimiento y en la liquidación del
    fondo.

  Ejemplo: un agente con 2.000 USDT compra oro (XAU) a 2.500 con stop loss en 2.450. La regla del
  1 % pide arriesgar 20 USDT: 20 ÷ 50 = 0,4 onzas (1.000 USDT de posición). Si el stop estuviera a
  5 USDT, la regla pediría 4 onzas (10.000 USDT): como sin apalancamiento no se puede pasar del
  capital, la app compra 0,8 onzas (2.000 USDT) y el riesgo real baja a 4 USDT (0,2 %).

Para que funcione en Binance (super admin): API key con permiso de Futuros (sin retiro ni
transferencias), el acuerdo de los perpetuos TradFi aceptado en la app de Binance y el modo de
posición "unidireccional" (One-way) en las preferencias de Futuros.

Forex (EUR/USD, USD/JPY) y los índices "de verdad" no están conectados: necesitan otro proveedor
de datos y un bróker. Ojo con `SPX/USDT:USDT` en Binance: no es el S&P 500, es una memecoin.

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

Agente = Nombre + Símbolo + Estrategia + Conjunto de indicadores + Dinero

El timeframe y el riesgo por operación los pone la estrategia. El dinero depende del tipo de agente:
  - Agente real: opera con la billetera de Binance, con lo que se le asigna desde el fondo.
  - Agente demo: opera con dinero simulado; al crearlo solo escribes cuánto quieres invertir.
Los dos tipos conviven: los reales se ven en el Inicio y los demo en "Agentes demo".

Ejemplo: el agente demo "BTC/USDT · EMA Trend Follower" vigila BTC/USDT en velas de 1h con la
estrategia EMA Trend Follower y el conjunto Tendencia, con 10.000 USDT simulados y arriesgando como
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

1.14 ¿Cómo se mide si un agente funciona?

La pestaña "Rendimiento" de cada agente cuenta sus operaciones cerradas: una operación va desde
que compra hasta que vuelve a quedar sin posición.

- % de operaciones ganadoras (win rate): 6 de 10 ganadoras = 60 %.
- R/R real: ganancia media / pérdida media. Si ganas en promedio $200 y pierdes $100, es 2 : 1,
  el mínimo que pide el sistema.
- Profit factor: todo lo ganado / todo lo perdido. $1.000 ganados y $500 perdidos = 2. Mayor
  que 1 = la estrategia gana más de lo que pierde.
- Caída máxima (drawdown): la peor racha. Si el resultado acumulado llegó a +$300 y bajó a
  −$100, la caída fue de $400.

"Track record" (menú Explorar) muestra lo mismo por estrategia, sumando todos los agentes que la
usan. Allí todo va en % de retorno, para que una cuenta grande no pese más que una pequeña, y no
se ve de quién es cada agente.

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
Las cuentas las crea un administrador (Configuración → Usuarios → "Invitar usuario"): llega un
correo de bienvenida y se entra con el correo y un código de un solo uso; no hay contraseñas.

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

Por seguridad solo hay una sesión abierta por persona: si entras desde otro navegador o
dispositivo, la sesión anterior se cierra. Esa otra pantalla muestra "Tu sesión se cerró" con
el motivo (iniciaste sesión en otro lugar) y te lleva al login. Si ya tienes una sesión abierta
cuando pides el código, el correo te lo avisa: si no fuiste tú, ignóralo.

En el menú de usuario (abajo en la barra lateral), "Mi perfil" cambia el nombre que se muestra.
El correo y el rol no se cambian desde ahí: el rol lo asigna un administrador, y si te lo cambia,
el menú se actualiza solo en unos minutos.

Arriba a la derecha está la campana de notificaciones: muestra lo último que avisaron tus
alertas y cuántas no has visto. Al abrirla quedan como vistas en tu cuenta, así que el
contador también se limpia en tus otros dispositivos.

Todo se navega desde el menú lateral: Inicio, Operar (mis agentes, alertas, mis cuentas),
Explorar (explorar mercados, estrategias, track record) y, según tu rol, "Mi inversión" (inversores)
o "Administración" (administradores). Las señales, órdenes y alertas de un agente se revisan
dentro del propio agente, así que no hay listas aparte "de todo el sistema". Para abrir un agente
que no es tuyo, entra a Administración → Fondo → "Agentes del fondo". "Configuración"
reúne lo que el administrador define para todos: los usuarios (y su rol) y el canal de Telegram.
Las estrategias se crean y editan en la misma página de Explorar → Estrategias: el administrador
ve ahí los botones "Nueva estrategia" y "Editar"; el resto solo las consulta. En "Usuarios" se cambia el rol de cada persona (Usuario, Administrador o
Inversor); nadie puede cambiar el suyo, para que la app nunca se quede sin administrador.

También desde "Usuarios" se bloquea o desactiva una cuenta. Bloquear es una suspensión temporal
(por ejemplo, si ves actividad sospechosa); desactivar es para una cuenta que ya no se usa. En los
dos casos la persona sale de la app al instante y no puede volver a entrar, y sus agentes activos
quedan en pausa: no abren operaciones nuevas, pero sus posiciones abiertas siguen protegidas con
su stop loss y take profit. Si reactivas la cuenta, los agentes siguen en pausa hasta que la
persona los reanude. Nadie puede bloquearse a sí mismo.

"Auditoría" (Configuración) muestra cada petición que llegó a la app: quién la hizo, cuándo, qué
ruta, si fue una consulta o un cambio y si falló. Sirve para responder preguntas como "¿quién
cambió este rol?" o "¿quién intentó entrar con este correo?". Se filtra por persona, tipo de
evento, fechas, ruta o solo errores; nunca muestra contraseñas, códigos ni claves.

Las listas grandes (el historial de alertas y las pestañas Señales y Órdenes de un agente) se
cargan por páginas: abren rápido aunque haya miles de registros.

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

3.0.2 Módulo 4 — La billetera de la plataforma (fondo común)
──────────────────────────────────────────────────────────────
Toda la plataforma usa UNA sola cuenta de Binance para guardar el dinero
de todos: propietarios, socios e inversores. Esa cuenta es la "billetera".

Dónde se ve: Administración → Fondo → Billetera (solo super admin y socios; un inversor nunca ve
el saldo total).

Qué muestra:
  Saldo total  → todo lo que hay en la billetera, convertido a USDT.
  Saldo libre  → lo que no está ocupado en órdenes abiertas.
  En órdenes   → lo que el exchange tiene bloqueado en órdenes que aún no se ejecutan.
  Activos      → cuánto hay de cada moneda (USDT, BTC…) y cuánto vale en USDT.
  Historial    → las lecturas anteriores del saldo.

Cómo se lee el saldo: la app le pregunta al exchange cada 5 minutos. Suma también la wallet
Funding de Binance, que es donde suelen caer el P2P y los depósitos, y la de Futuros, donde está
el margen de los agentes que operan perpetuos (oro, acciones…). Si una moneda no
tiene precio en USDT, se muestra pero no suma al total, y la página lo avisa.

Solo hay una billetera, la de Binance: nadie la crea ni la elige en la app.

Para empezar (quien administra el servidor):
  1. En Binance, crea una API key con permiso de lectura y de trading, NUNCA de retiro (los
     retiros se hacen a mano desde Binance).
  2. Ponla en el archivo .env del servidor (BINANCE_API_KEY y BINANCE_API_SECRET) y reinicia la
     API. Mientras falte, la página Billetera dice "La billetera de Binance aún no está conectada".
  3. En Billetera, pulsa "Sincronizar ahora" para ver el saldo de inmediato.

  Ejemplo: la billetera tiene 1.000 USDT libres, 200 USDT en una orden y 0,01 BTC a 60.000.
  Saldo total = 1.000 + 200 + 600 = 1.800 USDT · Saldo libre = 1.600 · En órdenes = 200.

3.0.3 Módulo 11 — El fondo común: tu saldo y los depósitos
─────────────────────────────────────────────────────────────
Cada persona (propietario, socio o inversor) tiene su cuenta dentro del fondo. Cada movimiento
queda escrito en un "libro" que nunca se edita: si algo se corrige, se agrega otro movimiento.

Tus saldos (Mi inversión → Mi saldo):
  Pendiente de asignar → dinero que depositaste y ya se confirmó, pero aún no está en un agente.
                         No se puede retirar: primero tiene que pasar por un agente.
  Disponible           → dinero que ya pasó por un agente (o comisiones). Este sí se retira.

Cómo depositar:
  1. En Mi saldo verás la red (p. ej. TRC20) y la dirección de la billetera. Cópiala con el botón.
  2. Desde TU PROPIA billetera (Binance u otra), envía USDT a esa dirección POR ESA MISMA RED (y
     con el memo, si la red lo pide). La plataforma no recibe transferencias bancarias: el dinero
     entra solo de billetera a billetera.
  3. Copia el ID de la transacción (TxID, a veces llamado hash) y pulsa "Registrar depósito" con
     el monto enviado. Si enviaste desde Binance a Binance, el ID es un número ("Internal
     transfer 513…"): pégalo tal cual.
  4. La app busca ese txid en el exchange cada pocos minutos. Si llegó el mismo monto y es de
     hasta 1.000 USDT, se confirma solo. Si el monto no coincide, si es mayor o si el exchange lo
     marcó fallido, queda "En revisión" y un super admin decide.
  5. Si en 72 horas el txid no aparece, la solicitud vence.

  Ejemplo: envías 500 USDT por TRC20 y registras el txid. A los pocos minutos el exchange lo
  muestra con 500 USDT → se confirma solo y tu "Pendiente de asignar" sube a 500.

  Se acredita lo que diga el exchange: si declaras 500 pero llegaron 480, queda en revisión.
  Un mismo txid no se puede registrar dos veces.

Para los super admin (Administración → Fondo):
  Depósitos      → confirmar (con nota si el exchange no lo respalda) o rechazar (con motivo);
                   pestaña "Sin reclamar": dinero que llegó sin que nadie lo registrara, para
                   asignárselo a su dueño.
  Participantes  → cuánto tiene cada persona, sus movimientos y "Devolver" (solo saldo pendiente,
                   casos excepcionales; el dinero se envía por fuera).
  Ajustes        → redes de depósito (en una billetera real la dirección se lee del exchange) y
                   reglas: permanencia mínima, tope de confirmación automática y vencimiento.
  Los socios ven todo esto sin poder cambiarlo, pero sí pueden depositar su propio dinero.

3.0.4 Módulo 11 — Los agentes del fondo: cómo trabaja tu dinero
─────────────────────────────────────────────────────────────────
El dinero del fondo no opera todo junto: cada agente tiene su propia "bolsa". Lo que tienes en un
agente se mide en UNIDADES, como las participaciones de un fondo de inversión.

  Valor de una unidad (NAV) = saldo del agente ÷ unidades que existen.
  La primera vez vale 1 USDT. Si el agente gana, cada unidad vale más; si pierde, vale menos.

Cómo entra tu dinero a un agente:
  1. Un super admin "pone en cola" parte de tu saldo pendiente para un agente.
  2. El dinero entra en la próxima LIQUIDACIÓN del agente. La liquidación se hace con el agente en
     pausa y sin operaciones abiertas, para que su saldo sea exacto (no un estimado).
  3. Con tu dinero se compran unidades al valor de ese momento.

  Ejemplo: el agente tiene 1.500 USDT y 1.500 unidades (cada una vale 1). Gana 300 → tiene 1.800
  y cada unidad vale 1,20. Tú entras con 600 USDT → recibes 500 unidades (600 ÷ 1,20).
  Así no te quedas con la ganancia que hicieron los demás antes de que entraras, ni ellos con la tuya.

Dónde lo ves: Mi saldo → "En agentes" y la pestaña "Mis agentes": cuánto aportaste, cuánto vale
hoy (según la última liquidación) y el resultado.

La regla del 1 % en un agente del fondo se calcula sobre el dinero de ESE agente, no sobre toda la
billetera. Un agente de la billetera que no está en el fondo no opera.

3.0.5 Módulo 11 — Sacar dinero, la comisión y los retiros
───────────────────────────────────────────────────────────
Retirar tu dinero tiene dos pasos: primero sale del agente y queda "Disponible"; después pides que
te lo envíen a tu billetera.

Paso 1 — Sacar dinero de un agente (Mi saldo → Mis agentes → "Sacar dinero"):
  - Eliges un monto o "Sacar todo". La salida queda EN COLA y se aplica en la próxima liquidación
    del agente, al valor de la unidad de ese momento.
  - Solo sale el dinero que lleva al menos la PERMANENCIA MÍNIMA en el agente (p. ej. 30 días). Sale
    primero lo más antiguo. Si una parte todavía no cumple, sale lo que cumple y el resto se queda
    en el agente; lo verás como "aún sin la permanencia mínima".
  - Sobre la GANANCIA de lo que sale se cobra la comisión. Lo que queda (valor − comisión) pasa a tu
    saldo Disponible.
  - Mientras está en cola puedes anularla.

La comisión es escalonada, como los impuestos:
  Cada tramo de ganancia paga su propio %, y solo sobre la parte que cae en ese tramo. Por eso ganar
  más nunca te deja con menos dinero neto. Si sales con pérdida, no hay comisión. La tabla vigente la
  ves en Mi saldo → Comisión. Los propietarios también la pagan sobre su propio dinero.

  Ejemplo con esta tabla: de 0 % a 50 % de ganancia → 10 %; de 50 % a 100 % → 15 %; desde 100 % → 20 %.
  Pusiste 1.000 USDT y al salir valen 3.000 (ganaste 2.000, un +200 %).
    Primeros 500 de ganancia (hasta +50 %)     × 10 % =  50
    Siguientes 500 (de +50 % a +100 %)         × 15 % =  75
    Los otros 1.000 (más de +100 %)            × 20 % = 200
    Comisión total = 325 USDT (16,25 % de la ganancia) → recibes 2.675 USDT en tu Disponible.

  La comisión se reparte entre los propietarios y los socios según los % acordados (que suman 100 %).
  Con 40 % / 40 % / 20 %, esos 325 se reparten así: 130 + 130 + 65.

Paso 2 — Retirar a tu billetera (Mi saldo → "Retirar"):
  No hay transferencias a bancos ni a Nequi: el dinero sale de la billetera de la plataforma en
  Binance a una dirección cripto tuya.
  1. Primero registra tu dirección (pestaña Retiros → "Agregar dirección"): la red (una de las que
     acepta el fondo, p. ej. TRC20), la dirección copiada de tu billetera y el memo si tu billetera
     lo pide. La app revisa que la dirección tenga la forma de esa red. Por seguridad, una dirección
     nueva se puede usar 48 horas después de registrarla.
  2. Pulsa "Retirar", elige la dirección y el monto. Verás la comisión de red de Binance y cuánto
     te llega. Solo puedes retirar lo Disponible; ese dinero queda reservado mientras el retiro
     está por enviar. El monto debe superar el mínimo de retiro de la red.
  3. Un super admin envía el dinero desde Binance y registra el ID de la transacción. La app lo
     busca en Binance y comprueba que salió completo hacia tu dirección y por tu red.
  4. Te llega un aviso con los detalles: cuánto recibes, la comisión de red, la red, tu dirección
     (abreviada), el ID de la transacción y el enlace para verla en el explorador de la red.
  5. Si el retiro se rechaza (con motivo) o lo anulas, el dinero vuelve a estar disponible.

  La comisión de red la pagas tú: Binance la descuenta de lo que se envía.
  Ejemplo: retiras 500 USDT por TRC20 y la comisión de la red es 1 USDT → recibes 499 USDT en tu
  billetera y de tu saldo salen 500.

Para los super admin (Administración → Fondo):
  Retiros      → los "Por enviar": "Registrar envío" muestra la red, la dirección completa, el memo
                 y el monto para copiarlos. Haz el retiro en Binance por ese monto, pega el ID de
                 la transacción y pulsa "Buscar en Binance": la app trae lo enviado y la comisión.
                 Si Binance aún lo procesa, espera a que salga como completado. Si fue a otra
                 dirección o red, no se puede registrar. Si Binance no lo muestra, se registra a
                 mano (recibido y comisión) con una nota. "Rechazar" pide un motivo.
                 La API key de la billetera solo LEE el historial: los retiros los hacen ustedes en
                 Binance (recomendado: lista blanca de direcciones de retiro en Binance).
  Comisiones   → la tabla escalonada (cada cambio es una versión nueva y no cambia lo ya cobrado), el
                 reparto entre propietarios y socios, y cuánto ha recibido cada uno.
  Liquidar     → la vista previa muestra quién sale, su comisión y su neto. Sin tabla de comisión o
                 sin reparto no se puede liquidar un agente que tiene salidas pedidas.

3.0.6 Módulo 11 — El resumen del fondo, los avisos y los comprobantes
───────────────────────────────────────────────────────────────────────
Resumen del fondo (Administración → Fondo → Resumen del fondo; super admin y socios):
  - Cuánto hay en la billetera y cuánto de eso está en cada agente.
  - Cuánto tienen las personas pendiente de asignar y disponible, qué retiros están por enviar y
    qué depósitos esperan una decisión.
  - Lo que ganó cada propietario o socio: comisiones recibidas más la ganancia de su propio
    dinero en los agentes.
  - La CONCILIACIÓN: comprueba que cada peso de la billetera tiene dueño.
      Billetera − capital de los agentes − pendiente − disponible = diferencia
    Lo normal es que dé casi 0 ("Todo cuadra").

  Ejemplo: la billetera tiene 10.050 USDT. Los agentes suman 8.000, el pendiente 1.500 y el
  disponible 500 → 10.000 tienen dueño y sobran 50. Suele ser un depósito que llegó y aún no se
  confirma, o una posición abierta que hoy vale más de lo que costó. Si la diferencia es
  negativa (falta dinero), hay que revisarla antes de enviar retiros.

Mi saldo, para todos:
  - "Lo que has ganado": lo que ya salió de los agentes (después de la comisión), lo que vas
    ganando en los agentes y, si recibes comisión, cuánto llevas.
  - "Descargar extracto (CSV)" en Movimientos: todos tus movimientos en un archivo que abre Excel.
  - En Retiros, cada envío muestra lo que recibiste, la comisión y el ID de la transacción con su
    enlace al explorador; "Comprobante" descarga el soporte si el super admin lo subió.

Comprobantes (opcionales): el ID de la transacción ya es la prueba del envío; aun así, al
registrarlo el super admin puede adjuntar una captura (PDF, PNG o JPG de hasta 5 MB), o hacerlo
después con "Adjuntar comprobante".

Avisos: te llegan a la campana de la app y, si están activos, por correo y por Telegram (a tu
chat, si lo vinculaste):
  - tu depósito se confirmó o se rechazó;
  - tu dinero entró a un agente o salió de él en una liquidación (con la comisión);
  - tu retiro se envió (recibido, comisión de red, red, dirección e ID de la transacción) o se
    rechazó.
  Los super admin reciben además: un depósito necesita revisión y alguien pidió un retiro.

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

3.1.1 Backtesting: probar una estrategia en el pasado

Antes de dejar que un agente opere, puedes ver cómo le habría ido a su estrategia: menú
Explorar → Backtesting (o "Probar en el pasado" en el detalle de una estrategia).

  1. Elige la estrategia, el símbolo, el timeframe y cuánta historia (500 a 3.000 velas).
  2. La app trae esa historia del exchange (no la guarda), calcula los indicadores y recorre
     las velas: cuando una cumple el régimen y todas las reglas, "compra" al abrir la
     siguiente, con stop loss a 1,5 × ATR y take profit a 3 × ATR (2:1), arriesgando el 1 %.
  3. Ves el resultado contra "comprar y mantener", el % de operaciones ganadoras, el R/R real,
     el profit factor, la caída máxima y cada operación simulada.

  Ejemplo: con 10.000 USDT, una entrada a 100 con ATR 10 pone el SL en 85 y el TP en 130. El
  riesgo es 100 USDT (1 %), así que compra 100 / 15 = 6,67 unidades. Si llega al TP gana
  6,67 × 30 = 200 USDT (2 : 1).

  Es una prueba SIN la IA: mide si las reglas tienen ventaja, no lo que decidiría el agente.
  Con menos de 30 operaciones el resultado puede ser suerte, y un buen pasado no garantiza el
  futuro: lo recomendado sigue siendo probar en paper antes de pasar a live.

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
estrategia, un conjunto de indicadores y su dinero en una sola unidad que analiza el mercado.

Hay dos tipos de agente, y conviven a la par:
  - Agentes reales (menú Inicio): operan con la billetera de Binance. Su dinero es el que les
    asignas desde Administración → Fondo → Agentes del fondo; sin asignación no generan señales.
  - Agentes demo (menú "Agentes demo"): operan con dinero simulado. Solo escribes cuánto quieres
    invertir; no sale de ninguna billetera ni del fondo. Sirven para ver cómo le iría a una
    estrategia antes de ponerle dinero real.
Un agente demo no se puede convertir en real ni al revés: si una estrategia funciona en demo, se
crea un agente real nuevo con ella.

Cómo crear un agente ("Crear agente real" en el inicio o "Crear agente demo" en Agentes demo):

  Paso 1 — ¿Qué quieres operar?
    Eliges el símbolo (por ejemplo BTC/USDT). Solo aparecen los que el sistema puede descargar solo.

  Paso 2 — ¿Cómo opera?
    Eliges la estrategia. Debajo aparecen solo los conjuntos de indicadores que le sirven, con el
    recomendado ya marcado. El timeframe y el riesgo vienen de la estrategia.

  Paso 3 — ¿Con qué dinero?
    Agente real: se explica que opera con la billetera de Binance (y, si el símbolo es un
    perpetuo, que usa la billetera de Futuros). Agente demo: escribes el monto a invertir, por
    ejemplo 10.000 USDT, y ves cuánto arriesgaría cada operación con la regla del 1 %.

  Paso 4 — Revisa y crea
    El sistema propone un nombre ("BTC/USDT · EMA Trend Follower") que puedes cambiar. Eliges
    qué hace el agente cuando la IA aprueba una operación: Manual (por defecto), Con aprobación
    o Automático (ver 3.6). Con "Iniciarlo al crear" marcado, el agente empieza a trabajar de
    inmediato.

Ejemplo con números: agente demo con 10.000 USDT y estrategia con riesgo de 1 % → cada
operación puede perder como máximo 100 USDT. Si la IA propone entrada en 95.500 y stop loss en
94.250, el tamaño de la posición es 100 / 1.250 = 0,08 BTC.

La página de cada agente:
  - Arriba: nombre (se puede cambiar), estado, modo, botones Iniciar / Pausar / Detener y
    "Analizar ahora".
  - "Preparando datos": aparece mientras se descargan las primeras velas y se calculan los
    indicadores (uno o dos minutos). La página se actualiza sola.
  - Pestañas: Señales, Órdenes (con "Nueva orden"), Posiciones (con las ejecuciones debajo),
    Mercado y Configuración (reglas de la estrategia y qué mide cada indicador).
  - Nueva orden: en una compra a mercado puedes poner stop loss y take profit; la app cierra la
    posición sola si el precio llega a alguno (en live, el stop loss queda en el exchange). Con
    los dos, el take profit debe estar al menos el doble de lejos que el stop loss, la misma
    regla 2:1 que usa la IA. Ejemplo: compras a 100 con SL 95 → el TP debe ser 110 o más.
  - Las órdenes live que siguen abiertas (una límite que no se ha ejecutado, por ejemplo) se
    pueden cancelar con "Cancelar". Lo que ya se ejecutó se mantiene.
  - Mercado: un gráfico del precio de cierre (con líneas de la entrada, el stop loss y el take
    profit si hay una posición abierta; pasa el cursor o usa las flechas para ver cada vela), las
    últimas velas del símbolo y timeframe del agente y, en "Indicadores", lo que la
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
  - Un agente demo necesita un monto mayor que 0; un agente real no lleva monto.
  - El tipo (real o demo) no se cambia después.
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

Compartir las señales de un agente (y seguir las de otros)
  - El dueño de un agente puede activar "Compartir señales" en su pestaña Configuración.
  - En Track record aparece la lista de agentes que comparten. Con Telegram conectado, pulsa
    "Suscribirme" y recibirás sus compras y ventas aprobadas: acción, símbolo, entrada, SL, TP
    y R/R. Es solo información: no se ejecuta nada en tu cuenta y no se ve de quién es el
    agente ni cuánto dinero maneja. "Dejar de seguir" lo detiene.

Las protecciones (se aplican a toda orden: manual, aprobada o automática)
  - Interruptor general: el administrador puede detener el envío de todas las órdenes de golpe.
    Mientras esté apagado no sale ninguna, ni siquiera los cierres por stop loss o take profit
    (en live, el stop loss que ya está puesto en el exchange sí se ejecuta).
  - No hay un interruptor aparte para lo real: los agentes reales y los demo funcionan a la
    vez. El único freno general es el interruptor de arriba, que detiene a todos.
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
  1. Crea una cuenta en la testnet de Binance (la de spot) y
     genera allí una API key y su secret. Las claves de la testnet no sirven en el exchange
     real, ni las reales en la testnet.
  2. El administrador pone LIVE_USE_SANDBOX=true y las claves de la testnet en BINANCE_API_KEY y
     BINANCE_API_SECRET del servidor. Ojo: mientras LIVE_USE_SANDBOX esté en true, todos los
     agentes reales van a la testnet.
  3. Crea un agente real y opera como siempre. Revisa en la testnet que aparezca el stop loss
     como orden y que la app registre lo que pase.
  4. Para pasar a dinero real, el administrador vuelve a poner LIVE_USE_SANDBOX=false y cambia
     las claves por las reales.


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
  Telegram  Manda el aviso a TU chat de Telegram si lo conectaste (menú de usuario → Conectar
            Telegram); si no, al chat del sistema. El mismo chat sirve para aprobar señales (ver 3.6).
  (Email)   El correo llega a la dirección con la que entras a la app.
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
  Cada ciclo del scheduler (~1 min)  Revisa solas las reglas de precio, P&L y drawdown
  POST /api/alerts/evaluate (manual) Lo mismo para las reglas de precio de un símbolo

El despacho es fire-and-forget: si falla una alerta, NO se cancela la señal u orden.
Las alertas son informativas — nunca bloquean el flujo de trading.

4.5.5 Historial de eventos
───────────────────────────
Cada vez que se dispara una regla, se crea un AlertEvent con:
  - título y mensaje descriptivo
  - severidad (info / warning / critical)
  - estado de entrega (pending / sent / failed)
  - el payload completo del contexto (signal_id, precio, etc.)

Esto crea un log de auditoría de todas las notificaciones enviadas. Además, cada aviso aparece
en la campana de la cabecera de la app (ver 3.0).

4.5.6 ¿Cómo se calculan el P&L y el drawdown de una alerta?
─────────────────────────────────────────────────────────────
Las reglas de P&L y drawdown siempre van atadas a un agente, y se miden en % de lo que ese agente
llegó a tener invertido en una sola operación (no la suma de todas, que diluiría el %).

  - P&L total: lo ganado o perdido en operaciones cerradas + lo que va ganando o perdiendo la
    abierta al último precio.
  - P&L del día: el P&L total ahora menos el que había a las 00:00 (hora de Colombia).
  - Drawdown: cuánto cayó el P&L desde su mejor momento. Si se recupera, baja; por eso no te
    sigue avisando cuando ya pasó.

Umbral negativo en P&L ("−5 %") avisa si se pierde eso o más; umbral positivo ("+5 %") avisa
si se gana eso o más.

Ejemplo: el agente cerró una operación con +40 (invirtió 1.000) y otra con −20 (invirtió 800), y
tiene abierta una de 0,01 BTC comprada a 60.000 que hoy vale 57.000 (−30).
  P&L total = 40 − 20 − 30 = −10 → −1 % de 1.000.
  Su mejor momento fue +40 → drawdown = 40 − (−10) = 50 → 5 %. Una regla de drawdown de 5 % avisa.

Para no llenarte de mensajes, una regla que ya avisó espera 60 minutos antes de volver a revisarse
(ALERT_REPEAT_MINUTES). Si la condición sigue, te lo recuerda cada hora.

---
PARTE 5 — El modelo de negocio: el fondo común

5.1 De las cuentas administradas al fondo común
─────────────────────────────────────────────────
  Antes cada inversor tenía su propia "cuenta administrada" y la comisión se calculaba con una
  marca de agua por cuenta (Módulo 10). Desde el 2026-10-23 eso se retiró: ahora todo el dinero
  está en UNA billetera y el Módulo 11 (Fondo común, sección 3.0.3 a 3.0.6) lleva la cuenta de
  cada persona.

  Lo que se mantiene de la idea original:
  - Si el agente no gana, no hay comisión.
  - Recuperar una pérdida no se cobra dos veces: la comisión se calcula sobre lo que costó cada
    parte de tu dinero, igual que una marca de agua.
  - Todo queda escrito y la persona lo ve: sus movimientos, lo que salió de cada agente y la
    comisión tramo por tramo.

5.4 Roles del sistema (fondo común)
─────────────────────────────────────
  Super admin → los propietarios de la plataforma (Andrés y Dayron). Crean y operan los
                agentes, invitan personas y configuran todo. No se puede dar este rol
                desde la app.
  Socio       → ve todo lo que ve un super admin (agentes, cuentas, órdenes, el fondo,
                auditoría), pero no puede crear, editar, pausar ni aprobar nada. Se invita
                desde Configuración → Usuarios.
  Inversor    → ve lo suyo en "Mi saldo": sus saldos, sus agentes, lo que ha ganado, sus
                retiros y la tabla de comisión. Nunca ve el total de la billetera.

  Ejemplo: un socio abre un agente y ve sus señales y órdenes, pero no aparecen los botones
  Iniciar, Pausar, Analizar ahora ni Nueva orden. Si intentara la acción por otro medio, la
  API le responde "Como socio puedes revisar todo, pero no hacer cambios".

5.5 ¿Qué necesitas para lanzar esto?
──────────────────────────────────────
  Requisito técnico:   Módulos 7 y 8 funcionando (bots operando en live)
  Requisito legal:     Administrar dinero de terceros con comisión es actividad regulada
                       (en Colombia, la SFC): validarlo con un abogado antes de recibir
                       dinero real. Un contrato con la tabla de comisión, la permanencia
                       mínima y cómo se piden los retiros
  Requisito de confianza: 3-6 meses de historial paper verificable antes de pedirle
                          dinero real a alguien

  Antes del primer peso de un inversor hay una lista de verificación completa en la spec del
  fondo (specs/M11-FUND.md → "Antes de recibir dinero real de terceros"). Lo más importante:
  - Probar todo el recorrido en práctica: depositar, asignar a un agente, liquidar con una
    salida, pagar el retiro y ver que la conciliación da 0.
  - Probarlo en testnet con el exchange real.
  - La API key de la billetera SIN permiso de retiro y con lista blanca de IP: si alguien la
    roba, no puede sacar el dinero.
  - Desactivar "pagar comisiones con BNB" en la billetera.
  - Respaldos automáticos de la base de datos: ahí vive la cuenta de cada persona.

  Riesgos que hay que tener presentes:
  - Todo el dinero está en un solo exchange: si el exchange falla, se afecta a todos. Conviene
    tener un tope y guardar el resto fuera.
  - Los retiros solo se atienden en una liquidación, y un agente con una operación abierta no se
    puede liquidar: acuerden un calendario (p. ej. el día 1 de cada mes).
  - Los retiros se envían a mano desde Binance: copien la dirección y la red desde la app (nunca
    las escriban) y usen la lista blanca de direcciones de Binance.
  - Si la conciliación del Resumen del fondo sale negativa (falta dinero), no paguen retiros
    hasta entender por qué.

La plataforma hace el cálculo automático y transparente — el inversor puede ver
cada operación que ejecutó el bot con su capital.
