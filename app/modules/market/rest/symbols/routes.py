# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/market/rest/symbols/routes.py
#
# ENDPOINTS:
# - GET  /symbols           → lista (autenticado, filtros opcionales)
# - POST /symbols           → crear (solo admin)
# - PUT  /symbols/{id}      → actualizar (solo admin)
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

from .error_messages import SYMBOL_ERROR_MESSAGES
from .schemas import CreateSymbolRequest, UpdateSymbolRequest

router = APIRouter(prefix="/symbols", tags=["Market — Symbols"])


def get_factory(db: Session = Depends(get_db)) -> MarketServiceFactory:
    return MarketServiceFactory(session=db)


def _symbol_to_dict(s: Any) -> dict:
    return {
        "id": s.id,
        "exchange_id": s.exchange_id,
        "symbol": s.symbol,
        "asset_class": s.asset_class,
        "base_asset": s.base_asset,
        "quote_asset": s.quote_asset,
        "tick_size": str(s.tick_size) if s.tick_size is not None else None,
        "lot_size": str(s.lot_size) if s.lot_size is not None else None,
        "is_active": s.is_active,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }


# ======================================================================
# GET /symbols
# ======================================================================

@router.get("", status_code=200)
def list_symbols(
    exchange_id: Optional[int] = Query(default=None, description="Filtrar por exchange"),
    asset_class: Optional[str] = Query(default=None, description="Filtrar por clase de activo"),
    is_active: Optional[bool] = Query(default=None, description="Filtrar por estado activo"),
    _identity: dict = Depends(token_required_actual),
    factory: MarketServiceFactory = Depends(get_factory),
):
    """Lista símbolos con filtros opcionales. Cualquier usuario autenticado."""
    result = factory.list_symbols().list(
        exchange_id=exchange_id,
        asset_class=asset_class,
        is_active=is_active,
    )

    if not result.success:
        return build_error_response(result, SYMBOL_ERROR_MESSAGES)

    return build_list_response(
        items=[_symbol_to_dict(s) for s in (result.data or [])],
        msg="OK",
    )


# ======================================================================
# POST /symbols
# ======================================================================

@router.post("", status_code=201)
def create_symbol(
    payload: CreateSymbolRequest,
    _identity: dict = Depends(admin_required),
    factory: MarketServiceFactory = Depends(get_factory),
):
    """Crea un símbolo. Solo admins."""
    result = factory.create_symbol().create(
        exchange_id=payload.exchange_id,
        symbol=payload.symbol,
        asset_class=payload.asset_class,
        base_asset=payload.base_asset,
        quote_asset=payload.quote_asset,
        tick_size=payload.tick_size,
        lot_size=payload.lot_size,
    )

    if not result.success:
        return build_error_response(result, SYMBOL_ERROR_MESSAGES)

    return build_created_response(
        data=_symbol_to_dict(result.data),
        msg="Símbolo creado exitosamente.",
    )


# ======================================================================
# PUT /symbols/{symbol_id}
# ======================================================================

@router.put("/{symbol_id}", status_code=200)
def update_symbol(
    symbol_id: int,
    payload: UpdateSymbolRequest,
    _identity: dict = Depends(admin_required),
    factory: MarketServiceFactory = Depends(get_factory),
):
    """Actualiza un símbolo. Solo admins."""
    result = factory.update_symbol().update(
        symbol_id=symbol_id,
        asset_class=payload.asset_class,
        base_asset=payload.base_asset,
        quote_asset=payload.quote_asset,
        tick_size=payload.tick_size,
        lot_size=payload.lot_size,
        is_active=payload.is_active,
    )

    if not result.success:
        return build_error_response(result, SYMBOL_ERROR_MESSAGES)

    return build_success_response(
        data=_symbol_to_dict(result.data),
        msg="Símbolo actualizado exitosamente.",
    )
