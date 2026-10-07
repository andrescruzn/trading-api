# Módulo 7 — Bots & Signals (Bots y Señales) ✅ COMPLETO

← [Índice de módulos](_ROOT.md)

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
