# Trading AI — Qué hace cada módulo

Una explicación simple de los 9 módulos del sistema, sin tecnicismos.

---

## Módulo 1 — Auth (Autenticación) ✅ COMPLETO

**En palabras simples:** Es la puerta de entrada al sistema. Se encarga de saber quién eres y si tienes permiso de entrar.

**Qué hace:**
- Te deja iniciar sesión con tu correo y contraseña
- También puedes iniciar sesión con un código de un solo uso (OTP) que llega a tu email
- Guarda una "sesión" segura en tu navegador para que no tengas que volver a escribir tu contraseña cada vez
- Si te equivocas la contraseña 3 veces, te bloquea temporalmente por seguridad
- Tiene dos tipos de usuario: **Administrador** (puede hacer todo) y **Usuario** (solo puede ver)

**Páginas:**
- `/login` — Pantalla de inicio de sesión
- `/dashboard` — Panel principal
- `/profile` — Cambiar contraseña

---

## Módulo 2 — Market Data (Datos de Mercado) ✅ COMPLETO

**En palabras simples:** Es la bodega de datos. Guarda toda la información de los precios de los activos financieros a lo largo del tiempo.

**Qué hace:**
- Registra los **exchanges** (plataformas de trading) como Binance, Bybit, Kraken, etc.
- Registra los **símbolos** (pares de trading) como BTC/USDT, ETH/USDT, EUR/USD, XAU/USD, etc.
- Registra los **timeframes** (marcos de tiempo) como 1 minuto, 5 minutos, 1 hora, 1 día, etc.
- Almacena **velas OHLCV**: cada vela es un resumen del precio en un período de tiempo (precio de apertura, precio más alto, precio más bajo, precio de cierre y volumen negociado)

**Páginas:**
- `/market/symbols` — Lista de todos los símbolos disponibles (para todos los usuarios)
- `/market/candles` — Ver las velas/precios de un símbolo (para todos los usuarios)
- `/admin/exchanges` — Gestionar exchanges (solo Administrador)
- `/admin/symbols` — Gestionar símbolos (solo Administrador)
- `/admin/timeframes` — Gestionar timeframes (solo Administrador)
- `/admin/candles/ingest` — Cargar velas/precios históricos (solo Administrador)

---

## Módulo 3 — Feature Engineering (Indicadores Técnicos) ✅ COMPLETO

**En palabras simples:** Es el analista técnico. Toma los precios históricos y calcula indicadores que ayudan a entender si el mercado está subiendo, bajando o moviéndose de lado.

**Qué hace:**
- Calcula indicadores populares como:
  - **RSI** — Si el activo está "sobrecomprado" o "sobrevendido"
  - **EMA** — Promedio móvil del precio (tendencia general)
  - **MACD** — Fuerza y dirección del movimiento del precio
  - **ATR** — Cuánto se mueve el precio en promedio (volatilidad)
  - **Bollinger Bands** — Rango normal de movimiento del precio
  - **Volumen relativo** — Si el volumen actual es mayor o menor al promedio reciente
- Detecta el **régimen del mercado**: ¿Está el precio haciendo máximos más altos (tendencia alcista)? ¿O está moviéndose en un rango lateral?
- Permite crear **Feature Sets**: conjuntos de indicadores nombrados y versionados que se reutilizan entre estrategias

**Por qué importa:** El agente de IA necesita estos indicadores para tomar decisiones. Sin ellos, el agente no tiene información suficiente para operar.

**Páginas — Usuario (cualquier usuario autenticado):**
- `/features` — Ver los indicadores calculados de un símbolo: filtra por símbolo, timeframe y feature set, y muestra la tabla con todos los valores (RSI, EMAs, MACD, ATR, Bollinger, régimen)

**Páginas — Administrador (solo admin):**
- `/admin/feature-sets` — Gestionar feature sets (crear nuevos con su spec JSON) y lanzar el cálculo de indicadores sobre cualquier símbolo y timeframe

---

## Módulo 4 — Accounts & Portfolio (Cuentas y Portafolio) 📌 PENDIENTE

**En palabras simples:** Es la billetera. Guarda información sobre tu dinero: cuánto tienes, en qué exchanges, y cómo ha evolucionado tu capital en el tiempo.

**Qué hace:**
- Registra tus **cuentas de trading** (puedes tener varias, en distintos exchanges)
- Cada cuenta puede ser **paper** (simulada, sin dinero real) o **live** (dinero real)
- Guarda los **balances**: cuánto tienes de cada moneda (USDT, BTC, ETH, etc.)
- Hace **snapshots** periódicos de tu portafolio para que puedas ver cómo crece (o decrece) tu capital

---

## Módulo 5 — Strategies (Estrategias) 📌 PENDIENTE

