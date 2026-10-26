# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/market/rest/exchanges/routes.py
#
# ENDPOINTS:
# - GET  /exchanges         → lista todos (autenticado)
#
# NOTAS:
# - Solo lectura: la plataforma opera únicamente con Binance
#   (`PLATFORM_EXCHANGE_NAME`); los exchanges no se crean ni se editan.
# ======================================================================

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.http import build_error_response, build_list_response
from app.common.security.jwt import token_required_actual
from app.common.utils import to_iso_utc
from app.extensions.db import get_db
from app.modules.market.providers import MarketServiceFactory

from .error_messages import EXCHANGE_ERROR_MESSAGES

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
        "created_at": to_iso_utc(ex.created_at),
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
