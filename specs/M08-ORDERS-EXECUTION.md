# Módulo 8 — Orders & Execution (Órdenes y Ejecución) ✅ COMPLETO

← [Índice de módulos](_ROOT.md)

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
