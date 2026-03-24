# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/services/positions/list_positions_service.py
#
# Lista posiciones abiertas de un bot o del sistema completo (admin).
# ======================================================================

from __future__ import annotations

from app.common.contracts import ServiceResult
from app.modules.orders.domain.position_entity import Position
from app.modules.orders.domain.position_repository import PositionRepository


class ListPositionsService:
    """
    Lista posiciones del sistema.

    Reglas de negocio:
    - Admin (bot_id=None): retorna todas las posiciones del sistema.
    - Usuario normal: requiere bot_id para ver solo sus posiciones.
    """

    def __init__(self, repo: PositionRepository):
        self._repo = repo

    def list(
        self,
        bot_id: int | None = None,
    ) -> ServiceResult[list[Position]]:
        if bot_id is not None:
            positions = self._repo.list_by_bot(bot_id=bot_id)
        else:
            positions = self._repo.list_all()

        return ServiceResult.ok(data=positions)
