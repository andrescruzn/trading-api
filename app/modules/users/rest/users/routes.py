# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/rest/users/routes.py
#
# ENDPOINTS:
# - GET /users            → listar usuarios (super admin y socio)
# - POST /users           → invitar (crear) un usuario (solo super admin)
# - PUT /users/{id}/role  → cambiar el rol de un usuario (solo super admin)
# - PUT /users/{id}/status → activar, bloquear o desactivar (solo super admin)
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

from app.common.http import (
    build_created_response,
    build_error_response,
    build_list_response,
    build_success_response,
)
from app.common.security.jwt.role_guard import staff_required, super_admin_required
from app.common.utils import to_iso_utc
from app.extensions.db import get_db
from app.modules.users.providers.auth_provider import AuthServiceFactory
from app.modules.users.services.users import UserSummaryPayload

from .error_messages import USER_ERROR_MESSAGES
from .schemas import InviteUserRequest, UpdateUserRoleRequest, UpdateUserStatusRequest

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
        "last_login_at": to_iso_utc(u.last_login_at),
    }


# ======================================================================
# GET /users
# ======================================================================

@router.get("", status_code=200)
def list_users(
    _identity: dict = Depends(staff_required),
    factory: AuthServiceFactory = Depends(get_factory),
):
    """Lista los usuarios del sistema con su rol (super admin y socio)."""
    result = factory.list_users().list()

    return build_list_response(items=[_user_to_dict(u) for u in (result.data or [])])


# ======================================================================
# POST /users
# ======================================================================

@router.post("", status_code=201)
def invite_user(
    payload: InviteUserRequest,
    _identity: dict = Depends(super_admin_required),
    factory: AuthServiceFactory = Depends(get_factory),
):
    """Da de alta a una persona y le envía la bienvenida (solo super admin)."""
    result = factory.invite_user().invite(
        email=payload.email,
        role_code=payload.role_code,
        full_name=payload.full_name,
    )
    if not result.success:
        return build_error_response(result, USER_ERROR_MESSAGES)
    return build_created_response(
        data=_user_to_dict(result.data),
        msg="Usuario creado. Le enviamos un correo para que entre con su código.",
    )


# ======================================================================
# PUT /users/{user_id}/role
# ======================================================================

@router.put("/{user_id}/role", status_code=200)
def update_user_role(
    user_id: int,
    payload: UpdateUserRoleRequest,
    identity: dict = Depends(super_admin_required),
    factory: AuthServiceFactory = Depends(get_factory),
):
    """Cambia el rol de un usuario (solo super admin; nunca el propio)."""
    result = factory.update_user_role().update(
        user_id=user_id,
        role_code=payload.role_code,
        requester_user_id=int(identity["user_id"]),
    )

    if not result.success:
        return build_error_response(result, USER_ERROR_MESSAGES)

    return build_success_response(data=_user_to_dict(result.data), msg="Rol actualizado.")


# ======================================================================
# PUT /users/{user_id}/status
# ======================================================================

# Texto de éxito por estado nuevo: dice qué le pasa a la persona.
_STATUS_SUCCESS_MESSAGES: dict[str, str] = {
    "active":   "Cuenta activada. Ya puede entrar con su código.",
    "blocked":  "Cuenta bloqueada. Cerramos su sesión y no podrá entrar hasta que la actives.",
    "disabled": "Cuenta desactivada. Cerramos su sesión y no podrá entrar.",
}


@router.put("/{user_id}/status", status_code=200)
def update_user_status(
    user_id: int,
    payload: UpdateUserStatusRequest,
    identity: dict = Depends(super_admin_required),
    factory: AuthServiceFactory = Depends(get_factory),
):
    """Activa, bloquea o desactiva la cuenta de un usuario (solo super admin; nunca la propia)."""
    result = factory.update_user_status().update(
        user_id=user_id,
        status=payload.status,
        requester_user_id=int(identity["user_id"]),
    )

    if not result.success:
        return build_error_response(result, USER_ERROR_MESSAGES)

    return build_success_response(
        data=_user_to_dict(result.data),
        msg=_STATUS_SUCCESS_MESSAGES.get(result.data.status, "Estado actualizado."),
    )
