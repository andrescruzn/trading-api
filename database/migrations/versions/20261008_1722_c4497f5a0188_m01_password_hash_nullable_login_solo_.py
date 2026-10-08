
"""m01 password_hash nullable (login solo OTP)

Revision ID: c4497f5a0188
Revises: c3c5639df2de
Create Date: 2026-10-08 17:22:22.247961+00:00

MOTIVO:
- M1 (Auth): el login pasa a ser solo por código OTP al correo; se eliminan
  el login con contraseña y el cambio de contraseña.
- users.password_hash queda obsoleta: pasa a nullable y se vacía (NULL) para
  no conservar hashes que ya no sirven. La columna no se borra.
- El downgrade NO recupera los hashes: deja '' (ninguna contraseña valida
  contra un hash vacío), así que tras volver atrás hay que asignar
  contraseñas nuevas.
"""

from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = 'c4497f5a0188'
down_revision: str | Sequence[str] | None = 'c3c5639df2de'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column('users', 'password_hash',
               existing_type=mysql.VARCHAR(length=255),
               nullable=True,
               comment='Obsoleta: el login es solo por OTP')

    # Sin login por contraseña, los hashes guardados ya no tienen uso.
    op.execute(sa.text("UPDATE users SET password_hash = NULL"))


def downgrade() -> None:
    # NOT NULL exige un valor: '' no valida contra ninguna contraseña.
    op.execute(sa.text("UPDATE users SET password_hash = '' WHERE password_hash IS NULL"))

    op.alter_column('users', 'password_hash',
               existing_type=mysql.VARCHAR(length=255),
               nullable=False,
               comment=None,
               existing_comment='Obsoleta: el login es solo por OTP')
