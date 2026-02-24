# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/services/auth/change_password_service.py
#
# CASO DE USO:
# - Cambiar la contraseña del usuario autenticado.
#
# REGLAS:
# - Verificar password actual antes de cambiar
# - Nueva password debe cumplir política de seguridad (8+ chars,
#   mayúscula, minúscula, número)
# - Nueva password != password actual
# - Al cambiar: revocar sesión actual (fuerza re-login por seguridad)
# ======================================================================

from __future__ import annotations

import re

from sqlalchemy.orm import Session

from app.common.contracts import ServiceResult
from app.common.security.password_hasher import hash_password, verify_password
from app.common.utils.input_cleaner import clean_str
from app.modules.users.domain import UserRepository


def _validate_password_strength(password: str) -> bool:
    """
    Política de contraseña:
    - Mínimo 8 caracteres
    - Al menos 1 mayúscula
    - Al menos 1 minúscula
    - Al menos 1 número
    """
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    return True


class ChangePasswordService:
    """
    Service para cambiar la contraseña del usuario autenticado.
    """

    def __init__(self, *, repo: UserRepository, session: Session):
        self._repo = repo
        self._session = session

    def change(
        self,
        user_id: int,
        current_password: str,
        new_password: str,
    ) -> ServiceResult[None]:
        """
        Retorna:
        - ok(None)
        - fail(code, http_status)
        """

        # --------------------------------------------------------------
        # 1) Input cleaning
        # --------------------------------------------------------------
        try:
            current_clean = clean_str(current_password, min_len=1, max_len=255)
            new_clean = clean_str(new_password, min_len=8, max_len=255)
        except ValueError:
            return ServiceResult.fail(code="VALIDATION_ERROR", http_status=422)

        # --------------------------------------------------------------
        # 2) Cargar usuario
        # --------------------------------------------------------------
        user = self._repo.get_by_id(int(user_id))
        if user is None:
            return ServiceResult.fail(code="USER_NOT_FOUND", http_status=404)

        if not user.is_active():
            return ServiceResult.fail(
                code="USER_NOT_ALLOWED",
                http_status=403,
                meta={"status": user.status},
            )

        # --------------------------------------------------------------
        # 3) Verificar password actual
        # --------------------------------------------------------------
        if not verify_password(current_clean, user.password_hash):
            return ServiceResult.fail(
                code="INVALID_CREDENTIALS",
                http_status=401,
            )

        # --------------------------------------------------------------
        # 4) Nueva password no puede ser igual a la actual
        # --------------------------------------------------------------
        if verify_password(new_clean, user.password_hash):
            return ServiceResult.fail(
                code="PASSWORD_SAME_AS_CURRENT",
                http_status=422,
            )

        # --------------------------------------------------------------
        # 5) Política de seguridad
        # --------------------------------------------------------------
        if not _validate_password_strength(new_clean):
            return ServiceResult.fail(
                code="PASSWORD_TOO_WEAK",
                http_status=422,
            )

        # --------------------------------------------------------------
        # 6) Cambiar password y revocar sesión (fuerza re-login)
        # --------------------------------------------------------------
        user.password_hash = hash_password(new_clean)
        user.token_current_jti = None  # Revoca sesión activa

        self._repo.update(user)
        self._session.commit()

        return ServiceResult.ok(None)
