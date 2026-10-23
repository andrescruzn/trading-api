# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/market/rest/explorer/routes.py
#
# ENDPOINTS:
# - GET  /explorer          → ranking de mercados por tendencia (autenticado)
# - POST /explorer/refresh  → descarga las velas diarias (solo super admin)
#
# NOTAS:
# - El GET solo lee la BD. Las velas 1d las trae el refresh (botón del
#   admin) o el scheduler, una vez al día.
# ======================================================================

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.http import build_error_response, build_list_response, build_success_response
from app.common.security.jwt import token_required_actual
from app.common.security.jwt.role_guard import super_admin_required
from app.extensions.db import get_db
from app.modules.market.providers import MarketServiceFactory
from app.modules.market.services.explorer import TrendRow

from .error_messages import EXPLORER_ERROR_MESSAGES

router = APIRouter(prefix="/explorer", tags=["Market — Explorer"])


def get_factory(db: Session = Depends(get_db)) -> MarketServiceFactory:
    return MarketServiceFactory(session=db)


def _row_to_dict(row: TrendRow) -> dict:
    s, m = row.symbol, row.metrics
    return {
        "symbol_id": s.id,
        "symbol": s.symbol,
        "exchange_name": s.exchange_name,
        "asset_class": s.asset_class,
        "is_perpetual": row.is_perpetual,
        "has_data": m is not None,
        "candles": m.candles if m else 0,
        "last_close": m.last_close if m else None,
        "last_ts": m.last_ts.isoformat() if m else None,
        "ret_30d": m.ret_30d if m else None,
        "ret_90d": m.ret_90d if m else None,
        "adx_14": m.adx_14 if m else None,
        "efficiency_30": m.efficiency_30 if m else None,
        "atr_pct_14": m.atr_pct_14 if m else None,
        "direction": m.direction if m else None,
        "strength": m.strength if m else None,
        "score": m.score if m else None,
    }


# ======================================================================
# GET /explorer
# ======================================================================

@router.get("", status_code=200)
def list_explorer(
    asset_class: Optional[str] = Query(default=None, description="Filtrar por clase de activo"),
    _identity: dict = Depends(token_required_actual),
    factory: MarketServiceFactory = Depends(get_factory),
):
    """Símbolos con descarga automática ordenados por fuerza de tendencia (velas 1d)."""
    result = factory.list_trend_explorer().list(asset_class=asset_class)
    if not result.success:
        return build_error_response(result, EXPLORER_ERROR_MESSAGES)
    return build_list_response([_row_to_dict(r) for r in result.data])


# ======================================================================
# POST /explorer/refresh
# ======================================================================

@router.post("/refresh", status_code=200)
def refresh_explorer(
    _identity: dict = Depends(super_admin_required),
    factory: MarketServiceFactory = Depends(get_factory),
):
    """Descarga las velas 1d de todos los símbolos (incluida la del día en curso). Solo admin."""
    result = factory.refresh_explorer_candles().refresh(force=True)
    if not result.success:
        return build_error_response(result, EXPLORER_ERROR_MESSAGES)

    d = result.data
    updated, failed = len(d["updated"]), len(d["failed"])
    msg = f"Datos actualizados: {updated} {'símbolo' if updated == 1 else 'símbolos'}."
    if failed:
        msg += f" {failed} no se pudieron descargar."
    return build_success_response(data=d, msg=msg)
