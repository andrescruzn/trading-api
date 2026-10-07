# Módulo 9 — Alerts (Alertas) ✅ COMPLETO

← [Índice de módulos](_ROOT.md)

**En palabras simples:** Es el sistema de notificaciones. Te avisa cuando pasa algo importante, sin que tengas que estar mirando la pantalla todo el tiempo.

**Qué hace:**
- Define **reglas de alerta** personalizables por tipo:
  - `signal` → "Avísame cuando mi bot genere una señal BUY/SELL"
  - `price` → "Avísame si el precio de BTC/USDT baja de $80,000"
  - `pnl` → "Avísame si el P&L del bot baja del -5%"
  - `drawdown` → "Avísame si el drawdown supera el 10%"
  - `error` → "Avísame cuando el bot entre en error"
- Envía las alertas por **4 canales**: Email (SMTP), Telegram (Bot API), Webhook (HTTP POST a URL externa) y Desktop (notificaciones nativas macOS/Windows/Linux con plyer)
- Las alertas se **disparan automáticamente** cuando se genera una señal (M7) o se ejecuta una orden (M8)
- Guarda un historial de todos los eventos de alerta disparados con estado de entrega
- El despacho es **fire-and-forget**: si falla una alerta, no afecta la operación de trading

**Páginas:**
- `/alerts` — Panel del usuario: reglas configuradas + historial de alertas recibidas
- `/admin/alerts` — Vista admin: todas las reglas y eventos del sistema
- `/admin/telegram` — Configurar y probar la conexión con Telegram Bot
