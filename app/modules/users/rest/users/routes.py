# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/rest/users/routes.py
#
# ENDPOINTS:
# - GET /users            → listar usuarios (solo admin)
# - PUT /users/{id}/role  → cambiar el rol de un usuario (solo admin)
#
# NOTAS:
# - Lo usan las vistas de Supervisión para mostrar el dueño de agentes,
#   cuentas, órdenes y alertas, y la página Usuarios. Solo datos de
#   identificación (sin OTP, JTI ni Telegram).
# ======================================================================

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.http import build_error_response, build_list_response, build_success_response
from app.common.security.jwt.role_guard import admin_required
from app.extensions.db import get_db
from app.modules.users.providers.auth_provider import AuthServiceFactory
from app.modules.users.services.users import UserSummaryPayload

from .error_messages import USER_ERROR_MESSAGES
from .schemas import UpdateUserRoleRequest

router = APIRouter(prefix="/users", tags=["Users"])


def get_factory(db: Session = Depends(get_db)) -> AuthServiceFactory:
    return AuthServiceFactory(session=db)


def _user_to_dict(u: UserSummaryPayload) -> dict[str, Any]:
    return {
        "id":            u.id,
        "email":         u.email,
        "full_name":     u.full_name,
        "role_code":     u.role_code,
        "role_label":    u.role_name,
        "status":        u.status,
        "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
    }


# ======================================================================
# GET /users
# ======================================================================

@router.get("", status_code=200)
def list_users(
    _identity: dict = Depends(admin_required),
    factory: AuthServiceFactory = Depends(get_factory),
):
    """Lista los usuarios del sistema con su rol (solo admin)."""
    result = factory.list_users().list()

    return build_list_response(items=[_user_to_dict(u) for u in (result.data or [])])


# ======================================================================
# PUT /users/{user_id}/role
# ======================================================================

@router.put("/{user_id}/role", status_code=200)
def update_user_role(
    user_id: int,
    payload: UpdateUserRoleRequest,
    identity: dict = Depends(admin_required),
    factory: AuthServiceFactory = Depends(get_factory),
):
    """Cambia el rol de un usuario (solo admin; nunca el propio)."""
    result = factory.update_user_role().update(
        user_id=user_id,
        role_code=payload.role_code,
        requester_user_id=int(identity["user_id"]),
    )

    if not result.success:
        return build_error_response(result, USER_ERROR_MESSAGES)

    return build_success_response(data=_user_to_dict(result.data), msg="Rol actualizado.")
