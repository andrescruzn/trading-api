# Glosario y reglas de escritura

Una palabra por concepto. Si la app dice "cuenta" en un lado y "wallet" en otro, la persona duda si son cosas distintas. **Los términos marcados con (*) son propuestas que el usuario debe confirmar**; si corrige uno, actualiza este archivo en la misma sesión.

## Términos preferidos

| Usa | Evita | Notas |
|---|---|---|
| **cuenta** | wallet, account, portafolio (para una sola) | Cuenta de exchange (paper o live). "Mis cuentas" para la lista. |
| **modo paper** / **modo live** | simulado/real mezclados | En badges: `Paper` / `Live`. En explicaciones: "paper (simulado, sin dinero real)". |
| **exchange** | bróker (para cripto), plataforma | Bróker solo cuando el tipo es `broker`. |
| **símbolo** | par, ticker, activo (para el registro) | El registro `BTC/USDT`. "Activo" = base o cotización (`BTC`, `USDT`). |
| **vela** | candle, barra | "Velas OHLCV" en títulos; "vela" en texto. |
| **timeframe** | temporalidad, intervalo | Término de oficio; se mantiene en inglés. |
| **indicador** | feature (en pantalla) | Cálculo sobre las velas (RSI, EMA, MACD…) que la IA revisa. |
| **conjunto de indicadores** | feature set (en pantalla) | Grupo de indicadores que usa un agente: **Completo**, **Tendencia**, **Rango**. |
| **régimen** | tendencia (para el concepto general) | Valores: **Tendencia alcista**, **Tendencia bajista**, **Lateral**. |
| **estrategia** | setup, sistema | |
| **señal** | alerta (para BUY/SELL/HOLD) | Acciones: **Compra**, **Venta**, **Mantener**. |
| **entrada** / **stop loss** / **take profit** | SL/TP sueltos en texto corrido | En tablas compactas sí: `Entrada`, `SL`, `TP`. |
| **riesgo/beneficio** | R:R, RR (en texto corrido) | En tablas: `R/R`. Formato `2,4:1`. |
| **tamaño de posición** | lotaje, size | |
| **orden** | trade (para la orden) | Tipos: **Mercado**, **Límite**, **Stop**, **Stop límite**. Lados: **Compra** / **Venta**. |
| **ejecución** | fill | "Ejecuciones" en la pestaña. |
| **posición** | trade abierto | |
| **agente** | bot, robot | Lo que la persona crea para operar: símbolo + estrategia + cuenta. En código y API sigue siendo `bot`. Estados: **Activo**, **Pausado**, **Detenido**. Acciones: **Iniciar** (**Reanudar** si está pausado), **Pausar**, **Detener**, **Analizar ahora** (pide una señal a la IA). "Mis agentes" para la lista. Excepción: el **bot de Telegram** conserva su nombre. |
| **Compartir señales** / **seguir un agente** | copiar, copy trading, publicar | El dueño **comparte** las señales de su agente; otra persona lo **sigue** (botón `Suscribirme`, para salir `Dejar de seguir`) y recibe sus compras y ventas aprobadas por Telegram. Es información: no se ejecuta nada en su cuenta. Los suyos se marcan `Es tuyo`. |
| **la IA** | agente de IA, modelo (para la IA) | El modelo de lenguaje que evalúa cada operación dentro de un agente. "Modelo" queda para los modelos de ML registrados. |
| **modo de ejecución** | modo de operación, autopiloto | Qué hace el agente cuando la IA aprueba: **Manual**, **Con aprobación**, **Automático**. No confundir con modo paper/live. |
| **señal por aprobar** | señal pendiente (en pantalla) | Señal de un agente Con aprobación que espera tu decisión. Acciones: **Aprobar** / **Descartar** (igual en la app y en Telegram). Estados: **Por aprobar**, **Ejecutada**, **Descartada**, **Vencida**, **No ejecutada**. |
| **regla de alerta** | trigger, alarma | Historial = **eventos de alerta**. |
| **inversor** | cliente | Participante del fondo común que solo ve lo suyo. |
| **socio** | partner, asociado | Ve todo en solo lectura y puede recibir parte de la comisión. |
| **super admin** | administrador, admin, dueño | Los propietarios de la plataforma. |
| **fondo común** | cuenta gestionada, cuenta administrada, managed account | M10 se retiró: el dinero de todos está en una billetera y cada persona tiene su saldo |
| **comisión de desempeño** | performance fee, fee (en texto corrido) | En tablas: `Comisión`. |
| **marca de agua (HWM)** | high water mark (solo) | Primera mención con la sigla entre paréntesis. |
| **período de facturación** | período (solo, si hay ambigüedad) | Acciones: **Abrir período**, **Cerrar período**. |
| **correo** | e-mail, email, mail | `email` solo en código. |
| **código de acceso** | OTP, token, PIN | Lo que llega por correo para ingresar. |
| **Iniciar sesión** | Loguearse, login | Botón: `Ingresar`. |
| **Administrador** / **Inversor** / **Usuario** | admin (en pantalla) | Igual que `role_label` del backend. |

## Reglas de forma

- **Mayúsculas**: solo la inicial en títulos, botones, labels y toasts (`Nuevo agente`, no `Nuevo Agente`). Siglas y nombres propios se respetan (OHLCV, HWM, BTC, Telegram).
- **Botones**: infinitivo o sustantivo de acción (`Crear bot`, `Guardar cambios`, `Descargar del exchange`). **Validaciones**: imperativo (`Elige el símbolo`, `Escribe el nombre`).
- **Puntuación**: títulos y botones sin punto; descripciones con punto. Signos de apertura completos (`¿Detener el bot?`).
- **Exclamaciones y emojis**: no en la app. En Telegram, solo el indicador de acción (🟢 compra / 🔴 venta / ⚪ mantener) si ya está en la plantilla.
- **Números**: formato `es-CO` → miles con punto, decimales con coma (`1.234,56`). Precios con `$` cuando la cotización es USD/USDT. Porcentajes con espacio: `1 %`.
- **Fechas**: compactas en tablas (`8 oct 2026, 2:30 p. m.`); hora del servidor en UTC solo cuando se aclara (`ts (UTC)`).
- **Longitud**: botones 1–3 palabras; título de toast ≤ 5 palabras; descripción ≤ 2 líneas.
- **Nada de**: `Aceptar` como botón único, `Clic aquí`, `Ok`, `Error` como título, plurales con `(s)`.
