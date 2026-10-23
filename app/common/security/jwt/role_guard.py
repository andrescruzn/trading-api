# -*- coding: utf-8 -*-

# ======================================================================
# app/common/security/jwt/role_guard.py
#
# PROPÓSITO:
# - Guards de autorización por rol usando la identidad validada por DB.
#
# ROLES (fondo común):
# - super_admin: los propietarios. Ven y cambian todo.
# - partner (socio): ve todo lo que ve un super admin, no cambia nada.
# - investor: solo lo suyo.
#
# REGLAS:
# - Lectura global ("staff") = super_admin + partner → `read_scope` None.
# - Escritura global = solo super_admin → `write_scope` None.
# - El bloqueo de escrituras del socio vive en read_only_policy.py
#   (aplicado en el guard JWT); aquí solo se decide quién ve y cambia qué.
# ======================================================================

from __future__ import annotations

from typing import Any, Dict

from fastapi import Depends

from app.common.config import settings
from app.common.security.jwt.auth_exceptions import AuthException
from app.common.security.jwt.jwt_guard import token_required_actual


def _role_id(identity: Dict[str, Any]) -> int:
    role_id = identity.get("role_id")
    if role_id is None:
        raise AuthException(code="AUTH_INVALID_IDENTITY", http_status=401)
    return int(role_id)


def is_super_admin(identity: Dict[str, Any]) -> bool:
    """True si la identidad es de un propietario (super admin)."""
    return int(identity.get("role_id", 0)) == int(settings.AUTH_SUPER_ADMIN_ROLE_ID)


def is_partner(identity: Dict[str, Any]) -> bool:
    """True si la identidad es de un socio (solo lectura)."""
    return int(identity.get("role_id", 0)) == int(settings.AUTH_PARTNER_ROLE_ID)


def is_investor(identity: Dict[str, Any]) -> bool:
    """True si la identidad es de un inversor."""
    return int(identity.get("role_id", 0)) == int(settings.AUTH_INVESTOR_ROLE_ID)


def is_staff(identity: Dict[str, Any]) -> bool:
    """True si puede ver todo el sistema (super admin o socio)."""
    return is_super_admin(identity) or is_partner(identity)


def super_admin_required(
    identity: Dict[str, Any] = Depends(token_required_actual),
) -> Dict[str, Any]:
    """Permite acceso SOLO a super admin (toda acción que cambia el sistema)."""
    if _role_id(identity) != int(settings.AUTH_SUPER_ADMIN_ROLE_ID):
        raise AuthException(
            code="AUTH_FORBIDDEN_ROLE", http_status=403, meta={"required": "super_admin"}
        )
    return identity


def staff_required(identity: Dict[str, Any] = Depends(token_required_actual)) -> Dict[str, Any]:
    """Permite acceso a super admin y socio (vistas de supervisión, solo lectura)."""
    _role_id(identity)
    if not is_staff(identity):
        raise AuthException(
            code="AUTH_FORBIDDEN_ROLE", http_status=403, meta={"required": "staff"}
        )
    return identity


def read_scope(identity: Dict[str, Any]) -> int | None:
    """
    user_id del que llama, o None si es staff (ve todo).

    Los servicios con propiedad reciben este valor como `owner_id` en lecturas.
    """
    if is_staff(identity):
        return None
    return int(identity["user_id"])


def write_scope(identity: Dict[str, Any]) -> int | None:
    """
    user_id del que llama, o None si es super admin (cambia todo).

    Los servicios con propiedad reciben este valor como `owner_id` en escrituras.
    Un socio queda limitado a lo propio (y el guard JWT ya le bloquea las escrituras).
    """
    if is_super_admin(identity):
        return None
    return int(identity["user_id"])