**En palabras simples:** Es el libro de reglas. Define exactamente cuándo el sistema debe considerar entrar o salir de una operación.

**Qué hace:**
- Guarda estrategias de trading con sus reglas configurables (¿en qué timeframe operar? ¿qué indicadores necesita? ¿tendencia o rango lateral?)
- Dos tipos principales:
  - **Trend-following** (seguir tendencia): opera cuando el precio está haciendo máximos más altos
  - **Mean-reversion** (reversión a la media): opera cuando el precio se aleja mucho de su promedio y se espera que regrese
- Valida que la estrategia sea coherente con el mercado actual (ej: una estrategia de tendencia no se activa en mercado lateral)

---

## Módulo 6 — AI Agent / Models (Agente de IA) 📌 PENDIENTE

**En palabras simples:** Es el cerebro. Toma todo lo que saben los otros módulos y decide si una operación es buena o mala.

**Qué hace:**
1. Revisa en qué régimen está el mercado (tendencia o rango) — si no coincide con la estrategia, cancela
2. Valida que se cumplan todas las reglas de la estrategia — si falta una, cancela
3. Calcula el tamaño de la posición: cuánto dinero poner en riesgo (máximo 1% del capital)
4. Verifica que la ganancia proyectada sea al menos el doble del riesgo (ratio 2:1) — si no, cancela
5. Da un veredicto final: **APROBADA** o **RECHAZADA**, con los niveles de entrada, Stop Loss y Take Profit

**Tecnología:** Usa **Ollama** corriendo en tu PC (es una IA local, sin costos de API externa). El modelo actual es `gemma3:4b`.

---

## Módulo 7 — Bots & Signals (Bots y Señales) 📌 PENDIENTE

**En palabras simples:** Es el piloto automático. Un bot es una instancia que aplica una estrategia sobre un símbolo específico, de forma continua y automática.

**Qué hace:**
- Crea **bots** que combinan: cuenta + símbolo + estrategia + parámetros de riesgo
- Los bots se pueden activar, pausar o detener
- Cada vez que el agente de IA aprueba una operación, el bot genera una **señal**: BUY, SELL o HOLD, con precio de entrada, Stop Loss, Take Profit y tamaño de posición
- Las señales con ratio R/R menor a 2:1 son automáticamente rechazadas

---

## Módulo 8 — Orders & Execution (Órdenes y Ejecución) 📌 PENDIENTE

**En palabras simples:** Es quien aprieta el botón de comprar/vender. Cuando el bot genera una señal aprobada, este módulo ejecuta la orden real en el exchange.

**Qué hace:**
- Envía órdenes al exchange (Binance, Bybit, etc.) vía API
- Tipos de órdenes: market (al precio actual), limit (a un precio específico), stop-limit (cierre automático)
- Registra las **ejecuciones** (fills): cuánto se compró/vendió realmente, a qué precio y con qué comisión
- Gestiona las **posiciones abiertas**: cuánto tienes comprado/vendido en este momento
- Cierra automáticamente una posición cuando el precio llega al Stop Loss o al Take Profit

**Importante:** Las cuentas "paper" simulan las órdenes sin tocar dinero real. Las cuentas "live" operan con dinero real.

---

## Módulo 9 — Alerts (Alertas) 📌 PENDIENTE

**En palabras simples:** Es el sistema de notificaciones. Te avisa cuando pasa algo importante, sin que tengas que estar mirando la pantalla todo el tiempo.

**Qué hace:**
- Define **reglas de alerta** personalizables, por ejemplo:
  - "Avísame si el precio de BTC/USDT baja de $80,000"
  - "Avísame si mi bot pierde más del 5% del capital"
  - "Avísame cuando se genere una señal de compra"
- Envía las alertas por **email** o por **webhook** (URL externa)
- Guarda un historial de todas las alertas disparadas

---

## Resumen visual del flujo completo

```
[Módulo 2: Market Data]
   Precios históricos (velas OHLCV)
         ↓
[Módulo 3: Feature Engineering]
   Indicadores técnicos + Régimen de mercado
         ↓
[Módulo 4: Accounts]     [Módulo 5: Strategies]
   Capital disponible  +  Reglas de entrada/salida
         ↓                        ↓
         └──────────┬─────────────┘
                    ↓
         [Módulo 6: AI Agent]
         ¿La operación es buena?
         APROBADA / RECHAZADA
                    ↓
         [Módulo 7: Bots & Signals]
         Señal: BUY / SELL / HOLD
                    ↓
         [Módulo 8: Orders & Execution]
         Orden enviada al exchange
         Stop Loss / Take Profit automáticos
                    ↓
         [Módulo 9: Alerts]
         Notificaciones por email o webhook
```

---

*El Módulo 1 (Auth) protege el acceso a todo el sistema. Sin estar autenticado, no se puede usar ningún módulo.*
