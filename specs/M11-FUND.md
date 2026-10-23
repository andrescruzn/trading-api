# Módulo 11 — Fondo común (Fund) 📌 EN CONSTRUCCIÓN

← [Índice de módulos](_ROOT.md)

## Ficha

| Campo | Valor |
|---|---|
| Estado | 📌 En construcción (F3 de 6 del plan del fondo común) |
| Avance | F1 roles ✅ · F2 billetera ✅ · **F3 libro y depósitos ✅** · F4 agentes y liquidación · F5 retiros y comisiones · F6 portales y retiro de M10 |
| Madurez (estimada) | 62 % — ver [Avance](#avance) |
| Tablas | `fund_settings`, `ledger_entries`, `deposit_requests` (R/W); `platform_wallet`, `accounts` (R, [M4](M04-ACCOUNTS-PORTFOLIO.md)); `users` (R) |
| Depende de | [M1](M01-AUTH.md) (roles super admin / socio / inversor), [M4](M04-ACCOUNTS-PORTFOLIO.md) (billetera de la plataforma y `WalletGateway`) |
| Lo usarán | F4 (asignación a agentes, [M7](M07-BOTS-SIGNALS.md)), F5 (retiros y comisiones), F6 (reemplaza a [M10](M10-BILLING.md)) |
| Prefijo API | `/api/fund/settings`, `/api/fund/deposits`, `/api/fund/me`, `/api/fund/participants` |
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

## Páginas

Hash routing: la URL real es `/#/<ruta>`.

**Todos los roles (super admin, socio, inversor):**
- `/#/my-fund` — **Mi saldo** (menú Mi inversión): tarjetas Pendiente de asignar / Disponible / Total, instrucciones para depositar (red, dirección con botón de copiar, memo si aplica, aviso de usar la misma red), "Registrar depósito" (red, monto, txid), pestañas **Mis depósitos** (estado, motivo de revisión o de rechazo, Anular si está pendiente) y **Movimientos** (libro).

**Staff (super admin y socio; el socio sin acciones):**
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
- ⏳ F4: asignación a agentes (lotes y unidades), 1 % sobre el capital del agente y liquidación
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

## Avance

| Métrica | Valor | Evidencia |
|---|---|---|
| Alcance del plan | **F3 de 6** | Libro mayor y depósitos verificados |
| Madurez | **≈ 62 %** | Funcionalidad 70 · Tests 30 · Seguridad 85 · Operación 65 |

- **Funcionalidad (70):** depósitos y libro completos; faltan asignación a agentes, retiros y comisiones (F4–F5).
- **Tests (30):** la lógica de dinero (verificación, carrera de confirmación, validaciones, devolución) se verificó con dobles de prueba en un script, sin archivo de test en `tests/`.
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

- Asignación a agentes, liquidación y el bucket `available` (F4).
- Retiros, comisión escalonada y reparto (F5).
- Conciliación billetera ↔ libro y retiro de M10 (F6).
- Depósitos en fiat (solo USDT por blockchain).

## Detalle técnico

### Tablas en BD
| Tabla | Nota |
|---|---|
| `fund_settings` | Una fila (CHECK `id = 1`): `min_hold_days` (0–365, default 30), `deposit_auto_confirm_max` (DECIMAL, default 1000), `deposit_request_ttl_hours` (1–720, default 72), `deposit_networks` JSON `[{network, name, address, tag}]`, `updated_by_user_id` |
| `ledger_entries` | `user_id`, `entry_type` (CHECK `deposit`\|`refund`; F4/F5 lo amplían), `bucket` (`pending`\|`available`), `amount` con signo (CHECK ≠ 0), `asset`, `ref_type`/`ref_id` (UNIQUE con `entry_type`), `bot_id` (F4), `description`, `created_by_user_id` (NULL = sistema); índice `(user_id, created_at)` |
| `deposit_requests` | `user_id`, `asset`, `network`, `txid` (UNIQUE), `declared_amount` (> 0), `credited_amount`, `address_from`, `exchange_deposit_id`, `exchange_status`, `status` (`pending`\|`review`\|`confirmed`\|`rejected`\|`expired`\|`canceled`), `review_reason` (`amount_mismatch`\|`over_threshold`\|`exchange_failed`\|`wrong_asset`), `resolved_by_user_id` (NULL en confirmación automática), `resolved_at`, `resolution_note`, `expires_at`; índices `(status, created_at)` y `(user_id, created_at)` |

### Código (`app/modules/fund/`)
| Capa | Archivos |
|---|---|
| domain | `fund_settings_entity.py`, `ledger_entry_entity.py`, `deposit_request_entity.py`, `fund_repositories.py` (contratos) |
| infrastructure | `fund_models.py`, `fund_repositories_impl.py` (fechas con `ensure_aware_utc`; `update_if_status` condicional) |
| services | `wallet_context.py` (billetera de M4) · `settings/` (`FundSettingsService`, `DepositNetworksService`) · `deposits/` (`CreateDepositRequestService`, `ResolveDepositRequestService`, `VerifyDepositsService`, `UnclaimedDepositsService`, `deposit_crediting.DepositCreditor`) · `ledger/` (`FundLedgerService`) |
| providers | `fund_provider.py` → `FundServiceFactory` (usa repos de M4 y M1 y `CcxtWalletGateway`) |
| rest | `error_messages.py` (incluye los `WALLET_*` de M4), `schemas.py`, `serializers.py`, `settings/routes.py`, `deposits/routes.py`, `ledger/routes.py` |

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

### Frontend (`frontend/src/modules/fund/`)
- `api/fund.api.ts`; `hooks/use-fund-queries.ts` (relee cada 60 s), `hooks/use-fund-mutations.ts`; `lib/fund-labels.ts`, `lib/fund-forms.ts`.
- Componentes: `copy-text`, `deposit-instructions`, `deposit-form-dialog`, `deposit-requests-table`, `ledger-table`, `deposit-decision-dialogs` (confirmar, rechazar, anular), `assign-unclaimed-dialog`, `refund-dialog`, `fund-settings-form`, `deposit-networks-dialog`.
- Páginas: `my-fund.tsx`, `admin-deposits.tsx`, `admin-participants.tsx`, `admin-fund-settings.tsx`; rutas `routes/_app/my-fund.lazy.tsx` y `routes/_app/admin/{deposits,participants,fund-settings}.lazy.tsx`.

## Gotchas críticos

- **Billetera de práctica:** no hay exchange, así que los depósitos nunca se verifican solos (solo vencen): se confirman a mano con nota.
- **`ledger_entries.entry_type`** tiene CHECK con los tipos de la F3: al añadir tipos (F4/F5) hay que ampliar el CHECK a mano en la migración (autogenerate no detecta cambios de CHECK en tablas existentes).
- **Fechas:** MySQL devuelve `TIMESTAMP` sin zona; los repos del fondo y de la billetera las marcan como UTC (`ensure_aware_utc`) para compararlas con `utc_now()` y para que el front no las lea como hora local. El código anterior a la F2 serializa fechas sin zona (posible desfase de 5 h en la UI; pendiente de revisar).
- **Migraciones y FK:** en `downgrade()` no borrar con `drop_index` un índice que use una FK (MySQL 1553); borrar la tabla directamente.

## Tests

- Sin archivos en `tests/fund/`. Verificación manual con dobles de prueba (script fuera del repo): normalización de txid, confirmación automática, revisión por monto y por tope, vencimiento, carrera de confirmación, validaciones al crear, nota obligatoria y límite de la devolución.

## Riesgos

- Un txid reclamado por quien no envió el dinero: mitigado por la unicidad (el primero que lo registra) y por `address_from` visible para el super admin; para montos grandes, la revisión manual.
- Administrar dinero de terceros en un fondo común con comisión de desempeño es actividad regulada (SFC en Colombia); validarlo con un abogado antes de recibir dinero real de terceros.

## Historial

- **2026-10-22** — Plan del fondo común aprobado (6 fases). F1: roles super admin / socio / inversor ([M1](M01-AUTH.md)).
- **2026-10-23** — F2: billetera única de la plataforma ([M4](M04-ACCOUNTS-PORTFOLIO.md)).
- **2026-10-23** — **F3: módulo `fund`**: ajustes del fondo, libro mayor append-only, depósitos verificados contra el exchange (automático hasta 1.000 USDT, vencimiento 72 h), depósitos sin reclamar, devolución excepcional; páginas Mi saldo, Depósitos, Participantes y Ajustes del fondo (migración `00abfeaac3b4`).
