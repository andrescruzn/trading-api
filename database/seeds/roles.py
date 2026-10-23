# -*- coding: utf-8 -*-

# ======================================================================
# database/seeds/roles.py
#
# PROPÓSITO:
# - Roles base de la app (fondo común): super_admin (propietarios),
#   investor y partner (socio, solo lectura).
#
# NOTAS:
# - Los IDs salen de settings (AUTH_*_ROLE_ID): la app los compara por ID,
#   así que deben coincidir con el .env.
# - El antiguo rol `user` ya no se siembra: la migración m01_roles_fondo
#   lo deja inactivo y `admin` pasa a llamarse `super_admin`.
# ======================================================================

from __future__ import annotations

from sqlalchemy.orm import Session

from app.common.config import settings
from app.modules.users.infrastructure.role_model import RoleModel
from database.seeds._helpers import SeedStats, get_or_create


def run(session: Session) -> SeedStats:
    stats = SeedStats()

    roles = [
        (settings.AUTH_SUPER_ADMIN_ROLE_ID, "super_admin", "Super admin"),
        (settings.AUTH_INVESTOR_ROLE_ID, "investor", "Inversor"),
        (settings.AUTH_PARTNER_ROLE_ID, "partner", "Socio"),
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
