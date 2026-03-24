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

## Módulo 4 — Accounts & Portfolio (Cuentas y Portafolio) ✅ COMPLETO

**En palabras simples:** Es la billetera. Guarda información sobre tu dinero: cuánto tienes, en qué exchanges, y cómo ha evolucionado tu capital en el tiempo.

**Qué hace:**
- Registra tus **cuentas de trading** (puedes tener varias, en distintos exchanges)
- Cada cuenta puede ser **paper** (simulada, sin dinero real) o **live** (dinero real)
- Guarda los **balances**: cuánto tienes de cada moneda (USDT, BTC, ETH, etc.) — snapshots inmutables
- Las credenciales de API (api_key/api_secret) se cifran con Fernet antes de guardarlas en la BD
- Equity curve vía time series de `account_balances`

**Páginas — Usuario (cualquier usuario autenticado):**
- `/portfolio` — Panel de cuentas: lista tus cuentas, crea nuevas, consulta balances y equity curve

**Páginas — Administrador (solo admin):**
- `/admin/accounts` — Vista global de todas las cuentas del sistema

---

## Módulo 5 — Strategies (Estrategias) ✅ COMPLETO

**En palabras simples:** Es el libro de reglas. Define exactamente cuándo el sistema debe considerar entrar o salir de una operación.

**Qué hace:**
- Guarda estrategias de trading con sus reglas configurables (¿en qué timeframe operar? ¿qué indicadores necesita? ¿tendencia o rango lateral?)
- Dos tipos principales:
  - **Trend-following** (seguir tendencia): opera cuando el precio está haciendo máximos más altos
  - **Mean-reversion** (reversión a la media): opera cuando el precio se aleja mucho de su promedio y se espera que regrese
- Valida coherencia tipo ↔ régimen: trend_following acepta trend_up/trend_down; mean_reversion acepta sideways
- Gestiona **datasets** de backtesting (rango de velas + features para un símbolo y timeframe)

**Páginas — Usuario (cualquier usuario autenticado):**
- `/strategies` — Lista de estrategias con tipo, régimen, timeframe y cantidad de reglas. Click para ver detalles completos.

**Páginas — Administrador (solo admin):**
- `/admin/strategies` — Crear y editar estrategias con editor de reglas JSON y validación de coherencia en vivo

---

## Módulo 6 — AI Agent / Models (Agente de IA) ✅ COMPLETO

**En palabras simples:** Es el cerebro. Toma todo lo que saben los otros módulos y decide si una operación es buena o mala.

**Qué hace:**
1. Revisa en qué régimen está el mercado (tendencia o rango) — si no coincide con la estrategia, cancela
2. Valida que se cumplan todas las reglas de la estrategia — si falta una, cancela
3. Consulta al LLM para calcular los niveles de entrada, Stop Loss y Take Profit; Python ejecuta la fórmula de posición: `Capital × risk_pct / |entrada − SL|`
4. Verifica que la ganancia proyectada sea al menos el doble del riesgo (ratio 2:1 configurable) — si no, cancela
5. Da un veredicto final: **APROBADA** o **RECHAZADA**, con todos los detalles de la operación

**Tecnología:** Soporta múltiples proveedores de LLM: OpenAI, Anthropic (Claude), xAI (Grok), DeepSeek, Gemini y Ollama (local). El proveedor se configura con la variable de entorno `LLM_PROVIDER`.

**Páginas — Usuario (cualquier usuario autenticado):**
- `/agent` — Panel de análisis: selecciona símbolo, timeframe, estrategia y cuenta, lanza el análisis y ve el resultado (APROBADA/RECHAZADA con entry, SL, TP, tamaño de posición y resumen de indicadores)

**Páginas — Administrador (solo admin):**
- No hay página admin específica en este módulo; la gestión de modelos ML se hace vía API

---

## Módulo 7 — Bots & Signals (Bots y Señales) ✅ COMPLETO

**En palabras simples:** Es el piloto automático. Un bot es una instancia que aplica una estrategia sobre un símbolo específico, de forma continua y automática.

**Qué hace:**
- Crea **bots** que combinan: cuenta + símbolo + estrategia + feature set + parámetros de riesgo
- Los bots se pueden activar (`start`), pausar (`pause`) y detener (`stop`) — máquina de estados con transiciones válidas
- Cada bot tiene su propio `feature_set_id` (no es global)
- Al generar una señal: invoca el Agente (M6) con el contexto del bot y persiste el resultado
- Las señales APROBADAS: acción BUY o SELL + entry, SL, TP, position_size, rr_ratio
- Las señales RECHAZADAS: acción HOLD, `approved=False`, todas persisten para trazabilidad
- `features_hash`: SHA-256 del contexto de mercado, fingerprint para auditoría

