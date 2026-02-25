# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/market/rest/exchanges/routes.py
#
# ENDPOINTS:
# - GET  /exchanges         → lista todos (autenticado)
# - POST /exchanges         → crear (solo admin)
# - PUT  /exchanges/{id}    → actualizar (solo admin)
# ======================================================================

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.http import (
    build_error_response,
    build_list_response,
    build_created_response,
    build_success_response,
)
from app.common.security.jwt import token_required_actual
from app.common.security.jwt.role_guard import admin_required
from app.extensions.db import get_db
from app.modules.market.providers import MarketServiceFactory

from .error_messages import EXCHANGE_ERROR_MESSAGES
from .schemas import CreateExchangeRequest, UpdateExchangeRequest

router = APIRouter(prefix="/exchanges", tags=["Market — Exchanges"])


# ======================================================================
# Dependency
# ======================================================================

def get_factory(db: Session = Depends(get_db)) -> MarketServiceFactory:
    return MarketServiceFactory(session=db)


# ======================================================================
# Helper: serializar Exchange a dict
# ======================================================================

def _exchange_to_dict(ex: Any) -> dict:
    return {
        "id": ex.id,
        "name": ex.name,
        "type": ex.type,
        "is_active": ex.is_active,
        "created_at": ex.created_at.isoformat() if ex.created_at else None,
    }


# ======================================================================
# GET /exchanges
# ======================================================================

@router.get("", status_code=200)
def list_exchanges(
    is_active: Optional[bool] = Query(default=None, description="Filtrar por estado activo"),
    _identity: dict = Depends(token_required_actual),
    factory: MarketServiceFactory = Depends(get_factory),
):
    """Lista exchanges. Cualquier usuario autenticado puede consultarlos."""
    result = factory.list_exchanges().list(is_active=is_active)

    if not result.success:
        return build_error_response(result, EXCHANGE_ERROR_MESSAGES)

    return build_list_response(
        items=[_exchange_to_dict(e) for e in (result.data or [])],
        msg="OK",
    )


# ======================================================================
# POST /exchanges
# ======================================================================

@router.post("", status_code=201)
def create_exchange(
    payload: CreateExchangeRequest,
    _identity: dict = Depends(admin_required),
    factory: MarketServiceFactory = Depends(get_factory),
):
    """Crea un exchange. Solo admins."""
    result = factory.create_exchange().create(
        name=payload.name,
        type=payload.type,
    )

    if not result.success:
        return build_error_response(result, EXCHANGE_ERROR_MESSAGES)

    return build_created_response(
        data=_exchange_to_dict(result.data),
        msg="Exchange creado exitosamente.",
    )


# ======================================================================
# PUT /exchanges/{exchange_id}
# ======================================================================

@router.put("/{exchange_id}", status_code=200)
def update_exchange(
    exchange_id: int,
    payload: UpdateExchangeRequest,
    _identity: dict = Depends(admin_required),
    factory: MarketServiceFactory = Depends(get_factory),
):
    """Actualiza nombre, tipo o estado de un exchange. Solo admins."""
    result = factory.update_exchange().update(
        exchange_id=exchange_id,
        name=payload.name,
        type=payload.type,
        is_active=payload.is_active,
    )

    if not result.success:
        return build_error_response(result, EXCHANGE_ERROR_MESSAGES)

    return build_success_response(
        data=_exchange_to_dict(result.data),
        msg="Exchange actualizado exitosamente.",
    )
