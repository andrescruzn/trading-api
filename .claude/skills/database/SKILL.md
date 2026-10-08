---
name: database
description: Base de datos MySQL 8 de Trading AI API (base trading_ai). Usar antes de escribir SQL, seeds, migraciones o modelos ORM, o cuando haga falta consultar el esquema, una tabla, una columna o un ENUM. Cubre dónde está el esquema, resumen de tablas por dominio, valores permitidos de los CHECK, convenciones de columnas, comandos de MySQL (MAMP en macOS / Windows) y gotchas de SQLAlchemy.
---

# Base de datos — MySQL 8 (`trading_ai`)

## Dónde está el esquema

El esquema real = **[`.claude/db_schema.sql`](../../db_schema.sql)** (dump del 2026-02-24, 25 tablas) **+ las migraciones legacy en [`migrations/`](../../../migrations/)** **+ las revisiones de Alembic en [`alembic/versions/`](../../../alembic/versions/)** (posteriores a `0001_baseline`):

| Migración legacy (congelada) | Estado en el dump |
|---|---|
| `m07_add_signal_price_columns.sql` (entry/SL/TP/size/rr/approved en `signals`) | ✅ incluida |
| `m07b_add_bot_feature_set_id.sql` (`bots.feature_set_id`) | ✅ incluida |
| `m10_billing.sql` (`investors`, `managed_accounts`, `billing_periods`, `fee_transactions`) | ❌ **no** está en el dump: leer la migración |

Para ver una tabla concreta, buscar `CREATE TABLE \`<tabla>\`` en esos archivos con Grep en vez de leer el dump entero (~38 KB). La fuente última de verdad es la BD local: `SHOW CREATE TABLE <tabla>;`.

## Tablas por dominio

| Dominio | Tablas |
|---|---|
| Catálogos | `roles` (1 user, 2 admin, 3 investor), `exchanges`, `symbols`, `timeframes`, `feature_sets`, `strategies` |
| Usuarios y cuentas | `users`, `accounts`, `account_balances` |
| Market data / ML | `candles`, `candle_features`, `datasets`, `models`, `model_runs` |
| Ejecución de bots | `bots`, `signals`, `orders`, `fills`, `positions`, `predictions`, `portfolio_snapshots` |
| Alertas y auditoría | `alert_rules`, `alert_events`, `audit_logs`, `system_events` |
| Billing (M10) | `investors`, `managed_accounts`, `billing_periods`, `fee_transactions` |

## Valores permitidos (CHECK constraints)

```
accounts.mode              : paper | live
accounts.status            : active | suspended
bots.mode                  : paper | live
bots.status                : running | stopped | paused | error
orders.side                : buy | sell
orders.type                : market | limit | stop | stop_limit
orders.status              : new | sent | partially_filled | filled | canceled | rejected
signals.action             : buy | sell | hold
models.model_type          : xgboost | lightgbm | sklearn | nn
models.status              : active | deprecated | archived
model_runs.status          : running | success | failed
symbols.asset_class        : crypto | metal | etf | stock | forex
exchanges.type             : crypto_exchange | broker | data_vendor
users.status               : active | blocked | disabled
alert_rules.rule_type      : pnl | drawdown | signal | error | price
alert_events.severity      : info | warning | critical
alert_events.delivery_status: pending | sent | failed
system_events.level        : info | warning | error
system_events.component    : market_data | execution | scheduler | api
managed_accounts.period_type: daily | weekly | monthly
billing_periods.status     : open | closed
fee_transactions.status    : pending | charged | waived
```

Otras restricciones que suelen morder:
- `orders`: `market` → `price` y `stop_price` NULL; `limit` → `price` NOT NULL, `stop_price` NULL; `stop`/`stop_limit` → `stop_price` NOT NULL. `qty > 0`.
- `positions.qty >= 0` (solo largos), único por `(bot_id, symbol_id)`.
- `candles`: único por `(symbol_id, timeframe_id, ts)`, `high >= low`.
- `signals.confidence` entre 0 y 1.

## Convenciones para tablas nuevas

- Motor `InnoDB`, charset `utf8mb4`, collation `utf8mb4_0900_ai_ci`.
- IDs `BIGINT AUTO_INCREMENT` (excepción histórica: `timeframes.id` es `SMALLINT`).
- Fechas `TIMESTAMP(6)`; `created_at DEFAULT CURRENT_TIMESTAMP(6)`, `updated_at ... ON UPDATE CURRENT_TIMESTAMP(6)`. La sesión MySQL trabaja en UTC.
- Precios, cantidades, balances: `DECIMAL(30,12)`. Porcentajes: `DECIMAL(5,4)`.
- Datos flexibles en columnas `JSON` (`meta`, `spec`, `params`, `payload`, `reasons`) con `CHECK (json_valid(col))`.
- ENUMs como `VARCHAR` + `CHECK (col IN (...))`, nombrado `chk_<tabla>_<col>`; índices `idx_<tabla>_<cols>`, FKs `fk_<tabla>_<ref>`, únicos `uq_<tabla>_<cols>`.

## Migraciones con Alembic

Todo cambio de esquema nuevo es una **revisión de Alembic** en `alembic/versions/`. La carpeta `migrations/` (`mNN_*.sql`) es **legacy y está congelada**: no se añaden archivos ahí.

