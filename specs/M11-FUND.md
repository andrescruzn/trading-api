# Módulo 11 — Fondo común (Fund) 📌 EN CONSTRUCCIÓN

← [Índice de módulos](_ROOT.md)

## Ficha

| Campo | Valor |
|---|---|
| Estado | 📌 En construcción (F5 de 6 del plan del fondo común) |
| Avance | F1 roles ✅ · F2 billetera ✅ · F3 libro y depósitos ✅ · F4 agentes y liquidación ✅ · **F5 salidas, comisión y retiros ✅** · F6 portales y retiro de M10 |
| Madurez (estimada) | 70 % — ver [Avance](#avance) |
| Tablas | `fund_settings`, `ledger_entries`, `deposit_requests`, `agent_pools`, `agent_settlements`, `unit_lots`, `allocation_orders`, `fee_schedules`, `commission_share_versions`, `redemption_requests`, `settlement_redemptions`, `commission_credits`, `payout_methods`, `withdrawal_requests` (R/W); `platform_wallet`, `accounts` (R, [M4](M04-ACCOUNTS-PORTFOLIO.md)); `bots` ([M7](M07-BOTS-SIGNALS.md)), `fills`, `orders`, `positions` ([M8](M08-ORDERS-EXECUTION.md)), `symbols`, `users` (R) |
| Depende de | [M1](M01-AUTH.md) (roles super admin / socio / inversor), [M4](M04-ACCOUNTS-PORTFOLIO.md) (billetera de la plataforma y `WalletGateway`) |
| Lo usan | [M7](M07-BOTS-SIGNALS.md) (regla del 1 % sobre el capital del agente) y [M8](M08-ORDERS-EXECUTION.md) (drawdown del RiskGate) vía `FundCapitalPort`; F6 (reemplaza a [M10](M10-BILLING.md)) |
| Prefijo API | `/api/fund/settings`, `/api/fund/deposits`, `/api/fund/me`, `/api/fund/participants`, `/api/fund/agents`, `/api/fund/allocations`, `/api/fund/redemptions`, `/api/fund/fees`, `/api/fund/commission-shares`, `/api/fund/commissions`, `/api/fund/withdrawals` |
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

**Qué hace (F5):**
- **Sacar dinero de un agente:** cada persona pide una salida (un monto o "todo"). Queda en cola y se aplica en la **próxima liquidación**, al NAV de ese momento. Salen primero los lotes más antiguos (FIFO) y solo los que cumplen la **permanencia mínima**; si no alcanza, sale lo que cumple y el resto sigue en el agente (queda informado como pendiente).
- **Comisión escalonada** (versionada, pública para todos): cada tramo de retorno paga su % solo sobre la parte de la ganancia que cae en él, como los impuestos. Se cobra sobre la ganancia de los lotes que salen (valor − costo); con pérdida, 0. El capital propio de los propietarios paga igual.
- **Reparto de la comisión** entre super admin y socios según % versionados que suman 100 %; el residuo del redondeo va al de menor id. Cada parte entra al **disponible** de quien la recibe.
- **Retiros:** del disponible libre (disponible − retiros por pagar − asignaciones en cola desde el disponible), a un **medio de pago** propio (banco o Nequi, datos cifrados) que se puede usar **48 h** después de registrarlo. Un super admin paga por fuera y registra COP, tasa y referencia; el asiento `withdrawal` descuenta el saldo al pagar. También puede rechazar con motivo; la persona anula mientras está por pagar.

## Páginas

Hash routing: la URL real es `/#/<ruta>`.

**Todos los roles (super admin, socio, inversor):**
- `/#/my-fund` — **Mi saldo** (menú Mi inversión): tarjetas Pendiente de asignar / Disponible / Total, instrucciones para depositar (red, dirección con botón de copiar, memo si aplica, aviso de usar la misma red), "Registrar depósito" (red, monto, txid), pestañas **Mis agentes** (F4: agente, estado, aportaste, vale hoy, resultado y fecha de la liquidación; F5: **Sacar dinero**, salidas en cola con Anular y "Lo que salió de tus agentes" con la comisión tramo por tramo), **Retiros** (F5: mis retiros con Anular y mis medios de pago con Agregar / Quitar), **Comisión** (F5: tabla vigente y, si la persona recibe comisión, el total recibido), **Mis depósitos** (estado, motivo de revisión o de rechazo, Anular si está pendiente) y **Movimientos** (libro). Desde la F4 también la tarjeta **En agentes** y el total con lo invertido. F5: botón **Retirar** (habilitado si hay saldo retirable) y la tarjeta Disponible muestra lo reservado en retiros por pagar.

**Staff (super admin y socio; el socio sin acciones):**
- `/#/admin/fund-agents` — **Agentes del fondo** (Administración → Fondo): agente, estado, valor de unidad, saldo liquidado, capital hoy, participantes, en cola y última liquidación; **Abrir agente al fondo**.
- `/#/admin/fund-agents/:poolId` — detalle: tarjetas (capital hoy, saldo liquidado, valor de unidad, participantes), pestañas Participantes (unidades, participación, aportó, vale), En cola (Cancelar), **Salidas en cola** (F5, Anular) y Liquidaciones (F5: salió y comisión); **Asignar dinero** y **Liquidar** (vista previa: saldo anterior, resultado, NAV, quién sale con valor, comisión, neto y desglose, salidas que esperan la permanencia, quién entra, comisiones en otra moneda y lo que impide liquidar).
- `/#/admin/withdrawals` — **Retiros** (F5, Administración → Fondo): filtros por estado (por defecto "Por pagar") y persona; **Pagar** (datos completos del medio de pago con copiar, tasa, pesos con sugerencia, referencia, nota) y **Rechazar** (motivo).
- `/#/admin/commissions` — **Comisiones** (F5): tabla de comisión (Publicar / Cambiar, hasta 10 tramos), reparto entre super admin y socios (Definir / Cambiar, suma 100 %) y comisiones recibidas por persona.
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
- ✅ (F5, 2026-10-23) Tablas `fee_schedules`, `commission_share_versions`, `redemption_requests`, `settlement_redemptions`, `commission_credits`, `payout_methods`, `withdrawal_requests`; columnas `redeemed_amount`, `units_redeemed`, `fees_total` en `agent_settlements`; CHECK de `ledger_entries` con `redemption`, `fee`, `commission`, `withdrawal` (migración `a159e69da372`)
- ✅ Dominio puro `commission.py` (`tiered_fee`, `split_commission`, `valid_tiers`, `valid_shares`) y salidas en `plan_settlement` (FIFO + permanencia)
- ✅ Salidas en cola aplicadas en la liquidación, comisión escalonada versionada, reparto versionado, medios de pago cifrados con espera de 48 h, retiros con pago manual (COP, tasa, referencia)
- ✅ Páginas Retiros y Comisiones; Mi saldo con Retirar, Sacar dinero, Retiros y Comisión
- ⏳ Comprobante del pago como archivo (hoy referencia + nota; decisión del usuario: F6)
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
| **Comisión escalonada marginal** por tramos de retorno (ganancia ÷ costo del lote) | Ganar más nunca deja menos neto; se cobra sobre el costo de cada lote, así recuperar pérdidas no se cobra dos veces (equivale a la marca de agua) | Un solo % según el tramo alcanzado (salto) |
| Tabla de comisión y reparto **versionados**: cada cambio es una fila nueva y cada línea de salida guarda `fee_schedule_id` y `commission_version_id` | Cambiar la tabla no reescribe lo cobrado | Editar la tabla vigente |
| Salidas solo en liquidación; sale lo que cumple la permanencia y **el resto se queda** (decisión del usuario, 2026-10-23) | Saldo exacto sin romper la regla de permanencia; la persona ve lo pendiente | Rechazar la salida entera · esperar a que todo cumpla |
| Liquidar con salidas exige tabla de comisión y, si alguna paga comisión, reparto (`FUND_SETTLE_NO_FEE_SCHEDULE` / `_NO_COMMISSION_SHARES`) | Nadie sale sin que se le cobre lo acordado | Cobrar 0 si falta la tabla |
| Residuo del reparto al **de menor id** | La suma de las partes es exactamente la comisión | Perder centavos |
| Retiro: **el dinero se reserva al pedir** (disponible libre) y **sale del libro al pagar** (asiento `withdrawal`) | Un rechazo o una anulación no necesitan asiento de vuelta; no se puede pedir dos veces lo mismo | Asiento al pedir y contra-asiento al rechazar |
| Medios de pago **cifrados** (`CredentialsCipher.encrypt_dict`) y **48 h de espera** (`PAYOUT_METHOD_COOLDOWN_HOURS`); solo un super admin ve los datos completos y solo al pagar | Si alguien toma una sesión, no puede desviar un retiro a su cuenta de inmediato | Datos en claro · sin espera |
| Sin doble aprobación de retiros por ahora (decisión del usuario) | Son dos propietarios; se puede añadir con un umbral | Doble firma desde el inicio |
| Comprobante = **referencia + nota** (decisión del usuario); archivo en F6 | Sin almacenamiento de archivos todavía | Subir el comprobante ya |
| El socio puede pedir salidas y retiros **suyos** y gestionar sus medios de pago (`read_only_policy.py`) | Solo lectura sobre el sistema, pero también es participante | Socio sin dinero propio |

## Avance

| Métrica | Valor | Evidencia |
|---|---|---|
| Alcance del plan | **F5 de 6** | Libro mayor, depósitos verificados, agentes del fondo, liquidación, salidas, comisión escalonada y retiros |
| Madurez | **≈ 70 %** | Funcionalidad 85 · Tests 30 · Seguridad 85 · Operación 70 |

- **Funcionalidad (85):** el ciclo completo del dinero funciona: depósito → asignación → liquidación → salida con comisión → retiro pagado. Falta la F6: portal de propietarios, conciliación, comprobante como archivo, avisos y quitar M10.
- **Tests (30):** la lógica de dinero (verificación, carrera de confirmación, validaciones, devolución; F4: flujo de caja, plan de liquidación, capital del agente, bloqueos y conflicto; F5: tramos, pérdida, límites, reparto con residuo, FIFO con permanencia, retiros y espera del medio de pago) se verificó con dobles de prueba en scripts, sin archivo de test en `tests/`.
- **Seguridad (85):** UPDATE condicional + índice único contra doble acreditación, txid único, dirección leída del exchange, roles (staff ve, super admin decide, inversor solo lo suyo), sin saldo total de la billetera para el inversor.
- **Operación (70):** verificación automática en el scheduler; las salidas y los retiros esperan a que un super admin liquide o pague (sin avisos M9 todavía).

## Posibles mejoras

| Prioridad | Mejora | Esfuerzo |
|---|---|---|
| Alta | Tests unitarios de `tiered_fee`, `split_commission`, `plan_settlement` con salidas, `WithdrawalService`, `VerifyDepositsService`, `DepositCreditor`, `normalize_txid` | M |
| Media | Avisos por Telegram/correo ([M9](M09-ALERTS.md)): depósito confirmado / en revisión / rechazado, liquidación hecha, retiro pedido (a los super admin) y retiro pagado o rechazado (F6) | M |
| Media | Doble aprobación de retiros sobre un umbral (los dos super admin) | M |
| Baja | Calendario de liquidaciones (p. ej. el día 1 de cada mes) visible para los inversores | S |
| Media | Exportar el libro (CSV) por persona | S |
| Baja | Registrar direcciones de origen por persona para detectar envíos de terceros | M |

## Fuera de alcance y pendientes conocidos

- Conciliación billetera ↔ libro, portal de propietarios, comprobante como archivo y retiro de M10 (F6).
- Depósitos en fiat (solo USDT por blockchain).

## Detalle técnico

### Tablas en BD
| Tabla | Nota |
|---|---|
| `fund_settings` | Una fila (CHECK `id = 1`): `min_hold_days` (0–365, default 30), `deposit_auto_confirm_max` (DECIMAL, default 1000), `deposit_request_ttl_hours` (1–720, default 72), `deposit_networks` JSON `[{network, name, address, tag}]`, `updated_by_user_id` |
| `ledger_entries` | `user_id`, `entry_type` (CHECK `deposit`\|`refund`\|`allocation`\|`redemption`\|`fee`\|`commission`\|`withdrawal`), `bucket` (`pending`\|`available`), `amount` con signo (CHECK ≠ 0), `asset`, `ref_type`/`ref_id` (UNIQUE con `entry_type`), `bot_id` (F4), `description`, `created_by_user_id` (NULL = sistema); índice `(user_id, created_at)` |
| `agent_pools` | `bot_id` (UNIQUE), `asset`, `equity`, `units` (≥ 0), `last_fill_id` (último fill contabilizado), `last_settlement_id` (sin FK), `created_by_user_id` |
| `agent_settlements` | `pool_id`, `bot_id`, `previous_equity`, `trading_result`, `equity_before`, `units_before`, `nav`, `allocated_amount`, `units_issued`, `equity_after`, `units_after`, `last_fill_id`, `fills_count`, `unvalued_fees` JSON, `note`, `settled_at`; índice `(pool_id, settled_at)` |
| `unit_lots` | `pool_id`, `user_id`, `units` (> 0), `units_remaining` (0 ≤ x ≤ units), `cost` (> 0), `nav_at_entry`, `settlement_id`, `acquired_at`; índices `(pool_id, acquired_at)` y `(user_id, acquired_at)` |
| `allocation_orders` | `pool_id`, `user_id`, `amount` (> 0), `source_bucket` (`pending`\|`available`), `status` (`queued`\|`applied`\|`canceled`), `note`, `settlement_id`, `created_by_user_id`, `resolved_at` |
| `agent_settlements` (F5) | + `redeemed_amount`, `units_redeemed`, `fees_total` (default 0) |
| `fee_schedules` | `tiers` JSON `[{from_return, rate}]` en fracción (el primero desde 0, crecientes, tasa 0–1, máx. 10), `note`, `created_by_user_id`; la vigente es la última |
| `commission_share_versions` | `shares` JSON `[{user_id, pct}]` en fracción (suman 1, solo super admin y socios), `note`; la vigente es la última |
| `redemption_requests` | `pool_id`, `user_id`, `amount` (NULL = todo; > 0), `status` (`queued`\|`applied`\|`canceled`), `note`, `settlement_id`, `created_by_user_id`, `resolved_at`; una en cola por persona y agente |
| `settlement_redemptions` | Lo que salió: `units`, `value`, `cost`, `gain`, `return_pct` (fracción), `fee`, `net`, `pending_amount`, `fee_schedule_id`, `commission_version_id`, `breakdown` JSON por tramo |
| `commission_credits` | `settlement_redemption_id`, `user_id`, `amount` (> 0): la parte de cada propietario |
| `payout_methods` | `user_id`, `kind` (`bank`\|`nequi`), `label`, `masked`, `enc_details` (Fernet), `usable_from` (creación + 48 h), `is_active`; máx. 5 activos |
| `withdrawal_requests` | `user_id`, `amount` (> 0), `payout_method_id`, `status` (`requested`\|`paid`\|`rejected`\|`canceled`), `paid_cop_amount`, `cop_rate`, `payment_reference`, `resolution_note`, `resolved_by_user_id`, `resolved_at`; máx. 5 abiertos por persona |
| `deposit_requests` | `user_id`, `asset`, `network`, `txid` (UNIQUE), `declared_amount` (> 0), `credited_amount`, `address_from`, `exchange_deposit_id`, `exchange_status`, `status` (`pending`\|`review`\|`confirmed`\|`rejected`\|`expired`\|`canceled`), `review_reason` (`amount_mismatch`\|`over_threshold`\|`exchange_failed`\|`wrong_asset`), `resolved_by_user_id` (NULL en confirmación automática), `resolved_at`, `resolution_note`, `expires_at`; índices `(status, created_at)` y `(user_id, created_at)` |

### Código (`app/modules/fund/`)
| Capa | Archivos |
|---|---|
| domain | `fund_settings_entity.py`, `ledger_entry_entity.py`, `deposit_request_entity.py`, `agent_pool_entity.py` (F4), `settlement.py` (F4: `cash_flow`, `plan_settlement`, puros; F5: `waiting_redemptions`, salidas FIFO), `commission.py` (F5: `tiered_fee`, `split_commission`), `withdrawal_entity.py` (F5: `PayoutMethod`, `WithdrawalRequest`, `mask_payout`), `fund_repositories.py`, `payout_repositories.py` (contratos) |
| infrastructure | `fund_models.py`, `fund_repositories_impl.py`, `agent_pool_models.py`, `agent_pool_repositories_impl.py`, `payout_models.py`, `payout_repositories_impl.py` (F5; `UnitLotRepository.consume` condicional) (fechas con `ensure_aware_utc`; `update_if_status` y `update_settled` condicionales) |
| services | `wallet_context.py` (billetera de M4) · `settings/` (`FundSettingsService`, `DepositNetworksService`) · `deposits/` (`CreateDepositRequestService`, `ResolveDepositRequestService`, `VerifyDepositsService`, `UnclaimedDepositsService`, `deposit_crediting.DepositCreditor`) · `ledger/` (`FundLedgerService`) · `pools/` (`AgentCapitalService` = `FundCapitalPort`, `AgentPoolsService`, `AllocationService`, `SettleAgentService`, `ParticipationsService`, `AgentInfoReader`, F5: `RedemptionService`) · `fees/` (F5: `FeeScheduleService`, `CommissionSharesService`) · `payouts/` (F5: `PayoutMethodsService`, `WithdrawalService`) |
| providers | `fund_provider.py` → `FundServiceFactory` (usa repos de M1, M4, M7, M8 y `CcxtWalletGateway`) y `build_fund_capital(session)` para bots/orders |
| rest | `error_messages.py` (incluye los `WALLET_*` de M4), `schemas.py`, `serializers.py`, `settings/routes.py`, `deposits/routes.py`, `ledger/routes.py`, `pools/routes.py`, `fees/routes.py` (F5), `payouts/routes.py` (F5) |

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
| POST | `/api/fund/redemptions` | sesión (incl. socio) | `{pool_id, amount?}` (sin monto = todo); un super admin puede mandar `user_id`; 409 `FUND_REDEMPTION_NO_UNITS` / `_ALREADY_QUEUED` |
| POST | `/api/fund/redemptions/{id}/cancel` | dueño o super admin | Solo `queued` |
| GET | `/api/fund/me/redemptions` | sesión | `{queued, history, lines, agents}` (`agents` = `pool_id` → agente) |
| GET | `/api/fund/fees` | sesión | Tabla vigente (porcentajes en %) |
| GET | `/api/fund/fees/history` | staff | Versiones |
| POST | `/api/fund/fees` | super admin | `{tiers: [{from_return_pct, rate_pct}], note?}`; 422 `FUND_FEE_INVALID_TIERS` |
| GET | `/api/fund/commission-shares` | staff | `{current, history}` |
| PUT | `/api/fund/commission-shares` | super admin | `{shares: [{user_id, pct}], note?}`; 422 `FUND_SHARES_INVALID` / `FUND_SHARES_NOT_OWNER` |
| GET | `/api/fund/commissions` | staff | Comisiones recibidas por persona |
| GET | `/api/fund/me/commissions` | sesión | Mis comisiones recibidas |
| GET · POST | `/api/fund/me/payout-methods` | sesión (incl. socio) | Enmascarados · crear `{kind, label, holder_name, document_number, bank_name/account_type/account_number o phone}` |
| POST | `/api/fund/me/payout-methods/{id}/deactivate` | dueño | |
| GET | `/api/fund/me/withdrawable` | sesión | Disponible libre |
| POST | `/api/fund/withdrawals` | sesión (incl. socio) | `{amount, payout_method_id}`; 409 `FUND_PAYOUT_COOLING_DOWN` / `FUND_WITHDRAWAL_EXCEEDS_AVAILABLE` / `_TOO_MANY_OPEN` |
| GET | `/api/fund/withdrawals` | sesión | Paginado; propios, o todos para el staff (`user_id`, `status`) |
| POST | `/api/fund/withdrawals/{id}/cancel` | dueño (incl. socio) | Solo `requested` |
| GET | `/api/fund/withdrawals/{id}/payout-details` | super admin | Datos descifrados del medio de pago |
| POST | `/api/fund/withdrawals/{id}/pay` | super admin | `{paid_cop_amount, cop_rate, payment_reference, note?}` → asiento `withdrawal` |
| POST | `/api/fund/withdrawals/{id}/reject` | super admin | `{note}` |

### Frontend (`frontend/src/modules/fund/`)
- `api/fund.api.ts`; `hooks/use-fund-queries.ts` (relee cada 60 s), `hooks/use-fund-mutations.ts`; `lib/fund-labels.ts`, `lib/fund-forms.ts`.
- Componentes: `copy-text`, `deposit-instructions`, `deposit-form-dialog`, `deposit-requests-table`, `ledger-table`, `deposit-decision-dialogs` (confirmar, rechazar, anular), `assign-unclaimed-dialog`, `refund-dialog`, `fund-settings-form`, `deposit-networks-dialog`.
- Páginas: `my-fund.tsx`, `admin-deposits.tsx`, `admin-participants.tsx`, `admin-fund-settings.tsx`, `admin-fund-agents.tsx`, `admin-fund-agent-detail.tsx`; rutas `routes/_app/my-fund.lazy.tsx`, `routes/_app/admin/{deposits,participants,fund-settings}.lazy.tsx` y `routes/_app/admin/fund-agents/{index,$poolId}.lazy.tsx`.
- F4: `hooks/use-fund-pools-queries.ts`, `hooks/use-fund-pools-mutations.ts`; componentes `open-pool-dialog`, `queue-allocation-dialog`, `settle-agent-dialog`, `participations-table`.
- F5: `api/fund-payouts.api.ts`, `hooks/use-fund-payouts-queries.ts` (los datos del medio de pago con `gcTime: 0`), `hooks/use-fund-payouts-mutations.ts`, `lib/fund-payouts-labels.ts`; componentes `redemption-dialog`, `redemptions-tables`, `fee-tables`, `fee-schedule-dialog`, `commission-shares-dialog`, `payout-method-dialog`, `payout-methods-table`, `withdrawal-dialog`, `withdrawals-table`, `withdrawal-decision-dialogs` (pagar, rechazar, anular); páginas `admin-withdrawals.tsx`, `admin-commissions.tsx` (rutas `routes/_app/admin/{withdrawals,commissions}.lazy.tsx`).

## Gotchas críticos

- **Billetera de práctica:** no hay exchange, así que los depósitos nunca se verifican solos (solo vencen): se confirman a mano con nota.
- **`ledger_entries.entry_type`** tiene CHECK con los tipos de la F3: al añadir tipos (F4/F5) hay que ampliar el CHECK a mano en la migración (autogenerate no detecta cambios de CHECK en tablas existentes).
- **Fechas:** MySQL devuelve `TIMESTAMP` sin zona; los repos del fondo y de la billetera las marcan como UTC (`ensure_aware_utc`) para compararlas con `utc_now()` y para que el front no las lea como hora local. El código anterior a la F2 serializa fechas sin zona (posible desfase de 5 h en la UI; pendiente de revisar).
- **Agentes de la billetera sin pool no generan señales** (`AGENT_NO_FUND_CAPITAL`): hay que abrirlos al fondo, asignarles dinero y liquidarlos una vez.
- **Órdenes manuales** sobre un agente del fondo cuentan en su resultado; sobre uno sin participantes bloquean la liquidación (equity sin dueño).
- **Comisión en la moneda base del par** (Binance sin BNB cobra la compra en BTC): la posición puede quedar con un residuo que bloquea la liquidación por "posición abierta".
- **Porcentajes en la API:** la BD guarda fracciones (0,5 = 50 %); la API los manda en % con `_pct`, que usa `format(..., "f")` porque `Decimal.normalize()` deja exponentes (`2E+2`) que la UI no entiende.
- **Liquidar con salidas en cola sin tabla de comisión o sin reparto** queda bloqueado: primero publicar ambos en Comisiones.
- **Medio de pago nuevo:** 48 h sin poder usarlo; conviene registrarlo antes de pedir la salida.
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
- **2026-10-23** — **F5: salidas, comisión y retiros**: salidas en cola aplicadas en la liquidación (FIFO + permanencia, lo demás se queda), comisión escalonada marginal versionada, reparto versionado entre super admin y socios (residuo al de menor id), medios de pago cifrados con 48 h de espera, retiros pagados por fuera (COP, tasa, referencia); páginas Retiros y Comisiones y Mi saldo con Retirar / Sacar dinero (migración `a159e69da372`).
- **2026-10-23** — **F4: agentes del fondo**: pools por agente con NAV y unidades, cola de asignaciones, liquidación con vista previa (agente pausado y sin posiciones, equity por flujo de caja, lotes, UPDATE condicional), `FundCapitalPort` para el 1 % y el drawdown (agente de la billetera sin pool = sin capital); páginas Agentes del fondo y Mis agentes (migración `521b4d0aac1b`).
