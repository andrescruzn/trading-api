# Módulo 10 — Billing & Managed Accounts (Facturación y Cuentas Administradas) ✅ COMPLETO

← [Índice de módulos](_ROOT.md)

## Ficha

| Campo | Valor |
|---|---|
| Estado | ✅ Completo |
| Avance (alcance original) | 100 % — 16/16 entregables |
| Madurez (estimada) | 75 % — ver [Avance](#avance) |
| Tablas | `investors`, `managed_accounts`, `billing_periods`, `fee_transactions` (R/W); `users`, `bots` (R) |
| Depende de | [M1](M01-AUTH.md) (rol `investor`), [M4](M04-ACCOUNTS-PORTFOLIO.md) (cuenta), [M7](M07-BOTS-SIGNALS.md) (bot opcional), [M8](M08-ORDERS-EXECUTION.md) (historial de órdenes/fills) |
| Lo usan | Es el módulo final (modelo de negocio) |
| Prefijo API | `/api/investors`, `/api/managed-accounts`, `/api/billing-periods`, `/api/fee-transactions` |
| Frontend | `frontend/src/modules/billing` |
| Última revisión | 2026-10-08 |

## Descripción

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

**Rol nuevo:** `role_id=3 → investor` (además de las secciones comunes del menú, ve "Mi inversión" con su dashboard)

## Páginas

Hash routing: la URL real es `/#/<ruta>`.

**Páginas — Administrador (solo admin):**
- `/#/admin/investors` — CRUD de inversores: crear, editar fee (en %) y estado
- `/#/admin/managed-accounts` — CRUD de cuentas administradas: capital, HWM, período, bot asignado
- `/#/admin/billing` — Gestión de períodos: abrir/cerrar período (diálogos con vista previa del fee) + High-Water Mark + historial de fees

**Páginas — Inversor (usuario con rol `investor`):**
- `/#/investor/dashboard` — KPIs: capital inicial, HWM, PnL neto total, fees pagados + historial de períodos + transacciones

## Entregables

Tablas nuevas: `investors`, `managed_accounts`, `billing_periods`, `fee_transactions`

Entregables:
- ✅ 4 tablas (modelos en `billing/infrastructure/`, creadas por Alembic) + rol investor en el seed `database/seeds/roles.py` (id = `AUTH_INVESTOR_ROLE_ID`)
- ✅ Domain entities: Investor, ManagedAccount, BillingPeriod (HWM logic), FeeTransaction con Protocol repos
- ✅ Infrastructure: ORM models (Numeric(5,4) fee_pct, Numeric(30,12) capital) + 4 repos impl
- ✅ HWM logic en `BillingPeriod.calculate_fee()`: `baseline = max(opening_equity, high_water_mark)`
- ✅ Services: CRUD investors, CRUD managed_accounts, open_billing_period, close_billing_period (atómico)
- ✅ Provider: BillingServiceFactory + get_billing_factory(session)
- ✅ REST: GET/POST `/api/investors`, GET/PUT `/api/investors/{id}`
- ✅ REST: GET/POST `/api/managed-accounts`, GET/PUT `/api/managed-accounts/{id}`
- ✅ REST: GET `/api/billing-periods`, POST `/api/billing-periods/open`, POST `/api/billing-periods/{id}/close`
- ✅ REST: GET `/api/fee-transactions`
- ✅ Web UI admin: `/#/admin/investors`, `/#/admin/managed-accounts`, `/#/admin/billing` (React desde 2026-10-08)
- ✅ Web UI inversor: `/#/investor/dashboard` (KPIs + historial períodos + fee transactions)
- ✅ Sidebar: sección "Mi inversión" visible solo para `role_code = investor` (`app-sidebar.tsx`, `role: ROLES.INVESTOR`)
- ✅ Nuevo rol: role_id=3 → investor; settings.AUTH_INVESTOR_ROLE_ID = 3
- ✅ ~~CSP: prefijo /investor/ en security_headers.py~~ (ya no aplica: API headless desde 2026-10-08)
- ✅ Tests unitarios: 53 tests pasando (entity HWM, close/open period service)

## Decisiones de diseño

| Decisión | Motivo | Alternativa descartada |
|---|---|---|
| **High-Water Mark**: `baseline = max(opening_equity, high_water_mark)`; `fee = max(closing − baseline, 0) × fee_pct` | El inversor nunca paga dos veces por recuperar pérdidas; alinea intereses | Fee sobre la ganancia bruta de cada período |
| `high_water_mark` inicial = `initial_capital` (no cero) | Con HWM = 0 el primer período cobraría fee sobre todo el capital | HWM = 0 |
| Se copia `investor.fee_pct` al período al abrirlo (**snapshot**) | Cambiar el fee del inversor no reescribe períodos pasados | Leer el fee vigente al cerrar |
| Cierre **atómico**: actualizar período + crear `fee_transaction` + `update_high_water_mark()` en un solo `commit()` | Nunca queda un período cerrado sin su cobro o con HWM desfasado | Pasos en transacciones separadas |
| Un solo período abierto por cuenta administrada | Evita solapes de facturación | Varios períodos concurrentes |
| `fee_pct` como `Numeric(5,4)` (0.20 = 20 %); el front pide el % y lo convierte a fracción string al enviar (`billing-labels.ts`: `(percent / 100).toFixed(4)`) | Precisión exacta sin `float` | Guardar porcentaje entero |
| Importes con `Numeric(30,12)` y `Decimal` | Dinero sin errores de coma flotante | `float` |
| `fee_transactions` con `billing_period_id` UNIQUE y estados `pending` / `charged` / `waived` | Un cobro por período, auditable | Campo `fee_paid` en el período |
| Rol nuevo `investor` (`role_id = 3`, `settings.AUTH_INVESTOR_ROLE_ID`) | El inversor tiene su dashboard propio (`_app/investor.tsx` con `InvestorGuardLayout`); el sidebar le añade "Mi inversión" y le oculta "Administración" | Reutilizar el rol `user` |
| Propiedad: el inversor ve solo sus cuentas (`find_by_user_id`); el admin usa `list_all()` | Aislamiento entre inversores | Filtrar en el cliente |
| Alta/edición de inversores, cuentas y períodos solo para admin | El cobro lo controla quien administra el negocio | Autoservicio |
| Prefijo `/api/` (hoy común a toda la API vía `settings.API_PREFIX`) | Originalmente para evitar colisión con las páginas Jinja; el prefijo `/investor/` del CSP desapareció con la API headless (2026-10-08) | — |

## Avance

| Métrica | Valor | Evidencia |
|---|---|---|
| Alcance original | **100 %** (16/16) | Migración, dominio, infraestructura, servicios, REST, UI admin + inversor, rol y 53 tests |
| Madurez | **≈ 75 %** | Funcionalidad 80 · Tests 80 · Seguridad 85 · Operación 55 |

- **Funcionalidad (80):** la `closing_equity` la **introduce el admin a mano** al cerrar el período (no se deriva de balances ni de posiciones). No hay endpoint para pasar una `fee_transaction` a `charged` / `waived`: las entidades tienen `mark_as_charged()` y `waive()`, pero el REST solo expone `GET /api/fee-transactions`.
- **Tests (80):** 53 tests (HWM, entidades, abrir/cerrar período); sin tests de REST ni de propiedad.
- **Operación (55):** sin cobro real, extractos ni automatización del cierre.

## Posibles mejoras

| Prioridad | Mejora | Esfuerzo |
|---|---|---|
| Alta | Endpoints (y botones en `/#/admin/billing`) para marcar una `fee_transaction` como `charged` o `waived`; hoy quedan en `pending` salvo edición en BD | S |
| Alta | Derivar `closing_equity` de los balances de la cuenta ([M4](M04-ACCOUNTS-PORTFOLIO.md)) o de `portfolio_snapshots` en lugar de pedirlo a mano | M |
| Alta | Aportes y retiros de capital a mitad de período (hoy distorsionan `gross_pnl` y el HWM) | L |
| Media | Cierre automático al llegar `period_type` (mensual/trimestral) con un job programado | M |
| Media | Extracto/PDF por período para el inversor y notificación por email/Telegram ([M9](M09-ALERTS.md)) al cerrar | M |
| Media | Tests de REST y de propiedad (inversor A no ve cuentas del inversor B) | S |
| Baja | Cobro real (pasarela de pago / facturación) integrado con `fee_transactions` | L |
| Baja | Múltiples monedas con conversión | L |

## Fuera de alcance y pendientes conocidos

- Cobro efectivo del fee (solo se registra la transacción).
- Aportes/retiros de capital durante un período abierto.
- Facturación legal / fiscal y cumplimiento normativo.
- Cierre automático de períodos.

## Detalle técnico

### Tablas en BD
| Tabla | Acción | Nota |
|-------|--------|------|
| `investors` | WRITE | Perfil de inversor: user_id (UNIQUE), fee_pct Decimal(5,4), is_active |
| `managed_accounts` | WRITE | Cuenta administrada: investor_id, account_id, bot_id opcional, capital, HWM, period_type |
| `billing_periods` | WRITE | Períodos: opening_equity, closing_equity, gross_pnl, fee_pct snapshot, fee_amount, net_pnl, status (open/closed) |
| `fee_transactions` | WRITE | Cobros de fee: billing_period_id (UNIQUE), amount, status (pending/charged/waived) |
| `users` | READ | Para verificar que user_id existe al crear inversor |
| `bots` | READ | Validación opcional del bot_id en managed_account |

### Modelos ORM (`app/modules/billing/infrastructure/`)
| Archivo | Clase | Tabla |
|---------|-------|-------|
| `investor_model.py` | `InvestorModel` | `investors` |
| `managed_account_model.py` | `ManagedAccountModel` | `managed_accounts` |
| `billing_period_model.py` | `BillingPeriodModel` | `billing_periods` |
| `fee_transaction_model.py` | `FeeTransactionModel` | `fee_transactions` |

Registrados en: `app/extensions/db/models_registry.py`

### Repositorios (`app/modules/billing/`)
| Domain (Protocol) | Infrastructure (impl) |
|-------------------|-----------------------|
| `domain/investor_repository.py` | `infrastructure/investor_repository_impl.py` → `SqlAlchemyInvestorRepository` |
| `domain/managed_account_repository.py` | `infrastructure/managed_account_repository_impl.py` → `SqlAlchemyManagedAccountRepository` |
| `domain/billing_period_repository.py` | `infrastructure/billing_period_repository_impl.py` → `SqlAlchemyBillingPeriodRepository` |
| `domain/fee_transaction_repository.py` | `infrastructure/fee_transaction_repository_impl.py` → `SqlAlchemyFeeTransactionRepository` |

### Domain Entities (`app/modules/billing/domain/`)
| Archivo | Entidad | Clave |
|---------|---------|-------|
| `investor_entity.py` | `Investor` | `fee_as_percentage()`, `is_valid_fee_pct()` |
| `managed_account_entity.py` | `ManagedAccount` | `VALID_PERIOD_TYPES`, `update_high_water_mark()` |
| `billing_period_entity.py` | `BillingPeriod` | `calculate_fee(closing_equity, hwm)` — baseline = max(opening_equity, hwm) |
| `fee_transaction_entity.py` | `FeeTransaction` | `mark_as_charged()`, `waive()`. States: pending/charged/waived |

### Lógica HWM (crítica)
```python
# BillingPeriod.calculate_fee(closing_equity, high_water_mark)
baseline = max(self.opening_equity, high_water_mark)
gross_pnl = closing_equity - self.opening_equity
profit_above_hwm = closing_equity - baseline   # puede ser negativo
fee_amount = max(profit_above_hwm, 0) * self.fee_pct
```
- Si `closing_equity <= baseline` → fee_amount = 0 (no cobrar si no hay nuevos máximos)
- `has_fee_to_charge()` → `fee_amount > 0`

### Servicios (`app/modules/billing/services/`)
| Subdir | Servicios |
|--------|-----------|
| `investors/` | `list_investors_service.py`, `create_investor_service.py`, `update_investor_service.py` |
| `managed_accounts/` | `list_managed_accounts_service.py`, `get_managed_account_service.py`, `create_managed_account_service.py`, `update_managed_account_service.py` |
| `billing/` | `list_billing_periods_service.py`, `open_billing_period_service.py`, `close_billing_period_service.py`, `list_fee_transactions_service.py` |

Provider: `app/modules/billing/providers/billing_provider.py` → `BillingServiceFactory` + `get_billing_factory(session)`

### Endpoints REST
| Método | Ruta | Auth | Nota |
|--------|------|------|------|
| GET | `/api/investors` | admin · investor | Admin: lista todos; investor: solo su propio perfil (lo usa el dashboard); otros roles → 403 |
| POST | `/api/investors` | admin | Crea inversor (valida user_id único, fee_pct 0-1) |
| GET | `/api/investors/{id}` | admin | Detalle inversor |
| PUT | `/api/investors/{id}` | admin | Actualiza fee_pct y/o is_active |
| GET | `/api/managed-accounts` | token | Admin ve todas; investor ve las suyas (find_by_user_id) |
| POST | `/api/managed-accounts` | admin | Crea cuenta administrada (HWM = initial_capital) |
| GET | `/api/managed-accounts/{id}` | token | Detalle con ownership check |
| PUT | `/api/managed-accounts/{id}` | admin | Actualiza nombre, bot_id, period_type, is_active |
| GET | `/api/billing-periods` | token | Filtro por managed_account_id |
| POST | `/api/billing-periods/open` | admin | Abre período (valida que no haya uno abierto) |
| POST | `/api/billing-periods/{id}/close` | admin | Cierra período (HWM + fee_tx atómico) |
| GET | `/api/fee-transactions` | token | Filtro por managed_account_id |

Los routers declaran `prefix="/investors"` y `"/managed-accounts"`; `billing_periods_router` no tiene prefijo y declara `/billing-periods…` y `/fee-transactions` en cada ruta. El `/api` lo añade `app_factory.py` (`settings.API_PREFIX`).

Routers registrados en `app/app_factory.py` (dentro de `api_routers`):
```python
from app.modules.billing.rest import investors_router, managed_accounts_router, billing_periods_router
```

### Frontend (`frontend/src/modules/billing/`)
| Ruta | Archivo de ruta | Página / componentes | Rol |
|-----|----------|----|-----|
| `/#/admin/investors` | `routes/_app/admin/investors.lazy.tsx` | `pages/admin-investors.tsx` + `components/investor-form-dialog.tsx` | admin |
| `/#/admin/managed-accounts` | `routes/_app/admin/managed-accounts.lazy.tsx` | `pages/admin-managed-accounts.tsx` + `components/managed-account-form-dialog.tsx` | admin |
| `/#/admin/billing` | `routes/_app/admin/billing.lazy.tsx` | `pages/admin-billing.tsx` + `components/billing-period-dialogs.tsx` (`OpenPeriodDialog`, `ClosePeriodDialog`) + `components/billing-tables.tsx` | admin |
| `/#/investor/dashboard` | `routes/_app/investor/dashboard.lazy.tsx` (guard `_app/investor.tsx`) | `pages/investor-dashboard.tsx` | investor |

- API: `api/billing.api.ts` (importes y `fee_pct` como string); hooks `use-billing-queries.ts` / `use-billing-mutations.ts`; conversión % ↔ fracción y etiquetas en `lib/billing-labels.ts`.

### Sidebar
- `app-shell/components/app-sidebar.tsx`: sección "Mi inversión" (`role: ROLES.INVESTOR`) con "Mi dashboard" → `/investor/dashboard`; sección "Administración" → "Inversores" (Inversores, Cuentas gestionadas, Facturación) solo para admin.
- El rol se decide por `role_code` de `GET /api/users/me`, no por el JWT.

### Settings nuevos (`app/common/config/settings.py`)
```python
AUTH_INVESTOR_ROLE_ID: int = 3  # leído de env AUTH_INVESTOR_ROLE_ID, default 3
```

## Gotchas críticos

- **fee_pct en BD:** `Numeric(5,4)` — se guarda como decimal (0.20 = 20%). El front pide el porcentaje y lo divide por 100 al enviar (`billing-labels.ts`).
- **HWM inicial:** en `create_managed_account`, `high_water_mark = initial_capital` (no cero).
- **Snapshot fee_pct:** al abrir período se copia `investor.fee_pct` al período — si cambia el fee futuro no afecta períodos pasados.
- **Cierre atómico:** `close_billing_period_service.py` hace un solo `session.commit()` que incluye: actualizar período + crear fee_tx + llamar `update_high_water_mark()`.
- **Investor ownership:** `list_managed_accounts` llama `find_by_user_id(current_user.id)` para filtrar al inversor. Admin usa `list_all()`.
- **Esquema:** 4 tablas declaradas en los modelos de `billing/infrastructure/` (antes `migrations/m10_billing.sql`, eliminado) + rol investor en `database/seeds/roles.py`.

## Tests

- 53 tests unitarios en `tests/billing/`: `test_billing_period_entity.py` (HWM), `test_investor_and_managed_account_entities.py`, `test_open_billing_period_service.py`, `test_close_billing_period_service.py`.
- **Huecos:** rutas REST, ownership del inversor, listados y `fee_transactions`.

## Riesgos

- **Dinero de terceros:** una `closing_equity` mal introducida genera un fee incorrecto; no hay verificación cruzada con el exchange.
- El cierre del período es irreversible desde la UI (no hay "reabrir").
- Administrar capital ajeno y cobrar comisión de performance puede tener implicaciones regulatorias según la jurisdicción; este documento no es asesoría legal.

## Historial

- **2026-03** — Módulo completado: migración `m10_billing.sql` + seed `seed_billing.sql` (rol `investor` id=3), dominio con HWM, servicios, REST, UI `/admin/investors`, `/admin/managed-accounts`, `/admin/billing` y `/investor/dashboard`.
- **2026-10-08** — API headless (/api), páginas migradas a React (frontend/).
