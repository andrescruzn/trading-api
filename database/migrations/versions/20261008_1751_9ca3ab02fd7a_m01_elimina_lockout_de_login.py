"""m01 elimina lockout de login (failed_attempts, login_locked_until)

Revision ID: 9ca3ab02fd7a
Revises: c4497f5a0188
Create Date: 2026-10-08 17:51:32.492008+00:00

MOTIVO:
- M1 (Auth): se quita el bloqueo de cuenta por códigos fallidos (3 → 1 h).
  Delataba qué correos tienen cuenta (solo las reales se bloqueaban) y
  dejaba bloquear cuentas ajenas. La fuerza bruta se frena ahora con rate
  limit por correo e IP + la vigencia de 10 min del OTP.
- users.failed_attempts y users.login_locked_until ya no tienen uso: se
  eliminan con su CHECK y su índice.
- Escrita a mano: autogenerate no detecta CHECKs quitados, y MySQL no deja
  borrar una columna mientras un CHECK la use (error 3959).
- El downgrade las vuelve a crear vacías (0 / NULL): nadie queda bloqueado.
"""

from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '9ca3ab02fd7a'
down_revision: str | Sequence[str] | None = 'c4497f5a0188'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint('chk_users_failed_attempts', 'users', type_='check')
    op.drop_index('idx_users_login_locked_until', table_name='users')
    op.drop_column('users', 'login_locked_until')
    op.drop_column('users', 'failed_attempts')


def downgrade() -> None:
    # Mismas posiciones que en el esquema inicial (después de status).
    op.execute(sa.text(
        "ALTER TABLE users "
        "ADD COLUMN failed_attempts INT NOT NULL DEFAULT '0' AFTER status, "
        "ADD COLUMN login_locked_until TIMESTAMP(6) NULL AFTER failed_attempts"
    ))
    op.create_index('idx_users_login_locked_until', 'users', ['login_locked_until'], unique=False)
    op.create_check_constraint('chk_users_failed_attempts', 'users', '`failed_attempts` >= 0')
