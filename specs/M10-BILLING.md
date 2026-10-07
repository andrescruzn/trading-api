# Módulo 10 — Billing & Managed Accounts (Facturación y Cuentas Administradas) ✅ COMPLETO

← [Índice de módulos](_ROOT.md)

**En palabras simples:** Es el modelo de negocio. Permite que inversores (tu jefe, clientes, socios) pongan capital en el sistema y tú te llevas un porcentaje de las ganancias que genera el bot. Si el bot no gana, tú no cobras.

**Qué hace:**
- Registra **inversores** con su fee_pct acordado y los vincula a un user_id del sistema
- Gestiona **cuentas administradas** (managed_accounts): capital inicial, High-Water Mark, período de facturación
- Abre y cierra **períodos de billing** con cálculo automático de gross PnL, fee y net PnL
- Aplica **High-Water Mark**: solo cobra fee sobre nuevos máximos de capital (protege al inversor de pagar dos veces)
- Registra todos los cobros como **fee_transactions** auditables (pending/charged/waived)
- Panel admin para gestionar inversores, cuentas y períodos
- Dashboard del inversor para ver su rendimiento histórico

**Modelo de negocio (Managed Account):**
- El inversor aporta capital (ej: $10,000 USD)
- El bot opera ese capital con las estrategias configuradas
- Al cierre del período: si ganó $500 → tú cobras $100 (20%) → el inversor recibe $400 netos
- Si el bot pierde → no se cobra nada (alineación de intereses)
- High-Water Mark: si en mes 2 pierde y en mes 3 recupera pero no supera el máximo anterior, no se cobra fee

**Tablas nuevas:** `investors`, `managed_accounts`, `billing_periods`, `fee_transactions`

**Rol nuevo:** `role_id=3 → investor` (solo ve su propio dashboard)

**Páginas — Administrador (solo admin):**
- `/admin/investors` — CRUD de inversores: crear, editar fee_pct y estado
- `/admin/managed-accounts` — CRUD de cuentas administradas: capital, HWM, período, bot asignado
- `/admin/billing` — Gestión de períodos: abrir/cerrar período + High-Water Mark + historial de fees

**Páginas — Inversor (usuario con rol `investor`):**
- `/investor/dashboard` — KPIs: capital inicial, HWM, PnL neto total, fees pagados + historial de períodos + transacciones
