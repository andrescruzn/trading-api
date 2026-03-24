# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/services/fills/list_fills_service.py
#
# Lista los fills de una orden o de un bot completo.
# ======================================================================

from __future__ import annotations

from app.common.contracts import ServiceResult
from app.modules.orders.domain.fill_entity import Fill
from app.modules.orders.domain.fill_repository import FillRepository
from app.modules.orders.domain.order_repository import OrderRepository


class ListFillsService:
    """
    Lista fills del sistema.

    Reglas de negocio:
    - Si se pasa order_id: retorna todos los fills de esa orden.
    - Si se pasa bot_id: retorna los fills recientes de ese bot (via JOIN).
    - Al menos uno de los dos debe estar presente.
    """

    def __init__(self, fill_repo: FillRepository, order_repo: OrderRepository):
        self._fill_repo = fill_repo
        self._order_repo = order_repo

    def list(
        self,
        order_id: int | None = None,
        bot_id: int | None = None,
        limit: int = 200,
    ) -> ServiceResult[list[Fill]]:
        if order_id is None and bot_id is None:
            return ServiceResult.fail(
                code="FILLS_MISSING_FILTER",
                http_status=422,
            )

        if order_id is not None:
            # Verificar que la orden exista antes de listar fills
            order = self._order_repo.get_by_id(order_id)
            if order is None:
                return ServiceResult.fail(code="ORDER_NOT_FOUND", http_status=404)
            fills = self._fill_repo.list_by_order(order_id=order_id)
        else:
            fills = self._fill_repo.list_by_bot(bot_id=bot_id, limit=limit)

        return ServiceResult.ok(data=fills)
