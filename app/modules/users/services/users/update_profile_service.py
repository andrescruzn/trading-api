# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/services/users/update_profile_service.py
#
# CASO DE USO:
# - La persona cambia su propio nombre visible (no hay más datos
#   editables: el correo es su identidad para entrar y el rol lo decide un
#   admin).
# ======================================================================

from __future__ import annotations

from app.common.contracts import ServiceResult
from app.common.utils import clean_str
from app.modules.users.domain import UserRepository
from app.modules.users.domain.user_entity import User


class UpdateProfileService:
    """Actualiza el nombre de la persona autenticada."""

    def __init__(self, *, repo: UserRepository):
        self._repo = repo

    def update(self, user_id: int, full_name: str | None) -> ServiceResult[User]:
        user = self._repo.get_by_id(int(user_id))
        if user is None:
            return ServiceResult.fail(code="USER_NOT_FOUND", http_status=404)

        name = None
        if full_name and full_name.strip():
            try:
                name = clean_str(full_name, max_len=255)
            except ValueError:
                return ServiceResult.fail(code="USER_INVALID_NAME", http_status=422)

        if name != user.full_name:
            user.full_name = name
            try:
                user = self._repo.update(user)
                self._repo.commit()
            except Exception:
                self._repo.rollback()
                raise

        return ServiceResult.ok(user)
