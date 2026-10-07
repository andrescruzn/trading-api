# Módulo 3 — Feature Engineering (Indicadores Técnicos) ✅ COMPLETO

← [Índice de módulos](_ROOT.md)

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
