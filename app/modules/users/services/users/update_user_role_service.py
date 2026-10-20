# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/services/users/update_user_role_service.py
#
# CASO DE USO:
# - Un admin cambia el rol de otro usuario (user / admin / investor).
#
# REGLAS:
# - El rol se recibe por código y se traduce al ID con los settings
#   AUTH_*_ROLE_ID (nunca IDs fijos en el código).
# - Nadie cambia su propio rol: así el sistema nunca se queda sin admin y
#   nadie se quita el acceso por error.
# - El cambio vale desde la siguiente petición del usuario: el guard JWT
#   lee el rol de la BD en cada request.
# ======================================================================

from __future__ import annotations

from app.common.contracts import ServiceResult
from app.modules.users.domain import UserRepository
from app.modules.users.services.users.list_users_service import UserSummaryPayload


class UpdateUserRoleService:
    """Cambia el rol de un usuario. `role_ids` mapea código → ID de rol."""

    def __init__(self, *, repo: UserRepository, role_ids: dict[str, int]):
        self._repo = repo
        self._role_ids = role_ids

    def update(
        self,
        user_id: int,
        role_code: str,
        requester_user_id: int,
    ) -> ServiceResult[UserSummaryPayload]:
        role_id = self._role_ids.get(role_code)
        if role_id is None:
            return ServiceResult.fail(code="USER_INVALID_ROLE", http_status=422)

        if int(user_id) == int(requester_user_id):
            return ServiceResult.fail(code="USER_CANNOT_CHANGE_OWN_ROLE", http_status=422)

        user = self._repo.get_by_id(int(user_id))
        if user is None:
            return ServiceResult.fail(code="USER_NOT_FOUND", http_status=404)

        role = self._repo.get_role_info(role_id)
        if role is None:
            # El ID del setting no existe en la tabla `roles` (BD mal sembrada).
            return ServiceResult.fail(code="USER_INVALID_ROLE", http_status=422)

        if user.role_id != role_id:
            user.role_id = role_id
            try:
                user = self._repo.update(user)
                self._repo.commit()
            except Exception:
                self._repo.rollback()
                raise

        return ServiceResult.ok(
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
