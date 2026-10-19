"""m08 positions native stop order

Revision ID: 3ac9fef574cb
Revises: f51e2dad9c13
Create Date: 2026-10-19 15:00:00.000000+00:00

MOTIVO:
- M8: en live, el stop loss de una posición abierta desde una señal queda
  como orden nativa en el exchange (protege aunque la API o el scheduler
  estén caídos). positions.sl_order_id BIGINT NULL (FK orders) apunta a
  esa orden; NULL = la protección la vigila el scheduler (paper, o un
  exchange sin stop loss nativo).
- Escrita a mano para dejar la columna junto a la protección (AFTER
  signal_id); `op.add_column` no admite AFTER.
- El downgrade quita la FK, su índice y la columna.
"""

from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '3ac9fef574cb'
down_revision: str | Sequence[str] | None = 'f51e2dad9c13'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(sa.text(
        "ALTER TABLE positions "
        "ADD COLUMN sl_order_id BIGINT NULL "
        "COMMENT 'Orden stop loss nativa en el exchange (live)' AFTER signal_id, "
        "ADD CONSTRAINT fk_positions_sl_order FOREIGN KEY (sl_order_id) REFERENCES orders (id)"
    ))


def downgrade() -> None:
    op.execute(sa.text("ALTER TABLE positions DROP FOREIGN KEY fk_positions_sl_order"))
    op.execute(sa.text(
        "ALTER TABLE positions DROP INDEX fk_positions_sl_order, DROP COLUMN sl_order_id"
    ))
