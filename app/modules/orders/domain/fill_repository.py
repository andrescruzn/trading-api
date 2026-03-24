# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/domain/fill_repository.py
#
# Contrato (interfaz ABC) del repositorio de fills.
# Los fills son inmutables una vez creados — solo se crean, no se editan.
# ======================================================================

from __future__ import annotations

from abc import ABC, abstractmethod

from app.modules.orders.domain.fill_entity import Fill


class FillRepository(ABC):

    @abstractmethod
    def list_by_order(self, order_id: int) -> list[Fill]:
        """Lista todos los fills de una orden específica."""
        ...

    @abstractmethod
    def list_by_bot(self, bot_id: int, limit: int = 200) -> list[Fill]:
        """Lista los fills más recientes de un bot (via join con orders)."""
        ...

    @abstractmethod
    def create(self, fill: Fill) -> Fill:
        """Persiste un nuevo fill. Retorna la entidad con ID asignado."""
        ...
