
"""m01 roles fondo

Revision ID: 87dc7203af68
Revises: 45ba83355691
Create Date: 2026-10-23 00:27:00.000000+00:00

MOTIVO:
- Fondo común (F1): los roles pasan a ser Super admin (propietarios), Socio (solo
  lectura) e Inversor.
  - `admin` se renombra a `super_admin` ("Super admin"), con el mismo ID.
  - Se crea `partner` ("Socio") con ID 4 (`AUTH_PARTNER_ROLE_ID`).
  - Las personas con rol `user` pasan a `investor` y el rol `user` queda inactivo
    (no se borra: lo referencian datos históricos y el FK de `users`).
- Migración solo de datos: no cambia el esquema. Se busca por `code` (no por ID)
  para no depender del .env de cada BD.
- downgrade: vuelve `super_admin` a `admin`, reactiva `user`, pasa los socios a
  inversor y borra `partner`. Quien era `user` antes del upgrade queda como
  `investor` (el upgrade no guarda quién era quién).
"""

from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '87dc7203af68'
down_revision: str | Sequence[str] | None = '45ba83355691'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(sa.text(
        "UPDATE roles SET code = 'super_admin', name = 'Super admin' WHERE code = 'admin'"
    ))
    op.execute(sa.text(
        "INSERT INTO roles (id, code, name, is_active) "
        "SELECT 4, 'partner', 'Socio', 1 FROM DUAL "
        "WHERE NOT EXISTS (SELECT 1 FROM roles WHERE code = 'partner')"
    ))
    # Los usuarios del rol `user` pasan a inversor (si ambos roles existen).
    op.execute(sa.text(
        "UPDATE users u "
        "JOIN roles r_user ON r_user.id = u.role_id AND r_user.code = 'user' "
        "JOIN roles r_inv ON r_inv.code = 'investor' "
        "SET u.role_id = r_inv.id"
    ))
    op.execute(sa.text("UPDATE roles SET is_active = 0 WHERE code = 'user'"))


def downgrade() -> None:
    op.execute(sa.text("UPDATE roles SET is_active = 1 WHERE code = 'user'"))
    op.execute(sa.text(
        "UPDATE users u "
        "JOIN roles r_partner ON r_partner.id = u.role_id AND r_partner.code = 'partner' "
        "JOIN roles r_inv ON r_inv.code = 'investor' "
        "SET u.role_id = r_inv.id"
    ))
    op.execute(sa.text("DELETE FROM roles WHERE code = 'partner'"))
    op.execute(sa.text(
        "UPDATE roles SET code = 'admin', name = 'Administrador' WHERE code = 'super_admin'"
    ))
