"""m11 retiros entre billeteras

Revision ID: 3e1b7c9d2a54
Revises: 9869015f140f
Create Date: 2026-10-26 13:00:00.000000+00:00

MOTIVO:
- Fondo común: por temas legales ya no se paga a cuentas bancarias ni a
  Nequi. Los retiros se envían desde la billetera de Binance a una dirección
  cripto de la persona (red + dirección + memo), y la comisión de red la
  paga ella.
  - `payout_methods.kind` admite `crypto`. `bank` y `nequi` quedan en el
    CHECK solo para las filas viejas, que se desactivan (autogenerate no
    detecta cambios de CHECK: va a mano).
  - `withdrawal_requests`: fuera `paid_cop_amount`, `cop_rate` y
    `payment_reference` (pago en pesos); entran `txid` (UNIQUE), `network`,
    `sent_amount`, `network_fee` y `exchange_withdrawal_id`.
  - Datos: los retiros `requested` que apuntaban a un banco o a Nequi se
    anulan con una nota (la persona vuelve a pedirlos a una dirección). Los
    pagados conservan su asiento en el libro, pero pierden el monto en COP,
    la tasa y la referencia (decisión del usuario: BD de desarrollo).
- downgrade: vuelve a las columnas de COP (vacías) y al CHECK sin `crypto`;
  antes borra los medios `crypto`, sus retiros, comprobantes y asientos
  `withdrawal` (no caben en el esquema anterior; solo para desarrollo).
"""

from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '3e1b7c9d2a54'
down_revision: str | Sequence[str] | None = '9869015f140f'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_KIND_CHECK = 'chk_payout_methods_kind'
_LEGACY = "('bank', 'nequi')"
_CANCEL_NOTE = (
    'Anulado: los retiros ya no se pagan a bancos ni a Nequi. '
    'Registra una dirección cripto y pide el retiro de nuevo.'
)


def upgrade() -> None:
    # ---- payout_methods: dirección cripto ----
    op.drop_constraint(_KIND_CHECK, 'payout_methods', type_='check')
    op.create_check_constraint(_KIND_CHECK, 'payout_methods', "`kind` IN ('bank', 'nequi', 'crypto')")
    op.alter_column(
        'payout_methods', 'kind',
        existing_type=sa.String(length=16), existing_nullable=False,
        comment='crypto (bank | nequi: históricos)',
        existing_comment='bank | nequi',
    )
    op.alter_column(
        'payout_methods', 'enc_details',
        existing_type=sa.Text(), existing_nullable=False,
        comment='Red, dirección y memo cifrados (Fernet)',
        existing_comment='Datos bancarios cifrados (Fernet)',
    )

    # ---- datos: fuera los bancos y Nequi ----
    op.execute(sa.text(
        "UPDATE withdrawal_requests SET status = 'canceled', resolved_at = CURRENT_TIMESTAMP(6), "
        "resolution_note = :note WHERE status = 'requested' AND payout_method_id IN "
        f"(SELECT id FROM payout_methods WHERE kind IN {_LEGACY})"
    ).bindparams(note=_CANCEL_NOTE))
    op.execute(sa.text(f"UPDATE payout_methods SET is_active = 0 WHERE kind IN {_LEGACY}"))

    # ---- withdrawal_requests: datos del envío ----
    op.drop_column('withdrawal_requests', 'paid_cop_amount')
    op.drop_column('withdrawal_requests', 'cop_rate')
    op.drop_column('withdrawal_requests', 'payment_reference')
    op.add_column('withdrawal_requests', sa.Column(
        'txid', sa.String(length=128), nullable=True,
        comment='Hash (o id interno de Binance) del envío'))
    op.add_column('withdrawal_requests', sa.Column(
        'network', sa.String(length=32), nullable=True, comment='Red por la que se envió'))
    op.add_column('withdrawal_requests', sa.Column(
        'sent_amount', sa.DECIMAL(precision=30, scale=12), nullable=True,
        comment='Lo que recibió el destino'))
    op.add_column('withdrawal_requests', sa.Column(
        'network_fee', sa.DECIMAL(precision=30, scale=12), nullable=True,
        comment='Comisión de red (la paga la persona)'))
    op.add_column('withdrawal_requests', sa.Column(
        'exchange_withdrawal_id', sa.String(length=64), nullable=True,
        comment='Id del retiro en Binance'))
    op.create_unique_constraint('uq_withdrawal_requests_txid', 'withdrawal_requests', ['txid'])


def downgrade() -> None:
    # Lo cripto no cabe en el esquema anterior: comprobantes, retiros y medios
    op.execute(sa.text(
        "DELETE FROM withdrawal_receipts WHERE withdrawal_request_id IN "
        "(SELECT id FROM withdrawal_requests WHERE payout_method_id IN "
        "(SELECT id FROM payout_methods WHERE kind = 'crypto'))"
    ))
    op.execute(sa.text(
        "DELETE FROM ledger_entries WHERE entry_type = 'withdrawal' "
        "AND ref_type = 'withdrawal_request' AND ref_id IN "
        "(SELECT id FROM withdrawal_requests WHERE payout_method_id IN "
        "(SELECT id FROM payout_methods WHERE kind = 'crypto'))"
    ))
    op.execute(sa.text(
        "DELETE FROM withdrawal_requests WHERE payout_method_id IN "
        "(SELECT id FROM payout_methods WHERE kind = 'crypto')"
    ))
    op.execute(sa.text("DELETE FROM payout_methods WHERE kind = 'crypto'"))

    op.drop_constraint('uq_withdrawal_requests_txid', 'withdrawal_requests', type_='unique')
    op.drop_column('withdrawal_requests', 'exchange_withdrawal_id')
    op.drop_column('withdrawal_requests', 'network_fee')
    op.drop_column('withdrawal_requests', 'sent_amount')
    op.drop_column('withdrawal_requests', 'network')
    op.drop_column('withdrawal_requests', 'txid')
    op.add_column('withdrawal_requests', sa.Column(
        'paid_cop_amount', sa.DECIMAL(precision=30, scale=12), nullable=True,
        comment='Pesos que se pagaron'))
    op.add_column('withdrawal_requests', sa.Column(
        'cop_rate', sa.DECIMAL(precision=30, scale=12), nullable=True,
        comment='COP por USDT usados'))
    op.add_column('withdrawal_requests', sa.Column(
        'payment_reference', sa.String(length=120), nullable=True,
        comment='Referencia de la transferencia'))

    op.alter_column(
        'payout_methods', 'enc_details',
        existing_type=sa.Text(), existing_nullable=False,
        comment='Datos bancarios cifrados (Fernet)',
        existing_comment='Red, dirección y memo cifrados (Fernet)',
    )
    op.alter_column(
        'payout_methods', 'kind',
        existing_type=sa.String(length=16), existing_nullable=False,
        comment='bank | nequi',
        existing_comment='crypto (bank | nequi: históricos)',
    )
    op.drop_constraint(_KIND_CHECK, 'payout_methods', type_='check')
    op.create_check_constraint(_KIND_CHECK, 'payout_methods', f"`kind` IN {_LEGACY}")
