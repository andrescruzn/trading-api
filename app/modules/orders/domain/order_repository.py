# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/domain/order_repository.py
#
# Contrato (interfaz ABC) del repositorio de órdenes.
# La capa infrastructure implementa este contrato con SQLAlchemy.
# Los servicios dependen de esta abstracción, nunca de la impl concreta.
# ======================================================================

from __future__ import annotations

from abc import ABC, abstractmethod

from app.modules.orders.domain.order_entity import Order


class OrderRepository(ABC):

    @abstractmethod
    def get_by_id(self, order_id: int) -> Order | None:
        """Obtiene una orden por su ID. Retorna None si no existe."""
        ...

    @abstractmethod
    def list_by_bot(self, bot_id: int, limit: int = 100) -> list[Order]:
        """Lista las órdenes más recientes de un bot específico."""
        ...

    @abstractmethod
    def list_all(self, limit: int = 200) -> list[Order]:
        """Lista las órdenes más recientes del sistema (uso admin)."""
        ...

    @abstractmethod
    def create(self, order: Order) -> Order:
        """Persiste una nueva orden. Retorna la entidad con ID asignado."""
        ...

    @abstractmethod
    def update(self, order: Order) -> Order:
        """Actualiza una orden existente. Lanza ValueError si no existe."""
        ...
