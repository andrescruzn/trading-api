---
name: database
description: Base de datos MySQL 8 de Trading AI API (base trading_ai). Usar antes de escribir SQL, seeds, migraciones o modelos ORM, o cuando haga falta consultar el esquema, una tabla, una columna o un ENUM. Cubre dónde está el esquema, resumen de tablas por dominio, valores permitidos de los CHECK, convenciones de columnas, comandos de MySQL (MAMP en macOS / Windows) y gotchas de SQLAlchemy.
---

# Base de datos — MySQL 8 (`trading_ai`)

## Dónde está el esquema

El esquema lo definen los **modelos ORM** (`app/modules/*/infrastructure/*_model.py`, registrados en `app/extensions/db/models_registry.py`) y se aplica con las **revisiones de Alembic** en [`alembic/versions/`](../../../alembic/versions/). No hay dump ni `.sql` de referencia.

- Una tabla concreta: leer su modelo (`grep -rn '__tablename__ = "<tabla>"' app`), que declara columnas, índices, FKs y CHECKs.
- DDL completo sin tocar la BD: `uv run alembic upgrade head --sql` (modo offline, solo imprime el SQL).
- Fuente última de verdad: la BD local, `SHOW CREATE TABLE <tabla>;`.

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

Todo cambio de esquema es una **revisión de Alembic** en `alembic/versions/`; nunca SQL suelto.

- Config: `alembic.ini` (sin URL) + `alembic/env.py`, que reutiliza `engine` de `app.extensions.db` (URL de `.env`, sesión en UTC) y `Base.metadata` vía `models_registry`.
- `0001_baseline` es una revisión vacía (punto de partida). El esquema completo (29 tablas) lo crea la revisión **generada con `--autogenerate` desde los modelos**, que le sigue.
- **Los modelos son la fuente del esquema**: cada uno declara exactamente lo que hay en MySQL (tipos, defaults, comentarios, índices, FKs, CHECKs y opciones de tabla). Ver "Modelos y Alembic" abajo.
- `env.py` ignora las tablas que existen en la BD sin modelo ORM (hoy solo `http_audit_YYYY`, que se crean en runtime), así autogenerate no propone borrarlas.

### Flujo para un cambio de esquema

1. Crear o modificar el modelo en `infrastructure/<x>_model.py` (y registrarlo en `models_registry.py` si es nuevo), siguiendo "Modelos y Alembic".
2. El usuario genera la revisión: `uv run alembic revision --autogenerate -m "m11 crear tabla x"`. El mensaje empieza por el módulo (`mNN`).
3. **Revisar y editar el archivo generado siempre.** En tablas **nuevas** autogenerate incluye CHECKs, comentarios y defaults del modelo. En tablas **existentes** no detecta CHECKs añadidos/quitados ni cambios de `server_default`: añadirlos a mano (`op.create_check_constraint(...)`, `op.alter_column(..., server_default=...)`). Completar `MOTIVO:` en el docstring y revisar que `downgrade()` sea correcto.
4. El usuario aplica: `uv run alembic upgrade head`, y luego `uv run alembic check` debe responder `No new upgrade operations detected`.

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
uv run alembic stamp head                              # marcar una BD que ya tiene el esquema, sin ejecutar nada
```

- **BD nueva desde cero:** `alembic upgrade head` y luego `python -m seeds`.
- **BD que ya tenía el esquema** (creada con el dump antes de Alembic): `alembic stamp head`, sin `upgrade`.

## Seeds

Los seeds son módulos Python en `seeds/`, uno por dominio, y se ejecutan con el runner (los ejecuta el usuario: escriben en la BD):

```bash
uv run python -m seeds                      # todos, en orden de dependencias
uv run python -m seeds roles market_data    # solo los indicados
uv run python -m seeds --list               # ver los disponibles
```

| Seed | Contenido |
|---|---|
| `roles` | user / admin / investor con los IDs de `settings.AUTH_*_ROLE_ID` |
| `market_data` | 7 exchanges, 14 timeframes, 24 símbolos |
| `strategies` | 6 estrategias de ejemplo |
| `accounts` | 2 cuentas paper con balances para el usuario demo (se omite si el usuario no existe) |

Reglas para un seed nuevo:
- Archivo `seeds/<dominio>.py` con `def run(session: Session) -> SeedStats`, registrado en `SEEDS` de `seeds/__main__.py` respetando el orden de dependencias.
- **Idempotente:** insertar con `get_or_create(session, Model, lookup={clave natural}, values={...}, stats=stats)` de `seeds/_helpers.py`. Busca por clave natural y nunca actualiza filas existentes. No depender de `INSERT IGNORE`: si la tabla no tiene `UNIQUE` sobre esa clave, duplica.
- Usar los modelos ORM y enlazar por nombre (exchange por `name`, usuario por `email`), nunca por IDs fijos. La excepción son los roles, que salen de `settings`.
- El seed no hace commit: el runner confirma uno por seed con `SqlAlchemyRepository.commit()` y hace rollback si falla.

## Comandos MySQL

Credenciales locales en `.env` (`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`). El binario no suele estar en el PATH:

```bash
# macOS (MAMP)
MYSQL=/Applications/MAMP/Library/bin/mysql80/bin/mysql
# Windows (Git Bash) — ajustar a la instalación local
MYSQL="/c/Program Files/MySQL/MySQL Server 8.0/bin/mysql.exe"

