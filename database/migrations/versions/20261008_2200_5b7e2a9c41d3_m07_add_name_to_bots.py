"""m07 add name to bots

Revision ID: 5b7e2a9c41d3
Revises: 9ca3ab02fd7a
Create Date: 2026-10-08 22:00:00.000000+00:00

MOTIVO:
- M7 (Bots): en la UI los bots pasan a llamarse "agentes" y son el punto
  de entrada de la app; cada uno necesita un nombre visible en vez de
  "Bot #12".
- bots.name VARCHAR(80) NOT NULL. Se agrega nullable, se rellena con
  'Agente #<id>' en los bots existentes y luego se vuelve NOT NULL; así no
  falla en una BD con datos.
- Escrita a mano: autogenerate no hace el backfill, y la BD de desarrollo
  no estaba al día para generarla.
- El downgrade elimina la columna (se pierden los nombres puestos a mano).
"""

from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '5b7e2a9c41d3'
down_revision: str | Sequence[str] | None = '9ca3ab02fd7a'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_COMMENT = "Nombre visible del agente (en la UI los bots se llaman agentes)"


def upgrade() -> None:
    # Misma posición que en el modelo (después de id).
    op.execute(sa.text(
        "ALTER TABLE bots ADD COLUMN name VARCHAR(80) NULL "
        f"COMMENT '{_COMMENT}' AFTER id"
    ))
    op.execute(sa.text(
        "UPDATE bots SET name = CONCAT('Agente #', id) WHERE name IS NULL"
    ))
    op.alter_column(
        'bots',
        'name',
        existing_type=sa.String(length=80),
        nullable=False,
        existing_comment=_COMMENT,
        comment=_COMMENT,
    )


def downgrade() -> None:
    op.drop_column('bots', 'name')
