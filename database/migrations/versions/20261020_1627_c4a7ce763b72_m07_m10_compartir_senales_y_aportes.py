"""m07 m10 compartir señales y aportes

Revision ID: c4a7ce763b72
Revises: 3ac9fef574cb
Create Date: 2026-10-20 16:27:23.182204+00:00

MOTIVO:
- M7: un agente puede compartir sus señales (bots.share_signals, default 0)
  y otros usuarios lo siguen por Telegram (tabla signal_subscriptions,
  UNIQUE bot_id + user_id; se borran con el agente o el usuario).
- M10: aportes y retiros del inversor (tabla capital_movements, kind
  deposit | withdrawal, amount > 0); ajustan la marca de agua.
- `share_signals` se agrega a mano con AFTER approval_ttl_minutes (junto a
  la configuración del modo de ejecución); `op.add_column` no admite AFTER.
- El downgrade borra las tablas directamente: sus índices respaldan las
  FK y MySQL no deja borrarlos antes (se van con la tabla).
"""

from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = 'c4a7ce763b72'
down_revision: str | Sequence[str] | None = '3ac9fef574cb'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('signal_subscriptions',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('bot_id', sa.BigInteger(), nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('created_at', mysql.TIMESTAMP(fsp=6), server_default=sa.text('CURRENT_TIMESTAMP(6)'), nullable=False),
    sa.ForeignKeyConstraint(['bot_id'], ['bots.id'], name='fk_signal_subscriptions_bot', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_signal_subscriptions_user', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('bot_id', 'user_id', name='uq_signal_subscriptions_bot_user'),
    mysql_charset='utf8mb4',
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_engine='InnoDB'
    )
    op.create_index('idx_signal_subscriptions_user', 'signal_subscriptions', ['user_id'], unique=False)
    op.create_table('capital_movements',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('managed_account_id', sa.BigInteger(), nullable=False),
    sa.Column('kind', sa.String(length=16), nullable=False, comment='deposit | withdrawal'),
    sa.Column('amount', sa.Numeric(precision=30, scale=12), nullable=False),
    sa.Column('ts', mysql.TIMESTAMP(fsp=6), nullable=False, comment='Cuándo entró o salió el dinero'),
    sa.Column('notes', sa.String(length=500), nullable=True),
    sa.Column('created_by_user_id', sa.BigInteger(), nullable=True),
    sa.Column('created_at', mysql.TIMESTAMP(fsp=6), server_default=sa.text('CURRENT_TIMESTAMP(6)'), nullable=False),
    sa.CheckConstraint("`kind` IN ('deposit', 'withdrawal')", name='chk_capital_movements_kind'),
    sa.CheckConstraint('`amount` > 0', name='chk_capital_movements_amount'),
    sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], name='fk_capital_movements_created_by', ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['managed_account_id'], ['managed_accounts.id'], name='fk_capital_movements_managed_account'),
    sa.PrimaryKeyConstraint('id'),
    mysql_charset='utf8mb4',
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_engine='InnoDB'
    )
    op.create_index('idx_capital_movements_account_ts', 'capital_movements', ['managed_account_id', 'ts'], unique=False)
    op.execute(sa.text(
        "ALTER TABLE bots "
        "ADD COLUMN share_signals TINYINT(1) NOT NULL DEFAULT 0 "
        "COMMENT '1 = otros usuarios pueden suscribirse a sus señales (Telegram)' "
        "AFTER approval_ttl_minutes"
    ))


def downgrade() -> None:
    op.drop_column('bots', 'share_signals')
    op.drop_table('capital_movements')
    op.drop_table('signal_subscriptions')
