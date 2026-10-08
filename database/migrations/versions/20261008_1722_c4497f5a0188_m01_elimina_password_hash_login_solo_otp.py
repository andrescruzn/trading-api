
"""m01 elimina password_hash (login solo OTP)

Revision ID: c4497f5a0188
Revises: c3c5639df2de
Create Date: 2026-10-08 17:22:22.247961+00:00

MOTIVO:
- M1 (Auth): el login pasa a ser solo por código OTP al correo; se eliminan
  el login con contraseña y el cambio de contraseña.
- users.password_hash ya no tiene uso: se elimina la columna.
- El downgrade la vuelve a crear (VARCHAR(255) NOT NULL, después de
  full_name) pero vacía (''): los hashes no se recuperan y ninguna
  contraseña valida contra '', así que tras volver atrás hay que asignar
  contraseñas nuevas.
"""

from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'c4497f5a0188'
down_revision: str | Sequence[str] | None = 'c3c5639df2de'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column('users', 'password_hash')


def downgrade() -> None:
    # NOT NULL sobre filas existentes exige un valor: DEFAULT '' para crearla
    # y luego se quita el default para dejarla como en el esquema inicial.
    op.execute(sa.text(
        "ALTER TABLE users "
        "ADD COLUMN password_hash VARCHAR(255) NOT NULL DEFAULT '' AFTER full_name"
    ))
    op.alter_column('users', 'password_hash',
               existing_type=sa.String(length=255),
               existing_nullable=False,
               server_default=None)
