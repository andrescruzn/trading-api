# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/services/auth/rotate_token_service.py
#
# CASO DE USO:
# - Rotar el token del usuario (renovar sesión).
#
# ESTRATEGIA:
# - Requiere token válido (token_required_actual en REST)
# - Emite nuevo JWT (nuevo JTI)
# - Actualiza user.token_current_jti = nuevo_jti
# - El token anterior queda inválido inmediatamente
#
# NOTA:
# - Esto es "refresh simple" SIN refresh token separado.
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from app.common.config.settings import Settings
from app.common.contracts import ServiceResult
from app.common.security.jwt import create_access_token
from app.modules.users.domain import UserRepository


@dataclass(frozen=True)
class RotateTokenPayload:
    """
    Payload crudo: nuevo token emitido.
    """
    access_token: str
    expires_at: datetime
    jti: str


class RotateTokenService:
    """
    Service para rotar token (renovar sesión).
    """

    def __init__(self, *, repo: UserRepository, session: Session, settings: Settings):
        self._repo = repo
        self._session = session
        self._settings = settings

    def rotate(self, user_id: int) -> ServiceResult[RotateTokenPayload]:
        """
        Retorna:
        - ok(RotateTokenPayload)
        - fail(...)
        """

        # --------------------------------------------------------------
        # 1) Cargar usuario
        # --------------------------------------------------------------
        user = self._repo.get_by_id(int(user_id))
        if user is None:
            return ServiceResult.fail(code="USER_NOT_FOUND", http_status=404)

        if not user.is_active():
            return ServiceResult.fail(code="USER_NOT_ALLOWED", http_status=403, meta={"status": user.status})

        # --------------------------------------------------------------
        # 2) Emitir nuevo token (nuevo JTI)
        # --------------------------------------------------------------
        token_pack = create_access_token(
            subject={"user_id": user.id},
            secret_key=self._settings.JWT_SECRET_KEY,
            expires_delta=self._settings.JWT_ACCESS_TOKEN_EXPIRES,
            algorithm=self._settings.JWT_ALGORITHM,
        )

        # --------------------------------------------------------------
        # 3) Persistir nuevo JTI (revoca el token anterior)
        # --------------------------------------------------------------
        user.token_current_jti = token_pack["jti"]
        self._repo.update(user)
        self._session.commit()

        return ServiceResult.ok(
            RotateTokenPayload(
                access_token=token_pack["token"],
                expires_at=token_pack["expires_at"],
                jti=token_pack["jti"],
            )
        )