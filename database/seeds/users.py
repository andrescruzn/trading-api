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
# - La contraseña sale de SEED_USERS_PASSWORD (.env) y se guarda con bcrypt;
#   nunca se versiona en claro. Si falta, el seed se omite.
# - Clave natural: email. Un usuario existente no se toca (ni su contraseña).
# ======================================================================

from __future__ import annotations

import os

from sqlalchemy.orm import Session

from app.common.config import settings
from app.common.security.password_hasher import hash_password
from app.modules.users.infrastructure.user_model import UserModel
from database.seeds._helpers import SeedStats, get_or_create

# (email, nombre completo)
USERS: list[tuple[str, str]] = [
    ("andrescruznovoa@gmail.com", "Andrés Cruz Novoa"),
    ("dayrondaza05@gmail.com", "Dayron Daza"),
]


def run(session: Session) -> SeedStats:
    stats = SeedStats()

    password = os.getenv("SEED_USERS_PASSWORD", "").strip()
    if not password:
        stats.notes.append("omitido: falta SEED_USERS_PASSWORD en el .env")
        return stats

    password_hash = hash_password(password)
    for email, full_name in USERS:
        get_or_create(
            session,
            UserModel,
            lookup={"email": email},
            values={
                "full_name": full_name,
                "password_hash": password_hash,
                "role_id": settings.AUTH_ADMIN_ROLE_ID,
                "status": "active",
            },
            stats=stats,
        )

    return stats
