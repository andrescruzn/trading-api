# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/rest/positions/routes.py
#
# ENDPOINTS:
# - GET /positions → listar posiciones (admin: todas; user: por bot_id)
# ======================================================================

from __future__ import annotations

from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.config import settings
from app.common.http import build_list_response, send
from app.common.security.jwt import token_required_actual
from app.extensions.db import get_db
from app.modules.orders.domain.position_entity import Position
from app.modules.orders.providers import OrderServiceFactory, get_order_factory

router = APIRouter(prefix="/api/positions", tags=["Positions"])


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


def _position_to_dict(p: Position) -> dict[str, Any]:
    return {
        "id":            p.id,
        "bot_id":        p.bot_id,
        "symbol_id":     p.symbol_id,
        "qty":           _decimal_or_none(p.qty),
        "avg_price":     _decimal_or_none(p.avg_price),
        "realized_pnl":  _decimal_or_none(p.realized_pnl),
        "is_flat":       p.is_flat(),
        "updated_at":    p.updated_at.isoformat() if p.updated_at else None,
    }


# ======================================================================
# GET /positions
# ======================================================================

@router.get("", status_code=200)
def list_positions(
    bot_id: int | None = Query(default=None, gt=0),
    identity: dict = Depends(token_required_actual),
    factory: OrderServiceFactory = Depends(get_factory),
):
    """
    Lista posiciones abiertas.
    - Admin: puede ver todas las posiciones del sistema.
    - Usuario: debe proveer bot_id para ver solo las de su bot.
    """
    is_admin = int(identity.get("role_id", 0)) == int(settings.AUTH_ADMIN_ROLE_ID)

    if not is_admin and bot_id is None:
        return send(msg="Debes indicar bot_id para ver tus posiciones.", status_code=400)

    result = factory.list_positions().list(bot_id=bot_id)

    return build_list_response(
        items=[_position_to_dict(p) for p in (result.data or [])],
        msg="OK",
    )
