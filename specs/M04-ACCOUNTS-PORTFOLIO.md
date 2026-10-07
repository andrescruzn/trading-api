# Módulo 4 — Accounts & Portfolio (Cuentas y Portafolio) ✅ COMPLETO

← [Índice de módulos](_ROOT.md)

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
