
"""m01 users notifications_seen_at

Revision ID: 45ba83355691
Revises: c4a7ce763b72
Create Date: 2026-10-20 16:55:17.502081+00:00

MOTIVO:
- M9 (campana de notificaciones): `users.notifications_seen_at`, última vez que la
  persona abrió sus notificaciones. NULL = nunca (todas sin leer). Se guarda en la
  cuenta para que el contador se limpie en todos los dispositivos.
"""

from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '45ba83355691'
down_revision: str | Sequence[str] | None = 'c4a7ce763b72'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # A mano para ubicarla tras las columnas de Telegram: op.add_column no admite AFTER
    op.execute(sa.text(
        "ALTER TABLE users "
        "ADD COLUMN notifications_seen_at TIMESTAMP(6) NULL "
        "COMMENT 'Última vez que el usuario abrió sus notificaciones; NULL = nunca (todas sin leer)' "
        "AFTER telegram_link_expires_at"
    ))


def downgrade() -> None:
    op.drop_column('users', 'notifications_seen_at')