"$MYSQL" -u root -p trading_ai < archivo.sql                     # ejecutar archivo
"$MYSQL" -u root -p trading_ai -e "SELECT COUNT(*) FROM candles;" # query directa
"$MYSQL" -u root -p trading_ai                                    # shell interactivo
```

El warning `Using a password on the command line interface can be insecure` es esperado.

## ORM (SQLAlchemy 2, síncrono)

- Modelos solo en `infrastructure/<x>_model.py`, heredan de `app.extensions.db.base.Base`, y se registran en `app/extensions/db/models_registry.py` (si no, las relaciones/FK fallan al arrancar).
- Estilo de los modelos existentes: `Column(...)` clásico (no `Mapped`/`mapped_column`); seguirlo por consistencia.
- Las tablas se crean con revisiones de Alembic, nunca con `create_all`.

### Modelos y Alembic (el modelo debe describir la tabla real)

Ejemplo de referencia: `app/modules/agent/infrastructure/prediction_model.py`.

- Fechas: `from sqlalchemy.dialects.mysql import TIMESTAMP` → `TIMESTAMP(fsp=6)`. **Nunca** `sqlalchemy.TIMESTAMP(6)`: ahí el primer argumento es `timezone`, sale `TIMESTAMP` sin precisión y MySQL rechaza el `DEFAULT CURRENT_TIMESTAMP(6)` (error 1067).
- `updated_at`: `server_default=text("CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)")`.
- Defaults de BD con `server_default=text("'1'")`, `text("'0.000000000000'")`… (el `default=` de Python no llega al DDL).
- Nada de `index=True` / `unique=True` en `Column` (generan nombres `ix_*`). Todo con nombre en `__table_args__`: `Index("idx_<tabla>_<cols>", ...)`, `UniqueConstraint(..., name="uq_...")`, `CheckConstraint("`col` IN ('a', 'b')", name="chk_...")`. FKs con `ForeignKey("t.id", name="fk_...", ondelete=...)`.
- No declarar un índice solo para una FK: MySQL lo crea con el nombre de la FK.
- Comentarios de columna con `comment="..."`.
- `__table_args__` termina siempre con `MYSQL_TABLE_OPTIONS` (de `app.extensions.db`): InnoDB, utf8mb4, utf8mb4_0900_ai_ci.
- Columnas `DECIMAL` llegan como `Decimal` de Python; convertir explícitamente si se opera con `float`.
- Queries siempre parametrizadas (ORM o `text()` con `:param`), nunca f-strings con input.
- `session.commit()` solo dentro de la capa repositorio (base `SqlAlchemyRepository`); el servicio llama `repo.commit()` (ver `backend-core`).