**Páginas — Usuario (cualquier usuario autenticado):**
- `/bots` — Panel de bots: lista tus bots, crea nuevos, start/pause/stop, ver señales de cada bot, generar señal manualmente

**Páginas — Administrador (solo admin):**
- `/admin/bots` — Vista global de todos los bots del sistema con filtros por estado y modo

---

## Módulo 8 — Orders & Execution (Órdenes y Ejecución) ✅ COMPLETO

**En palabras simples:** Es quien aprieta el botón de comprar/vender. Cuando el bot genera una señal aprobada, este módulo ejecuta la orden real en el exchange.

**Qué hace:**
- Crea **órdenes** para un bot: market (precio actual), limit (precio fijo), stop y stop-limit
- Ejecuta la orden según el modo del bot:
  - **Paper mode:** simula el fill usando el precio de cierre de la última vela (fee = 0)
  - **Live mode:** envía la orden real al exchange vía ccxt, recibe precio y fee reales
- Registra las **ejecuciones** (fills): cuánto se ejecutó realmente, a qué precio y con qué comisión
- Gestiona las **posiciones abiertas**: recalcula el precio promedio (WAP) en cada compra, acumula el P&L realizado en cada venta
- Máquina de estados de la orden: `new → sent → filled / partially_filled / canceled / rejected`

**Importante:** Las cuentas "paper" simulan las órdenes sin tocar dinero real. Las cuentas "live" operan con dinero real.

**Páginas — Usuario (cualquier usuario autenticado):**
- `/orders` — Libro de órdenes: selector de bot, tabs de Órdenes / Posiciones / Ejecuciones, modal para crear nueva orden

**Páginas — Administrador (solo admin):**
- `/admin/orders` — Vista global de todas las órdenes del sistema con filtros por lado, estado y tipo

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

## Módulo 10 — Billing & Managed Accounts (Facturación y Cuentas Administradas) 📌 PENDIENTE

**En palabras simples:** Es el modelo de negocio. Permite que inversores (tu jefe, clientes, socios) pongan capital en el sistema y tú te llevas un porcentaje de las ganancias que genera el bot. Si el bot no gana, tú no cobras.

**Qué hace:**
- Registra **inversores** y el capital que aportaron a cada cuenta administrada
- Calcula automáticamente la **ganancia neta** al cierre de cada período (semana/mes)
- Aplica la **performance fee** configurada (ej: 20% de las ganancias)
- Genera un **estado de cuenta** por inversor: capital inicial, ganancias brutas, fee cobrado, ganancia neta del inversor
- Registra todos los cobros en un historial auditable
- Envía el resumen automáticamente por email al cerrar el período

**Modelo de negocio (Managed Account):**
- El inversor aporta capital (ej: $10,000 USD)
- El bot opera ese capital con las estrategias configuradas
- Al cierre del período: si ganó $500 → tú cobras $100 (20%) → el inversor recibe $400 netos
- Si el bot pierde → no se cobra nada (alineación de intereses)

**Páginas — Administrador (solo admin):**
- `/admin/billing` — Panel de inversores, capital aportado, ganancias del período, fees cobrados

**Páginas — Inversor (usuario con rol inversor):**
- `/investor/dashboard` — Mi capital, rendimiento histórico, fees pagados, estado de cuenta

---

## Resumen visual del flujo completo

```
[Módulo 2: Market Data]
   Precios históricos (velas OHLCV)
         ↓
[Módulo 3: Feature Engineering]
   Indicadores técnicos + Régimen de mercado
         ↓
[Módulo 4: Accounts ✅]  [Módulo 5: Strategies ✅]
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

---

## ⚠️ Nota importante — El sistema no garantiza ganancias por sí solo

El bot ejecuta las reglas de las estrategias con disciplina perfecta. Pero la rentabilidad depende del **edge** (ventaja estadística) de esas estrategias.

**¿Qué es el edge?**
Una estrategia tiene edge cuando el historial de operaciones muestra que las ganancias superan las pérdidas de forma consistente. Se mide con: Win Rate, R/R real, Profit Factor y Max Drawdown.

**¿Cómo se valida el edge en este sistema?**
1. Correr el sistema en **modo paper** (M7 + M8 sin dinero real) durante 3-6 meses
2. Acumular 100+ operaciones por estrategia
3. Calcular métricas reales del historial (`signals` → `orders` → `fills`)
4. Solo pasar a live si los números son consistentemente positivos

**Capital mínimo para operar en live:**
- $5,000 → mínimo para que la Regla del 1% genere operaciones con tamaño real
- $10,000 → razonable para demostrar resultados
- $50,000+ → donde empieza a ser negocio real

Ver `MANUAL.md` Parte 4 para explicación completa de edge, capital y rutas de negocio.
