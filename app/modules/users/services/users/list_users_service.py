# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/services/users/list_users_service.py
#
# CASO DE USO:
# - Listar los usuarios del sistema (solo admin) para mostrar quién es el
#   dueño de cada agente, cuenta, orden o alerta en las vistas globales.
#
# NOTAS:
# - Devuelve solo datos de identificación (sin OTP, JTI ni Telegram).
# - El rol se lee de la tabla `roles` una vez por rol distinto.
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.common.contracts import ServiceResult
from app.modules.users.domain import UserRepository


@dataclass(frozen=True)
class UserSummaryPayload:
    """Identificación de un usuario para las vistas de administración."""
    id: int
    email: str
    full_name: str | None
    role_code: str
    role_name: str
    status: str
    last_login_at: datetime | None


class ListUsersService:
    """Lista todos los usuarios con su rol, ordenados por ID."""

    def __init__(self, *, repo: UserRepository):
        self._repo = repo

    def list(self) -> ServiceResult[list[UserSummaryPayload]]:
        users = self._repo.list_all()

        roles: dict[int, dict[str, str] | None] = {}
        items: list[UserSummaryPayload] = []
        for user in users:
            role_id = int(user.role_id)
            if role_id not in roles:
                roles[role_id] = self._repo.get_role_info(role_id)
            role = roles[role_id] or {"code": "", "name": ""}
            items.append(
                UserSummaryPayload(
                    id=user.id,
                    email=user.email,
                    full_name=user.full_name,
                    role_code=str(role["code"]),
                    role_name=str(role["name"]),
                    status=user.status,
                    last_login_at=user.last_login_at,
                )
            )

        return ServiceResult.ok(items)
