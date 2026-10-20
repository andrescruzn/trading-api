# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/rest/users/routes.py
#
# ENDPOINTS:
# - GET /users → listar usuarios (solo admin)
#
# NOTAS:
# - Lo usan las vistas de Supervisión para mostrar el dueño de agentes,
#   cuentas, órdenes y alertas. Solo datos de identificación.
# ======================================================================

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.http import build_list_response
from app.common.security.jwt.role_guard import admin_required
from app.extensions.db import get_db
from app.modules.users.providers.auth_provider import AuthServiceFactory

router = APIRouter(prefix="/users", tags=["Users"])


def get_factory(db: Session = Depends(get_db)) -> AuthServiceFactory:
    return AuthServiceFactory(session=db)


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

    return build_list_response(
        items=[
            {
                "id":         u.id,
                "email":      u.email,
                "full_name":  u.full_name,
                "role_code":  u.role_code,
                "role_label": u.role_name,
                "status":     u.status,
            }
            for u in (result.data or [])
        ],
    )
