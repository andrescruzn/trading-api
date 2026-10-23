# Módulo 11 — Fondo común (Fund) 📌 EN CONSTRUCCIÓN

← [Índice de módulos](_ROOT.md)

## Ficha

| Campo | Valor |
|---|---|
| Estado | 📌 En construcción (F4 de 6 del plan del fondo común) |
| Avance | F1 roles ✅ · F2 billetera ✅ · F3 libro y depósitos ✅ · **F4 agentes y liquidación ✅** · F5 retiros y comisiones · F6 portales y retiro de M10 |
| Madurez (estimada) | 65 % — ver [Avance](#avance) |
| Tablas | `fund_settings`, `ledger_entries`, `deposit_requests`, `agent_pools`, `agent_settlements`, `unit_lots`, `allocation_orders` (R/W); `platform_wallet`, `accounts` (R, [M4](M04-ACCOUNTS-PORTFOLIO.md)); `bots` ([M7](M07-BOTS-SIGNALS.md)), `fills`, `orders`, `positions` ([M8](M08-ORDERS-EXECUTION.md)), `symbols`, `users` (R) |
| Depende de | [M1](M01-AUTH.md) (roles super admin / socio / inversor), [M4](M04-ACCOUNTS-PORTFOLIO.md) (billetera de la plataforma y `WalletGateway`) |
| Lo usan | [M7](M07-BOTS-SIGNALS.md) (regla del 1 % sobre el capital del agente) y [M8](M08-ORDERS-EXECUTION.md) (drawdown del RiskGate) vía `FundCapitalPort`; F5 (retiros y comisiones); F6 (reemplaza a [M10](M10-BILLING.md)) |
| Prefijo API | `/api/fund/settings`, `/api/fund/deposits`, `/api/fund/me`, `/api/fund/participants`, `/api/fund/agents`, `/api/fund/allocations` |
| Frontend | `frontend/src/modules/fund` |
| Última revisión | 2026-10-23 |

## Descripción

**En palabras simples:** toda la plataforma usa una sola billetera de exchange para el dinero de todos (propietarios, socios e inversores). Este módulo lleva la cuenta de cuánto le corresponde a cada persona: un **libro mayor** donde cada movimiento queda escrito y nunca se edita. El dinero entra por **depósitos en USDT** que se verifican solos contra el exchange.

**Qué hace (F3):**
- Cada persona tiene dos saldos: **pendiente de asignar** (depósito confirmado que aún no pasó por un agente; no se retira) y **disponible** (viene de un agente o de comisiones; se retira — se llena desde la F4).
- **Depósitos verificados:** la persona ve la red y la dirección de la billetera, envía USDT y registra txid + monto. El scheduler busca el txid en los depósitos del exchange: si coincide y no supera el tope, se confirma solo; si no, queda **en revisión** para un super admin. Se acredita lo que reporta el exchange.
- **Depósitos sin reclamar:** los que entraron a la billetera sin solicitud; un super admin los asigna a su dueño con una nota.
- **Devolución excepcional** de saldo pendiente (super admin, con motivo).
- **Ajustes del fondo:** redes de depósito (dirección leída del exchange), tope de confirmación automática, vencimiento de solicitudes y permanencia mínima.

**Qué hace (F4):**
- **Agentes del fondo:** un super admin abre al fondo un agente que opera sobre la billetera con un par en USDT. Cada uno tiene un **pool**: equity exacta de su última liquidación y **unidades** en circulación; **NAV = equity ÷ unidades** (1 en la primera liquidación).
- **Asignar dinero:** un super admin pone en cola dinero de una persona (de su saldo pendiente o disponible) para un agente.
- **Liquidación:** con el agente pausado o detenido y sin posiciones ni órdenes abiertas, se calcula la equity exacta (ventas − compras − comisiones en USDT desde la anterior), el NAV, y se aplica la cola: cada asignación sale del saldo de la persona y se convierte en un **lote** de unidades al NAV. Vista previa antes de confirmar.
- **La regla del 1 % y el drawdown** de un agente del fondo usan **su** capital (equity liquidada + resultado desde entonces, con lo abierto a costo), no el saldo de la billetera. Un agente sobre la billetera sin pool no opera (capital 0).

## Páginas

Hash routing: la URL real es `/#/<ruta>`.

**Todos los roles (super admin, socio, inversor):**
- `/#/my-fund` — **Mi saldo** (menú Mi inversión): tarjetas Pendiente de asignar / Disponible / Total, instrucciones para depositar (red, dirección con botón de copiar, memo si aplica, aviso de usar la misma red), "Registrar depósito" (red, monto, txid), pestañas **Mis agentes** (F4: agente, estado, aportaste, vale hoy, resultado y fecha de la liquidación), **Mis depósitos** (estado, motivo de revisión o de rechazo, Anular si está pendiente) y **Movimientos** (libro). Desde la F4 también la tarjeta **En agentes** y el total con lo invertido.

**Staff (super admin y socio; el socio sin acciones):**
- `/#/admin/fund-agents` — **Agentes del fondo** (Administración → Fondo): agente, estado, valor de unidad, saldo liquidado, capital hoy, participantes, en cola y última liquidación; **Abrir agente al fondo**.
- `/#/admin/fund-agents/:poolId` — detalle: tarjetas (capital hoy, saldo liquidado, valor de unidad, participantes), pestañas Participantes (unidades, participación, aportó, vale), En cola (Cancelar) y Liquidaciones; **Asignar dinero** y **Liquidar** (vista previa: saldo anterior, resultado, NAV, quién entra, comisiones en otra moneda y lo que impide liquidar).
- `/#/admin/deposits` — **Depósitos** (Administración → Fondo): pestaña Solicitudes con filtros por estado (por defecto "En revisión") y persona, Confirmar (monto + nota) y Rechazar (motivo); pestaña **Sin reclamar** con Asignar; "Verificar ahora".
- `/#/admin/participants` — **Participantes**: cada persona con cuenta y sus saldos, totales del fondo, panel lateral de movimientos y "Devolver" (solo si tiene saldo pendiente).
- `/#/admin/fund-settings` — **Ajustes del fondo**: redes de depósito ("Cambiar redes": en live casillas con las redes del exchange; en práctica, red y dirección a mano) y reglas (permanencia mínima, tope de confirmación automática, vencimiento).

## Entregables

- ✅ (F3, 2026-10-23) Tablas `fund_settings`, `ledger_entries`, `deposit_requests` (migración `00abfeaac3b4`)
- ✅ Dominio: `FundSettings`, `DepositNetworkConfig`, `LedgerEntry`, `FundBalances`, `DepositRequest` (+ `normalize_txid`, `amounts_match`)
- ✅ Verificación automática por txid en el scheduler (`verify_fund_deposits`, después de sincronizar la billetera)
- ✅ Confirmar / rechazar / anular, depósitos sin reclamar y asignación, devolución excepcional
- ✅ Redes de depósito leídas del exchange (`fetch_deposit_networks`, `fetch_deposit_address`)
- ✅ REST `/api/fund/*` (18 endpoints) y páginas Mi saldo, Depósitos, Participantes y Ajustes del fondo
- ✅ (F4, 2026-10-23) Tablas `agent_pools`, `agent_settlements`, `unit_lots`, `allocation_orders` + CHECK de `ledger_entries` con `allocation` (migración `521b4d0aac1b`)
- ✅ Abrir un agente al fondo, cola de asignaciones, liquidación con vista previa y lotes; `FundCapitalPort` (1 % y drawdown sobre el capital del agente)
- ✅ Páginas Agentes del fondo (lista y detalle) y Mis agentes en Mi saldo
- ⏳ F5: retiros (banco/Nequi), comisión escalonada y reparto entre propietarios
- ⏳ F6: portales y conciliación; reemplazar M10

## Decisiones de diseño

| Decisión | Motivo | Alternativa descartada |
|---|---|---|
| **El participante es el usuario**: sin tabla `participants`; el tipo (propietario, socio, inversor) sale de su rol | Menos tablas y sin datos duplicados; el % de comisión de cada propietario llega en F5, donde se usa | Tabla `participants` desde la F3 |
| **Libro mayor append-only** con buckets `pending` / `available` y monto con signo; el saldo es la suma | Cada peso se puede explicar; una corrección es otro asiento, nunca una edición | Columna de saldo que se actualiza |
| Índice único `(entry_type, ref_type, ref_id)` en `ledger_entries` | La BD impide acreditar dos veces la misma solicitud aunque falle la lógica | Confiar solo en el servicio |
| **Confirmar = UPDATE condicional primero, asiento después** (`DepositCreditor`, `update_if_status`) | El scheduler y un super admin pueden resolver la misma solicitud a la vez: solo uno gana y solo ese acredita | Leer y escribir sin condición |
| **Se acredita lo del exchange** (`credited_amount`), no lo declarado; diferencia > 1 % → revisión | El exchange es la fuente de verdad del dinero que entró | Acreditar lo declarado |
| Tope de confirmación automática **1.000 USDT** y vencimiento **72 h** (decisión del usuario, 2026-10-23), configurables | Lo chico entra solo; lo grande lo mira una persona | Todo manual · todo automático |
| **txid único en todo el fondo** y normalizado (hex de Tron/EVM a minúsculas, también con prefijo `0X`; base58 tal cual) | Nadie reclama dos veces el mismo depósito ni el de otra persona | Comparar sin normalizar |
| En billetera live **la dirección de depósito se lee del exchange**; en práctica se escribe a mano | Un error de tipeo mandaría dinero a una dirección ajena | Escribirla a mano siempre |
| Confirmar sin respaldo del exchange (o con otro monto) exige **nota**; rechazar exige **motivo** | Queda escrito por qué se acreditó o no; la persona lo ve | Decisiones sin explicación |
| **Devolución** solo de saldo pendiente de asignar, con motivo | Regla de negocio: no se retira dinero que no pasó por un agente; la devolución es la excepción | Devolver cualquier saldo |
| El socio puede depositar y anular **su** solicitud (`read_only_policy.py`) | Es solo lectura sobre el sistema, pero también es participante | Socio sin dinero propio |
| Máximo 10 solicitudes abiertas por persona | Evita llenar la cola de verificación | Sin límite |
| **Unidades por agente (NAV) + lotes** | Quien entra paga el valor del momento y no se queda con ganancias de otros; cada lote guarda costo y fecha (comisión y permanencia en F5) | Repartir cada operación por porcentajes |
| **Entradas solo en liquidación** (agente pausado, sin posiciones ni órdenes) y equity por **flujo de caja** de los fills nuevos | Saldo exacto sin valorar posiciones abiertas (decisión del usuario, 2026-10-23) | Entrar con el agente corriendo y marcar a mercado |
| El pool arranca en el **último fill** del bot (`last_fill_id`) | Lo que el agente operó antes (pruebas) no se reparte a nadie | Contar toda la historia del bot |
| **`FundCapitalPort`** en el dominio de bots; lo implementa `AgentCapitalService` y lo inyectan los providers de bots y orders (import diferido) | El 1 % y el drawdown usan el capital del agente sin que bots/orders importen el módulo fund (sin ciclos) | Importar fund desde bots |
| Capital para el 1 % = equity liquidada + flujo desde entonces + lo abierto **a costo** | No depende del precio del momento; una pérdida reduce el tamaño de inmediato | Solo la equity liquidada (no ve las pérdidas) · marcar a mercado |
| Agente sobre la billetera **sin pool = capital 0** (decisión del usuario) | Nadie arriesga el dinero de todos por fuera de la contabilidad del fondo | Que use el saldo libre de la billetera |
| Comisiones en la moneda base del par no se restan (ya se reflejan en lo que se vende); en otra moneda (BNB) se informan sin valorar | Evita restar dos veces; lo no valorado queda visible | Valorar BNB a precio de mercado |
| Liquidación con **UPDATE condicional** del pool (`last_fill_id` y liquidación anterior esperados) | Dos liquidaciones simultáneas no suman dos veces el resultado | Bloqueo pesimista |
| Bloqueo **equity sin dueño** (unidades en 0 y resultado ≠ 0) | Una orden manual sobre un agente sin participantes no se reparte a quien entra | Repartirlo a los que entran |

## Avance

| Métrica | Valor | Evidencia |
|---|---|---|
| Alcance del plan | **F4 de 6** | Libro mayor, depósitos verificados, agentes del fondo y liquidación |
| Madurez | **≈ 65 %** | Funcionalidad 75 · Tests 30 · Seguridad 85 · Operación 70 |

- **Funcionalidad (75):** depósitos, libro y entradas a los agentes completos; faltan retiros (redimir unidades) y comisiones (F5).
- **Tests (30):** la lógica de dinero (verificación, carrera de confirmación, validaciones, devolución; F4: flujo de caja, plan de liquidación, capital del agente, bloqueos y conflicto) se verificó con dobles de prueba en scripts, sin archivo de test en `tests/`.
- **Seguridad (85):** UPDATE condicional + índice único contra doble acreditación, txid único, dirección leída del exchange, roles (staff ve, super admin decide, inversor solo lo suyo), sin saldo total de la billetera para el inversor.
- **Operación (65):** verificación automática en el scheduler; sin avisos (M9) al confirmar o rechazar.

## Posibles mejoras

| Prioridad | Mejora | Esfuerzo |
|---|---|---|
| Alta | Tests unitarios de `VerifyDepositsService`, `ResolveDepositRequestService`, `DepositCreditor`, `normalize_txid` | S |
| Media | Avisos por Telegram/correo ([M9](M09-ALERTS.md)): depósito confirmado / en revisión / rechazado; nuevos en revisión a los super admin (plan F5) | M |
| Media | Exportar el libro (CSV) por persona | S |
| Baja | Registrar direcciones de origen por persona para detectar envíos de terceros | M |

## Fuera de alcance y pendientes conocidos

- El bucket `available` se llena al redimir unidades (F5).
- Retiros, comisión escalonada y reparto (F5).
- Conciliación billetera ↔ libro y retiro de M10 (F6).
- Depósitos en fiat (solo USDT por blockchain).

## Detalle técnico

### Tablas en BD
| Tabla | Nota |
|---|---|
| `fund_settings` | Una fila (CHECK `id = 1`): `min_hold_days` (0–365, default 30), `deposit_auto_confirm_max` (DECIMAL, default 1000), `deposit_request_ttl_hours` (1–720, default 72), `deposit_networks` JSON `[{network, name, address, tag}]`, `updated_by_user_id` |
| `ledger_entries` | `user_id`, `entry_type` (CHECK `deposit`\|`refund`; F4/F5 lo amplían), `bucket` (`pending`\|`available`), `amount` con signo (CHECK ≠ 0), `asset`, `ref_type`/`ref_id` (UNIQUE con `entry_type`), `bot_id` (F4), `description`, `created_by_user_id` (NULL = sistema); índice `(user_id, created_at)` |
| `agent_pools` | `bot_id` (UNIQUE), `asset`, `equity`, `units` (≥ 0), `last_fill_id` (último fill contabilizado), `last_settlement_id` (sin FK), `created_by_user_id` |
| `agent_settlements` | `pool_id`, `bot_id`, `previous_equity`, `trading_result`, `equity_before`, `units_before`, `nav`, `allocated_amount`, `units_issued`, `equity_after`, `units_after`, `last_fill_id`, `fills_count`, `unvalued_fees` JSON, `note`, `settled_at`; índice `(pool_id, settled_at)` |
| `unit_lots` | `pool_id`, `user_id`, `units` (> 0), `units_remaining` (0 ≤ x ≤ units), `cost` (> 0), `nav_at_entry`, `settlement_id`, `acquired_at`; índices `(pool_id, acquired_at)` y `(user_id, acquired_at)` |
| `allocation_orders` | `pool_id`, `user_id`, `amount` (> 0), `source_bucket` (`pending`\|`available`), `status` (`queued`\|`applied`\|`canceled`), `note`, `settlement_id`, `created_by_user_id`, `resolved_at` |
| `deposit_requests` | `user_id`, `asset`, `network`, `txid` (UNIQUE), `declared_amount` (> 0), `credited_amount`, `address_from`, `exchange_deposit_id`, `exchange_status`, `status` (`pending`\|`review`\|`confirmed`\|`rejected`\|`expired`\|`canceled`), `review_reason` (`amount_mismatch`\|`over_threshold`\|`exchange_failed`\|`wrong_asset`), `resolved_by_user_id` (NULL en confirmación automática), `resolved_at`, `resolution_note`, `expires_at`; índices `(status, created_at)` y `(user_id, created_at)` |

### Código (`app/modules/fund/`)
| Capa | Archivos |
|---|---|
| domain | `fund_settings_entity.py`, `ledger_entry_entity.py`, `deposit_request_entity.py`, `agent_pool_entity.py` (F4), `settlement.py` (F4: `cash_flow`, `plan_settlement`, puros), `fund_repositories.py` (contratos) |
| infrastructure | `fund_models.py`, `fund_repositories_impl.py`, `agent_pool_models.py`, `agent_pool_repositories_impl.py` (fechas con `ensure_aware_utc`; `update_if_status` y `update_settled` condicionales) |
| services | `wallet_context.py` (billetera de M4) · `settings/` (`FundSettingsService`, `DepositNetworksService`) · `deposits/` (`CreateDepositRequestService`, `ResolveDepositRequestService`, `VerifyDepositsService`, `UnclaimedDepositsService`, `deposit_crediting.DepositCreditor`) · `ledger/` (`FundLedgerService`) · `pools/` (`AgentCapitalService` = `FundCapitalPort`, `AgentPoolsService`, `AllocationService`, `SettleAgentService`, `ParticipationsService`, `AgentInfoReader`) |
| providers | `fund_provider.py` → `FundServiceFactory` (usa repos de M1, M4, M7, M8 y `CcxtWalletGateway`) y `build_fund_capital(session)` para bots/orders |
| rest | `error_messages.py` (incluye los `WALLET_*` de M4), `schemas.py`, `serializers.py`, `settings/routes.py`, `deposits/routes.py`, `ledger/routes.py`, `pools/routes.py` |

Gateway ([M4](M04-ACCOUNTS-PORTFOLIO.md)): `WalletGateway.fetch_deposits`, `fetch_deposit_networks` (`fetch_currencies`), `fetch_deposit_address`. Scheduler: `verify_fund_deposits()` corre justo después de `sync_platform_wallet()` cada `WALLET_SYNC_INTERVAL_SECONDS`.

### Endpoints REST
| Método | Ruta | Auth | Nota |
|---|---|---|---|
| GET | `/api/fund/settings` | staff | Ajustes completos |
| PUT | `/api/fund/settings` | super admin | Permanencia, tope y vencimiento |
| GET | `/api/fund/settings/networks/available` | super admin | Redes del exchange (`is_live`) |
| PUT | `/api/fund/settings/networks` | super admin | En live la dirección se lee del exchange |
| GET | `/api/fund/deposits/info` | sesión | Moneda, redes con dirección y permanencia |
| POST | `/api/fund/deposits` | sesión (incl. socio) | `{network, txid, amount}`; 409 `FUND_DEPOSIT_TXID_TAKEN` / `FUND_DEPOSIT_TOO_MANY_OPEN` / `FUND_WALLET_NOT_CONFIGURED` |
| GET | `/api/fund/deposits` | sesión | Paginado; propias, o todas para el staff (`user_id`, `status`) |
| POST | `/api/fund/deposits/{id}/cancel` | dueño (incl. socio) | Solo `pending` |
| POST | `/api/fund/deposits/{id}/confirm` | super admin | `{amount?, note?}`; nota obligatoria sin respaldo del exchange |
| POST | `/api/fund/deposits/{id}/reject` | super admin | `{note}` |
| POST | `/api/fund/deposits/verify` | super admin | Resumen `{checked, confirmed, review, expired, waiting}` |
| GET | `/api/fund/deposits/unclaimed` | staff | Últimos 30 días, estado `ok`, sin solicitud |
| POST | `/api/fund/deposits/unclaimed/assign` | super admin | `{txid, user_id, note}` |
| GET | `/api/fund/me/balances` · `/api/fund/me/ledger` | sesión | Lo propio |
| GET | `/api/fund/participants` · `/api/fund/participants/{id}/ledger` | staff | |
| POST | `/api/fund/participants/{id}/refunds` | super admin | `{amount, reason}`; 409 `FUND_REFUND_EXCEEDS_PENDING` |
| GET | `/api/fund/agents` | staff | Pools con agente, capital estimado, cola, participantes |
| GET | `/api/fund/agents/eligible` | super admin | Agentes de la billetera con par en USDT y sin pool |
| POST | `/api/fund/agents` | super admin | `{bot_id}`; 422 `FUND_BOT_NOT_ON_WALLET` / `FUND_BOT_WRONG_QUOTE`, 409 `FUND_POOL_EXISTS` |
| GET | `/api/fund/agents/{pool_id}` | staff | + `participants_detail`, `queued`, `settlements` |
| POST | `/api/fund/agents/{pool_id}/allocations` | super admin | `{user_id, amount, source_bucket}`; 409 `FUND_ALLOCATION_EXCEEDS_BALANCE` |
| POST | `/api/fund/allocations/{id}/cancel` | super admin | Solo `queued` |
| GET | `/api/fund/agents/{pool_id}/settlement-preview` | staff | Plan + `blockers` y `blocker_messages` |
| POST | `/api/fund/agents/{pool_id}/settle` | super admin | `{note?}`; 409 con el primer bloqueo (`FUND_SETTLE_BOT_RUNNING` / `_OPEN_POSITIONS` / `_OPEN_ORDERS` / `_ORPHAN_EQUITY` / `_NEGATIVE_EQUITY`) o `FUND_SETTLE_CONFLICT` |
| GET | `/api/fund/me/participations` | sesión | En qué agentes está mi dinero y cuánto vale |

### Frontend (`frontend/src/modules/fund/`)
- `api/fund.api.ts`; `hooks/use-fund-queries.ts` (relee cada 60 s), `hooks/use-fund-mutations.ts`; `lib/fund-labels.ts`, `lib/fund-forms.ts`.
- Componentes: `copy-text`, `deposit-instructions`, `deposit-form-dialog`, `deposit-requests-table`, `ledger-table`, `deposit-decision-dialogs` (confirmar, rechazar, anular), `assign-unclaimed-dialog`, `refund-dialog`, `fund-settings-form`, `deposit-networks-dialog`.
- Páginas: `my-fund.tsx`, `admin-deposits.tsx`, `admin-participants.tsx`, `admin-fund-settings.tsx`, `admin-fund-agents.tsx`, `admin-fund-agent-detail.tsx`; rutas `routes/_app/my-fund.lazy.tsx`, `routes/_app/admin/{deposits,participants,fund-settings}.lazy.tsx` y `routes/_app/admin/fund-agents/{index,$poolId}.lazy.tsx`.
- F4: `hooks/use-fund-pools-queries.ts`, `hooks/use-fund-pools-mutations.ts`; componentes `open-pool-dialog`, `queue-allocation-dialog`, `settle-agent-dialog`, `participations-table`.

## Gotchas críticos

- **Billetera de práctica:** no hay exchange, así que los depósitos nunca se verifican solos (solo vencen): se confirman a mano con nota.
- **`ledger_entries.entry_type`** tiene CHECK con los tipos de la F3: al añadir tipos (F4/F5) hay que ampliar el CHECK a mano en la migración (autogenerate no detecta cambios de CHECK en tablas existentes).
- **Fechas:** MySQL devuelve `TIMESTAMP` sin zona; los repos del fondo y de la billetera las marcan como UTC (`ensure_aware_utc`) para compararlas con `utc_now()` y para que el front no las lea como hora local. El código anterior a la F2 serializa fechas sin zona (posible desfase de 5 h en la UI; pendiente de revisar).
- **Agentes de la billetera sin pool no generan señales** (`AGENT_NO_FUND_CAPITAL`): hay que abrirlos al fondo, asignarles dinero y liquidarlos una vez.
- **Órdenes manuales** sobre un agente del fondo cuentan en su resultado; sobre uno sin participantes bloquean la liquidación (equity sin dueño).
- **Comisión en la moneda base del par** (Binance sin BNB cobra la compra en BTC): la posición puede quedar con un residuo que bloquea la liquidación por "posición abierta".
- **Migraciones y FK:** en `downgrade()` no borrar con `drop_index` un índice que use una FK (MySQL 1553); borrar la tabla directamente.

## Tests

- Ajustado `tests/bots/test_generate_signal_service.py` (`analyze` recibe `capital`).
- Sin archivos en `tests/fund/`. Verificación manual con dobles de prueba (script fuera del repo): normalización de txid, confirmación automática, revisión por monto y por tope, vencimiento, carrera de confirmación, validaciones al crear, nota obligatoria y límite de la devolución.

## Riesgos

- Un txid reclamado por quien no envió el dinero: mitigado por la unicidad (el primero que lo registra) y por `address_from` visible para el super admin; para montos grandes, la revisión manual.
- Administrar dinero de terceros en un fondo común con comisión de desempeño es actividad regulada (SFC en Colombia); validarlo con un abogado antes de recibir dinero real de terceros.

## Historial

- **2026-10-22** — Plan del fondo común aprobado (6 fases). F1: roles super admin / socio / inversor ([M1](M01-AUTH.md)).
- **2026-10-23** — F2: billetera única de la plataforma ([M4](M04-ACCOUNTS-PORTFOLIO.md)).
- **2026-10-23** — **F3: módulo `fund`**: ajustes del fondo, libro mayor append-only, depósitos verificados contra el exchange (automático hasta 1.000 USDT, vencimiento 72 h), depósitos sin reclamar, devolución excepcional; páginas Mi saldo, Depósitos, Participantes y Ajustes del fondo (migración `00abfeaac3b4`).
- **2026-10-23** — **F4: agentes del fondo**: pools por agente con NAV y unidades, cola de asignaciones, liquidación con vista previa (agente pausado y sin posiciones, equity por flujo de caja, lotes, UPDATE condicional), `FundCapitalPort` para el 1 % y el drawdown (agente de la billetera sin pool = sin capital); páginas Agentes del fondo y Mis agentes (migración `521b4d0aac1b`).
