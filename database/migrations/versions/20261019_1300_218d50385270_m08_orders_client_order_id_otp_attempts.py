"""m08 orders client_order_id and otp failed attempts

Revision ID: 218d50385270
Revises: a4e81c5d27f9
Create Date: 2026-10-19 13:00:00.000000+00:00

MOTIVO (auditoría de seguridad 2026-10-19):
- M8: orders.client_order_id VARCHAR(64) NULL + UNIQUE. Es el
  `clientOrderId` ("ta-{id}") que se envía al exchange: idempotencia y
  forma de encontrar la orden si la respuesta se pierde por red. NULL en
  las órdenes anteriores (y varios NULL no chocan con el UNIQUE).
- M1: users.otp_failed_attempts INT NOT NULL DEFAULT 0. Intentos fallidos
  del código vigente; al llegar a OTP_MAX_FAILED_ATTEMPTS se invalida. El
  rate limit en memoria no basta con varios workers.
- Escrita a mano para dejar cada columna junto a las de su grupo (AFTER);
  `op.add_column` no admite AFTER.
- El downgrade quita el UNIQUE y las dos columnas (se pierde ese dato).
"""

from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '218d50385270'
down_revision: str | Sequence[str] | None = 'a4e81c5d27f9'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(sa.text(
        "ALTER TABLE orders "
        "ADD COLUMN client_order_id VARCHAR(64) NULL AFTER exchange_order_id, "
        "ADD CONSTRAINT uq_orders_client_order_id UNIQUE (client_order_id)"
    ))
    op.execute(sa.text(
        "ALTER TABLE users "
        "ADD COLUMN otp_failed_attempts INT NOT NULL DEFAULT 0 AFTER otp_expires_at"
    ))


def downgrade() -> None:
    op.drop_column('users', 'otp_failed_attempts')
    op.drop_constraint('uq_orders_client_order_id', 'orders', type_='unique')
    op.drop_column('orders', 'client_order_id')
