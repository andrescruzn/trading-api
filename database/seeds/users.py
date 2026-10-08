# -*- coding: utf-8 -*-

# ======================================================================
# database/seeds/users.py
#
# PROPÓSITO:
# - Usuarios base del equipo (rol admin), para no tener que registrarlos
#   desde la web en cada BD nueva.
#
# NOTAS:
# - Requiere el seed `roles` (FK users.role_id).
# - Sin contraseña: el login es solo por código OTP al correo.
# - Clave natural: email. Un usuario existente no se toca.
# ======================================================================

from __future__ import annotations

from sqlalchemy.orm import Session

from app.common.config import settings
from app.modules.users.infrastructure.user_model import UserModel
from database.seeds._helpers import SeedStats, get_or_create

# (email, nombre completo)
USERS: list[tuple[str, str]] = [
    ("andrescruznovoa@gmail.com", "Andrés Cruz Novoa"),
    ("dayrondaza05@gmail.com", "Dayron Daza"),
]


def run(session: Session) -> SeedStats:
    stats = SeedStats()

    for email, full_name in USERS:
        get_or_create(
            session,
            UserModel,
            lookup={"email": email},
            values={
                "full_name": full_name,
                "role_id": settings.AUTH_ADMIN_ROLE_ID,
                "status": "active",
            },
            stats=stats,
        )

    return stats
