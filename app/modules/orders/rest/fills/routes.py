# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/rest/fills/routes.py
#
# ENDPOINTS:
# - GET /fills → listar fills de una orden o de un bot
# ======================================================================

from __future__ import annotations

from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.http import build_error_response, build_list_response
from app.common.security.jwt import token_required_actual
from app.extensions.db import get_db
from app.modules.orders.domain.fill_entity import Fill
from app.modules.orders.providers import OrderServiceFactory, get_order_factory

from .error_messages import FILL_ERROR_MESSAGES

router = APIRouter(prefix="/api/fills", tags=["Fills"])


# ======================================================================
# Dependency
# ======================================================================

def get_factory(db: Session = Depends(get_db)) -> OrderServiceFactory:
    return get_order_factory(db)


# ======================================================================
# Serializer
# ======================================================================

def _decimal_or_none(val: Decimal | None) -> float | None:
    return float(val) if val is not None else None


def _fill_to_dict(f: Fill) -> dict[str, Any]:
    return {
        "id":                f.id,
        "order_id":          f.order_id,
        "exchange_trade_id": f.exchange_trade_id,
        "qty":               _decimal_or_none(f.qty),
        "price":             _decimal_or_none(f.price),
        "fee":               _decimal_or_none(f.fee),
        "fee_asset":         f.fee_asset,
        "notional_value":    _decimal_or_none(f.notional_value()),
        "ts":                f.ts.isoformat() if f.ts else None,
        "created_at":        f.created_at.isoformat() if f.created_at else None,
    }


# ======================================================================
# GET /fills
# ======================================================================

@router.get("", status_code=200)
def list_fills(
    order_id: int | None = Query(default=None, gt=0),
    bot_id:   int | None = Query(default=None, gt=0),
    limit:    int        = Query(default=200, ge=1, le=500),
    identity: dict = Depends(token_required_actual),
    factory: OrderServiceFactory = Depends(get_factory),
):
    """
    Lista fills. Requiere al menos uno de: order_id o bot_id.

    - ?order_id=X : todos los fills de esa orden específica.
    - ?bot_id=X   : fills recientes del bot (via JOIN con orders).
    """
    result = factory.list_fills().list(
        order_id=order_id,
        bot_id=bot_id,
        limit=limit,
    )

    if not result.success:
        return build_error_response(result, FILL_ERROR_MESSAGES)

    return build_list_response(
        items=[_fill_to_dict(f) for f in (result.data or [])],
        msg="OK",
    )
