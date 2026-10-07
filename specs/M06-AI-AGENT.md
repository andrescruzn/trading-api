# Módulo 6 — AI Agent / Models (Agente de IA) ✅ COMPLETO

← [Índice de módulos](_ROOT.md)

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
