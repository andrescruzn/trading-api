"""m02 solo binance

Revision ID: 9869015f140f
Revises: ff5577d3faef
Create Date: 2026-10-26 12:00:00.000000+00:00

MOTIVO:
- La plataforma opera con un solo exchange: Binance (spot y perpetuos
  USDⓈ-M). Cuentas y símbolos nuevos se enlazan siempre a él
  (`PLATFORM_EXCHANGE_NAME`) y ya no se crean ni editan exchanges.
- Solo datos, sin cambios de esquema:
  - asegura la fila `Binance` (la BD puede venir sin el seed);
  - desactiva los demás exchanges (Bybit, Kraken, Coinbase, Bitget, OKX,
    TradingView) y sus símbolos, sin borrar historia (velas, agentes y
    órdenes que los usaron siguen enlazados);
  - pasa todas las cuentas a Binance (también las de práctica y las que
    no tenían exchange).
- downgrade: reactiva los demás exchanges y sus símbolos. El exchange
  anterior de cada cuenta no se guarda, así que las cuentas quedan en
  Binance.
"""

from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '9869015f140f'
down_revision: str | Sequence[str] | None = 'ff5577d3faef'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_PLATFORM = 'Binance'
_OTHER_EXCHANGES = f"SELECT id FROM exchanges WHERE name <> '{_PLATFORM}'"


def upgrade() -> None:
    # UNIQUE(name): si ya existe, no hace nada
    op.execute(sa.text(
        f"INSERT IGNORE INTO exchanges (name, type, is_active) "
        f"VALUES ('{_PLATFORM}', 'crypto_exchange', 1)"
    ))
    op.execute(sa.text(f"UPDATE exchanges SET is_active = (name = '{_PLATFORM}')"))

    # Los subqueries leen `exchanges`, no la tabla que se actualiza: MySQL lo permite
    op.execute(sa.text(f"UPDATE symbols SET is_active = 0 WHERE exchange_id IN ({_OTHER_EXCHANGES})"))
    op.execute(sa.text(
        f"UPDATE accounts SET exchange_id = "
        f"(SELECT id FROM exchanges WHERE name = '{_PLATFORM}')"
    ))


def downgrade() -> None:
    # Los de TradingView ya estaban desactivados desde 7d1f3a6b9e20
    op.execute(sa.text(
        f"UPDATE symbols SET is_active = 1 WHERE exchange_id IN "
        f"({_OTHER_EXCHANGES} AND name <> 'TradingView')"
    ))
    op.execute(sa.text("UPDATE exchanges SET is_active = 1"))
