# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/domain/fill_repository.py
#
# Contrato (interfaz ABC) del repositorio de fills.
# Los fills son inmutables una vez creados — solo se crean, no se editan.
# ======================================================================

from __future__ import annotations

from abc import ABC, abstractmethod

from app.modules.orders.domain.fill_entity import BotFill, Fill
from app.common.contracts import TransactionalRepository
from app.modules.orders.domain.performance import TradeFill


class FillRepository(TransactionalRepository, ABC):

    @abstractmethod
    def list_by_order(self, order_id: int) -> list[Fill]:
        """Lista todos los fills de una orden específica."""
        ...

    @abstractmethod
    def list_by_bot(self, bot_id: int, limit: int = 200) -> list[Fill]:
        """Lista los fills más recientes de un bot (via join con orders)."""
        ...

    @abstractmethod
    def list_trade_fills_by_bots(self, bot_ids: list[int]) -> dict[int, list[TradeFill]]:
        """Todos los fills de esos bots con el lado de su orden, por bot y por fecha."""
        ...

    @abstractmethod
    def list_by_bot_after(self, bot_id: int, after_fill_id: int) -> list[BotFill]:
        """
        Fills del bot con id > `after_fill_id`, del más viejo al más nuevo.
        Lo usa el fondo común: lo operado desde la última liquidación.
        """
        ...

    @abstractmethod
    def max_id_by_bot(self, bot_id: int) -> int:
        """Id del último fill del bot (0 si no tiene)."""
        ...

    @abstractmethod
    def create(self, fill: Fill) -> Fill:
        """Persiste un nuevo fill. Retorna la entidad con ID asignado."""
        ...
