# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/services/auth/logout_service.py
#
# CASO DE USO:
# - Logout seguro invalidando la sesión actual.
#
# ESTRATEGIA:
# - token_current_jti = None  => cualquier token existente muere
#
# NOTA:
# - El endpoint REST debe estar protegido con token_required_actual
#   para asegurar que el logout viene de una sesión válida.
# ======================================================================

from __future__ import annotations

from sqlalchemy.orm import Session

from app.common.contracts import ServiceResult
from app.modules.users.domain import UserRepository


class LogoutService:
    """
    Service para cerrar sesión (revocar token).
    """

    def __init__(self, *, repo: UserRepository, session: Session):
        self._repo = repo
        self._session = session

    def logout(self, user_id: int) -> ServiceResult[None]:
        """
        Revoca sesión del usuario.

        Retorna:
        - ok(None) si revocado
        - fail(...) si usuario no existe
        """

        # --------------------------------------------------------------
        # 1) Cargar usuario
        # --------------------------------------------------------------
        user = self._repo.get_by_id(int(user_id))
        if user is None:
            return ServiceResult.fail(code="USER_NOT_FOUND", http_status=404)

        # --------------------------------------------------------------
        # 2) Revocar sesión actual
        # --------------------------------------------------------------
        user.token_current_jti = None

        self._repo.update(user)
        self._session.commit()

        return ServiceResult.ok(None)