- Config: `alembic.ini` (sin URL) + `alembic/env.py`, que reutiliza `engine` de `app.extensions.db` (URL de `.env`, sesión en UTC) y `Base.metadata` vía `models_registry`.
- `0001_baseline` es una revisión vacía que representa el esquema previo (dump + `migrations/*.sql` hasta `m10`). Una BD existente se marca con `stamp`, no con `upgrade`.
- `env.py` ignora las tablas que existen en la BD sin modelo ORM (`audit_logs`, `system_events`, `predictions`, `portfolio_snapshots`, `http_audit_YYYY`), así autogenerate no propone borrarlas. Para gestionar una de ellas con Alembic, primero crearle su modelo.

### Flujo para un cambio de esquema

1. Crear o modificar el modelo en `infrastructure/<x>_model.py` (y registrarlo en `models_registry.py` si es nuevo).
2. El usuario genera la revisión: `uv run alembic revision --autogenerate -m "m11 crear tabla x"`. El mensaje empieza por el módulo (`mNN`).
3. **Revisar y editar el archivo generado siempre.** Autogenerate no detecta `CHECK`, ENUMs vía `CHECK`, comentarios ni cambios de `server_default`, y puede proponer índices o FKs con otros nombres si el modelo no declara el mismo nombre que la BD (`idx_…`, `fk_…`, `uq_…`). Añadir a mano con `op.create_check_constraint(...)` / `op.execute(...)` lo que falte, completar `MOTIVO:` en el docstring y escribir un `downgrade()` real.
4. El usuario aplica: `uv run alembic upgrade head`.
5. Recordar que `.claude/db_schema.sql` queda desactualizado (regenerarlo con `mysqldump --no-data`).

Para tablas nuevas, declarar en el modelo los nombres reales de índices y constraints (`Index("idx_x_y", ...)`, `ForeignKey(..., name="fk_x_y")`, `UniqueConstraint(..., name="uq_x_y")`) y `mysql_engine` / `mysql_charset` / `mysql_collate` en `__table_args__`, para que la revisión generada siga las convenciones de arriba.

### Comandos (los ejecuta el usuario: escriben o leen su BD)

```bash
uv run alembic current                                 # revisión aplicada en la BD
uv run alembic history --verbose                       # lista de revisiones
uv run alembic check                                   # ¿hay diferencias modelos ↔ BD? (no escribe)
uv run alembic revision --autogenerate -m "mNN ..."    # generar revisión desde los modelos
uv run alembic revision -m "mNN ..."                   # revisión vacía (SQL/datos a mano)
uv run alembic upgrade head                            # aplicar pendientes
uv run alembic upgrade head --sql                      # solo imprimir el SQL, sin ejecutar
uv run alembic downgrade -1                            # deshacer la última
uv run alembic stamp 0001_baseline                     # marcar una BD existente sin ejecutar nada
```

**BD nueva desde cero:** cargar `.claude/db_schema.sql` + `migrations/m10_billing.sql` + seeds, luego `alembic stamp 0001_baseline` y `alembic upgrade head`.

## Seeds

- **Seed:** `seeds/seed_<modulo>.sql`, **idempotente** (`INSERT IGNORE` o `ON DUPLICATE KEY UPDATE`), referencias por nombre con subqueries (`SELECT id FROM exchanges WHERE name = 'Binance'`), nunca IDs hardcodeados salvo `roles`.
- Seeds existentes: `seed_market_data.sql` (exchanges, timeframes, symbols), `seed_accounts.sql`, `seed_strategies.sql`, `seed_billing.sql` (rol investor).

## Comandos MySQL

Credenciales locales en `.env` (`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`). El binario no suele estar en el PATH:

```bash
# macOS (MAMP)
MYSQL=/Applications/MAMP/Library/bin/mysql80/bin/mysql
# Windows (Git Bash) — ajustar a la instalación local
MYSQL="/c/Program Files/MySQL/MySQL Server 8.0/bin/mysql.exe"

"$MYSQL" -u root -p trading_ai < seeds/seed_billing.sql          # ejecutar archivo
"$MYSQL" -u root -p trading_ai -e "SELECT COUNT(*) FROM candles;" # query directa
"$MYSQL" -u root -p trading_ai                                    # shell interactivo
```

El warning `Using a password on the command line interface can be insecure` es esperado.

## ORM (SQLAlchemy 2, síncrono)

- Modelos solo en `infrastructure/<x>_model.py`, heredan de `app.extensions.db.base.Base`, y se registran en `app/extensions/db/models_registry.py` (si no, las relaciones/FK fallan al arrancar).
- Estilo de los modelos existentes: `Column(...)` clásico (no `Mapped`/`mapped_column`); seguirlo por consistencia.
- Las tablas se crean con revisiones de Alembic, nunca con `create_all`. Si se genera DDL desde código (como `app/common/audit/audit_table_factory.py`), usar `sqlalchemy.dialects.mysql.TIMESTAMP(fsp=6)`: en el `TIMESTAMP` genérico el primer argumento es `timezone`, no la precisión.
- Columnas `DECIMAL` llegan como `Decimal` de Python; convertir explícitamente si se opera con `float`.
- Queries siempre parametrizadas (ORM o `text()` con `:param`), nunca f-strings con input.
- `session.commit()` solo dentro de la capa repositorio (base `SqlAlchemyRepository`); el servicio llama `repo.commit()` (ver `backend-core`).
