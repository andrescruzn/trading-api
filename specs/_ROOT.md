# Trading AI — Índice de módulos

Una explicación simple de los 10 módulos del sistema, sin tecnicismos. Cada módulo tiene su propia spec.

## Estado del proyecto

| Módulo | Estado | Descripción |
|--------|--------|-------------|
| [M1 — Auth & Web UI](M01-AUTH.md) | ✅ Completo | Login password/OTP, sesiones JWT, roles, dashboard |
| [M2 — Market Data](M02-MARKET-DATA.md) | ✅ Completo | Exchanges, símbolos, timeframes, velas OHLCV via ccxt |
| [M3 — Feature Engineering](M03-FEATURE-ENGINEERING.md) | ✅ Completo | RSI, ATR, EMA, MACD, Bollinger Bands, régimen de mercado |
| [M4 — Accounts & Portfolio](M04-ACCOUNTS-PORTFOLIO.md) | ✅ Completo | Cuentas de exchange (credenciales cifradas), balances, equity curve |
| [M5 — Strategies](M05-STRATEGIES.md) | ✅ Completo | Reglas de entrada/salida, validación tipo/régimen, datasets |
| [M6 — AI Agent / Models](M06-AI-AGENT.md) | ✅ Completo | Prompt Maestro multi-provider LLM, modelos ML y model runs |
| [M7 — Bots & Signals](M07-BOTS-SIGNALS.md) | ✅ Completo | Bots automáticos, señales BUY/SELL/HOLD con entry/SL/TP |
| [M8 — Orders & Execution](M08-ORDERS-EXECUTION.md) | ✅ Completo | Órdenes paper/live (ccxt), fills, posiciones |
| [M9 — Alerts](M09-ALERTS.md) | ✅ Completo | Reglas de alerta, notificaciones email/Telegram/webhook/desktop |
| [M10 — Billing & Managed Accounts](M10-BILLING.md) | ✅ Completo | Inversores, cuentas administradas, performance fee con HWM |

Más detalle:
- Hoja de ruta: [`.claude/memory/ROADMAP.md`](../.claude/memory/ROADMAP.md)
- Tablas, archivos y endpoints por módulo: [`.claude/memory/MODULES_MAP.md`](../.claude/memory/MODULES_MAP.md)
- Manual en lenguaje simple: [`MANUAL.md`](../MANUAL.md)

---

## Flujo completo

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

El [Módulo 1 (Auth)](M01-AUTH.md) protege el acceso a todo el sistema. Sin estar autenticado, no se puede usar ningún módulo.
El [Módulo 10 (Billing)](M10-BILLING.md) se apoya en el historial de órdenes y ejecuciones del [Módulo 8](M08-ORDERS-EXECUTION.md) para calcular el fee de performance.

---

## ⚠️ Nota importante — El sistema no garantiza ganancias por sí solo

El bot ejecuta las reglas de las estrategias con disciplina perfecta. Pero la rentabilidad depende del **edge** (ventaja estadística) de esas estrategias.

**¿Qué es el edge?**
Una estrategia tiene edge cuando el historial de operaciones muestra que las ganancias superan las pérdidas de forma consistente. Se mide con: Win Rate, R/R real, Profit Factor y Max Drawdown.

**¿Cómo se valida el edge en este sistema?**
1. Correr el sistema en **modo paper** ([M7](M07-BOTS-SIGNALS.md) + [M8](M08-ORDERS-EXECUTION.md) sin dinero real) durante 3-6 meses
2. Acumular 100+ operaciones por estrategia
3. Calcular métricas reales del historial (`signals` → `orders` → `fills`)
4. Solo pasar a live si los números son consistentemente positivos

**Capital mínimo para operar en live:**
- $5,000 → mínimo para que la Regla del 1% genere operaciones con tamaño real
- $10,000 → razonable para demostrar resultados
- $50,000+ → donde empieza a ser negocio real

Ver [`MANUAL.md`](../MANUAL.md) Parte 4 para explicación completa de edge, capital y rutas de negocio.
