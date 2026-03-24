# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/services/orders/list_orders_service.py
#
# Lista órdenes de un bot. Admin ve todas las del sistema.
# ======================================================================

from __future__ import annotations

from app.common.contracts import ServiceResult
from app.modules.orders.domain.order_entity import Order
from app.modules.orders.domain.order_repository import OrderRepository


class ListOrdersService:
    """
    Lista órdenes del sistema.

    Reglas de negocio:
    - Admin (bot_id=None): retorna las órdenes más recientes del sistema.
    - Usuario normal: requiere bot_id para filtrar por su bot.
    """

    def __init__(self, repo: OrderRepository):
        self._repo = repo

    def list(
        self,
        bot_id: int | None = None,
        limit: int = 100,
    ) -> ServiceResult[list[Order]]:
        if bot_id is not None:
            orders = self._repo.list_by_bot(bot_id=bot_id, limit=limit)
        else:
            orders = self._repo.list_all(limit=limit)

        return ServiceResult.ok(data=orders)
