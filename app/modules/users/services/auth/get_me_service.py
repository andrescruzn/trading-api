# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/services/auth/get_me_service.py
#
# CASO DE USO:
# - Obtener el perfil del usuario autenticado.
#
# PROPÓSITO:
# - Alimentar el dashboard con datos reales del usuario + su rol.
#
# DISEÑO:
# - Consulta la tabla `roles` directamente para obtener code y name,
#   siguiendo el mismo patrón que jwt_guard.py.
# - Así el label del rol viene de la BD y no de una comparación
#   hardcodeada en settings.
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.common.contracts import ServiceResult
from app.modules.users.domain import UserRepository


@dataclass(frozen=True)
class UserProfilePayload:
    """
    Payload crudo del perfil del usuario (sin UI).
    Incluye información del rol leída desde la tabla roles.
    """
    id: int
    email: str
    full_name: Optional[str]
    role_id: int
    role_code: str        # ej: "user", "admin"
    role_name: str        # ej: "Usuario", "Administrador"
    status: str
    last_login_at: Optional[datetime]
    created_at: Optional[datetime]


class GetMeService:
    """
    Service para obtener el perfil del usuario autenticado.
    """

    def __init__(self, *, repo: UserRepository, session: Session):
        self._repo = repo
        self._session = session

    def get(self, user_id: int) -> ServiceResult[UserProfilePayload]:
        """
        Retorna:
        - ok(UserProfilePayload) con datos del usuario y su rol
        - fail("USER_NOT_FOUND", 404)
        - fail("ROLE_NOT_FOUND", 500) si el rol está corrupto en BD
        """

        # --------------------------------------------------------------
        # 1) Cargar usuario
        # --------------------------------------------------------------
        user = self._repo.get_by_id(int(user_id))
        if user is None:
            return ServiceResult.fail(code="USER_NOT_FOUND", http_status=404)

        # --------------------------------------------------------------
        # 2) Leer rol desde la tabla `roles` (mismo patrón que jwt_guard)
        # --------------------------------------------------------------
        role_row = self._session.execute(
            text("SELECT code, name FROM roles WHERE id = :role_id LIMIT 1"),
            {"role_id": int(user.role_id)},
        ).mappings().first()

        if role_row is None:
            return ServiceResult.fail(code="ROLE_NOT_FOUND", http_status=500)

        # --------------------------------------------------------------
        # 3) Mapear a payload de dominio
        # --------------------------------------------------------------
        return ServiceResult.ok(
            UserProfilePayload(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                role_id=user.role_id,
                role_code=str(role_row["code"]),
                role_name=str(role_row["name"]),
                status=user.status,
                last_login_at=user.last_login_at,
                created_at=user.created_at,
            )
        )
