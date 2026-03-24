# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/rest/orders/routes.py
#
# ENDPOINTS:
# - POST /orders         → crear y ejecutar una orden
# - GET  /orders         → listar órdenes (admin: todas; user: por bot_id)
# - GET  /orders/{id}    → detalle de una orden
# ======================================================================

from __future__ import annotations

from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.config import settings
from app.common.http import (
    build_created_response,
    build_error_response,
    build_list_response,
    build_success_response,
    send,
)
from app.common.security.jwt import token_required_actual
from app.extensions.db import get_db
from app.modules.orders.domain.order_entity import Order
from app.modules.orders.providers import OrderServiceFactory, get_order_factory

from .error_messages import ORDER_ERROR_MESSAGES
from .schemas import CreateOrderRequest

router = APIRouter(prefix="/api/orders", tags=["Orders"])


# ======================================================================
# Dependency
# ======================================================================

def get_factory(db: Session = Depends(get_db)) -> OrderServiceFactory:
    return get_order_factory(db)


# ======================================================================
# Serializer — Order entity → dict JSON-safe
# ======================================================================

def _decimal_or_none(val: Decimal | None) -> float | None:
    """Convierte Decimal a float para JSON. None permanece None."""
    return float(val) if val is not None else None


def _order_to_dict(o: Order) -> dict[str, Any]:
    return {
        "id":                  o.id,
        "bot_id":              o.bot_id,
        "signal_id":           o.signal_id,
        "exchange_order_id":   o.exchange_order_id,
        "side":                o.side,
        "type":                o.type,
        "status":              o.status,
        "qty":                 _decimal_or_none(o.qty),
        "price":               _decimal_or_none(o.price),
        "stop_price":          _decimal_or_none(o.stop_price),
        "time_in_force":       o.time_in_force,
        "meta":                o.meta,
        "ts":                  o.ts.isoformat() if o.ts else None,
        "created_at":          o.created_at.isoformat() if o.created_at else None,
    }


# ======================================================================
# POST /orders
# ======================================================================

@router.post("", status_code=201)
def create_order(
    payload: CreateOrderRequest,
    identity: dict = Depends(token_required_actual),
    factory: OrderServiceFactory = Depends(get_factory),
):
    """
    Crea y ejecuta una orden de trading.

    El bot debe estar en estado 'running'. La orden se ejecuta
    inmediatamente via PaperExecutor (paper) o LiveExecutor (live)
    y se persiste junto con el Fill y la actualización de Position.
    """
    result = factory.create_order().create(
        bot_id=payload.bot_id,
        side=payload.side,
        order_type=payload.type,
        qty=payload.qty,
        price=payload.price,
        stop_price=payload.stop_price,
        time_in_force=payload.time_in_force,
        signal_id=payload.signal_id,
    )

    if not result.success:
        return build_error_response(result, ORDER_ERROR_MESSAGES)

    return build_created_response(
        data=_order_to_dict(result.data),
        msg="Orden ejecutada exitosamente.",
    )


# ======================================================================
# GET /orders
# ======================================================================

@router.get("", status_code=200)
def list_orders(
    bot_id: int | None = Query(default=None, gt=0),
    limit:  int        = Query(default=100, ge=1, le=500),
    identity: dict = Depends(token_required_actual),
    factory: OrderServiceFactory = Depends(get_factory),
):
    """
    Lista órdenes.
    - Admin: puede listar todas las órdenes o filtrar por bot_id.
    - Usuario: debe proveer bot_id para ver solo las órdenes de su bot.
    """
    is_admin = int(identity.get("role_id", 0)) == int(settings.AUTH_ADMIN_ROLE_ID)

    if not is_admin and bot_id is None:
        return send(msg="Debes indicar bot_id para listar tus órdenes.", status_code=400)

    result = factory.list_orders().list(bot_id=bot_id, limit=limit)

    return build_list_response(
        items=[_order_to_dict(o) for o in (result.data or [])],
        msg="OK",
    )


# ======================================================================
# GET /orders/{order_id}
# ======================================================================

@router.get("/{order_id}", status_code=200)
def get_order(
    order_id: int,
    identity: dict = Depends(token_required_actual),
    factory: OrderServiceFactory = Depends(get_factory),
):
    """Obtiene el detalle de una orden por su ID."""
    result = factory.get_order().get(order_id=order_id)

    if not result.success:
        return build_error_response(result, ORDER_ERROR_MESSAGES)

    return build_success_response(data=_order_to_dict(result.data), msg="OK")
