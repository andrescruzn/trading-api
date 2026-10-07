# Módulo 5 — Strategies (Estrategias) ✅ COMPLETO

← [Índice de módulos](_ROOT.md)

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
