"""m08 futuros live y funding

Revision ID: b7d4e2a91c63
Revises: 3e1b7c9d2a54
Create Date: 2026-10-26 14:00:00.000000+00:00

MOTIVO:
- M8: los perpetuos de Binance (metales, materias primas, ETFs, acciones) se
  operan en live: solo largos, 1x y margen aislado. Binance cobra o paga
  funding cada pocas horas sobre la posición abierta; no es un fill, pero
  mueve dinero.
  - `funding_payments`: cada cobro/pago (con signo), por agente, cuenta y
    símbolo; UNIQUE (cuenta, id del exchange) para no duplicar al releer.
- M11: el funding entra al flujo de caja del agente del fondo.
  - `agent_pools.last_funding_id`: último funding contabilizado (como
    `last_fill_id`; lo anterior a abrir el pool no cuenta).
  - `agent_settlements.funding_total`: funding incluido en el resultado.
- downgrade: borra la tabla y las dos columnas.
"""

from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = 'b7d4e2a91c63'
down_revision: str | Sequence[str] | None = '3e1b7c9d2a54'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('funding_payments',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('bot_id', sa.BigInteger(), nullable=False),
    sa.Column('account_id', sa.BigInteger(), nullable=False),
    sa.Column('symbol_id', sa.BigInteger(), nullable=False),
    sa.Column('amount', sa.DECIMAL(precision=30, scale=12), nullable=False, comment='Con signo: + recibido, − pagado'),
    sa.Column('asset', sa.String(length=32), nullable=False, comment='Moneda del funding (USDT)'),
    sa.Column('exchange_funding_id', sa.String(length=64), nullable=False, comment='Id del registro en Binance'),
    sa.Column('ts', mysql.TIMESTAMP(fsp=6), nullable=False, comment='Cuándo lo liquidó el exchange'),
    sa.Column('created_at', mysql.TIMESTAMP(fsp=6), server_default=sa.text('CURRENT_TIMESTAMP(6)'), nullable=False),
    sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], name='fk_funding_payments_account'),
    sa.ForeignKeyConstraint(['bot_id'], ['bots.id'], name='fk_funding_payments_bot'),
    sa.ForeignKeyConstraint(['symbol_id'], ['symbols.id'], name='fk_funding_payments_symbol'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('account_id', 'exchange_funding_id', name='uq_funding_payments_account_exchange_id'),
    mysql_charset='utf8mb4',
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_engine='InnoDB'
    )
    op.create_index('idx_funding_payments_bot_ts', 'funding_payments', ['bot_id', 'ts'], unique=False)

    op.add_column('agent_pools', sa.Column(
        'last_funding_id', sa.BigInteger(), server_default=sa.text("'0'"), nullable=False,
        comment='Último funding (perpetuos) ya contabilizado'))
    op.add_column('agent_settlements', sa.Column(
        'funding_total', sa.DECIMAL(precision=30, scale=12),
        server_default=sa.text("'0.000000000000'"), nullable=False,
        comment='Funding de perpetuos incluido en el resultado'))


def downgrade() -> None:
    op.drop_column('agent_settlements', 'funding_total')
    op.drop_column('agent_pools', 'last_funding_id')
    # La tabla se borra entera (con sus índices y FK): ver gotcha de MySQL 1553
    op.drop_table('funding_payments')
