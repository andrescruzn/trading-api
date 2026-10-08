# -*- coding: utf-8 -*-

# ======================================================================
# seeds/roles.py
#
# PROPÓSITO:
# - Roles base de la app: user, admin e investor (M10).
#
# NOTAS:
# - Los IDs salen de settings (AUTH_*_ROLE_ID): la app los compara por ID,
#   así que deben coincidir con el .env.
# - Reemplaza al rol investor de seeds/seed_billing.sql; user y admin solo
#   existían en el dump.
# ======================================================================

from __future__ import annotations

from sqlalchemy.orm import Session

from app.common.config import settings
from app.modules.users.infrastructure.role_model import RoleModel
from seeds._helpers import SeedStats, get_or_create


def run(session: Session) -> SeedStats:
    stats = SeedStats()

    roles = [
        (settings.AUTH_USER_ROLE_ID, "user", "Usuario"),
        (settings.AUTH_ADMIN_ROLE_ID, "admin", "Administrador"),
        (settings.AUTH_INVESTOR_ROLE_ID, "investor", "Inversor"),
    ]
    for role_id, code, name in roles:
        get_or_create(
            session,
            RoleModel,
            lookup={"code": code},
            values={"id": role_id, "name": name, "is_active": 1},
            stats=stats,
        )

    return stats
