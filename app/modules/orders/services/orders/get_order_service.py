# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/services/orders/get_order_service.py
#
# Obtiene el detalle de una orden por ID.
# ======================================================================

from __future__ import annotations

from app.common.contracts import ServiceResult
from app.modules.orders.domain.order_entity import Order
from app.modules.orders.domain.order_repository import OrderRepository


class GetOrderService:
    """Retorna el detalle de una orden por su ID."""

    def __init__(self, repo: OrderRepository):
        self._repo = repo

    def get(self, order_id: int) -> ServiceResult[Order]:
        order = self._repo.get_by_id(order_id)
        if order is None:
            return ServiceResult.fail(code="ORDER_NOT_FOUND", http_status=404)

        return ServiceResult.ok(data=order)
