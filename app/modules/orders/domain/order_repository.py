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
from dataclasses import dataclass
from datetime import datetime

from app.modules.orders.domain.order_entity import Order
from app.common.contracts import TransactionalRepository


@dataclass(frozen=True)
class OrderCriteria:
    """
    Filtros de los listados de órdenes (mismos en lista simple y paginada).

    `bot_ids`: None = sin filtro (todas, solo admin); [] = ninguna orden
    (p. ej. un dueño sin agentes): el repositorio no consulta.
    """
    bot_ids: list[int] | None = None
    side: str | None = None
    status: str | None = None
    type: str | None = None


class OrderRepository(TransactionalRepository, ABC):

    @abstractmethod
    def get_by_id(self, order_id: int) -> Order | None:
        """Obtiene una orden por su ID. Retorna None si no existe."""
        ...

    @abstractmethod
    def search(self, criteria: OrderCriteria, offset: int = 0, limit: int = 100) -> list[Order]:
        """Órdenes que cumplen `criteria`, la más reciente primero (ts desc, id desc)."""
        ...

    @abstractmethod
    def count(self, criteria: OrderCriteria) -> int:
        """Total de órdenes que cumplen `criteria` (paginación)."""
        ...

    @abstractmethod
    def has_active_order_for_signal(self, signal_id: int) -> bool:
        """True si la señal ya tiene una orden que no fue rechazada ni cancelada."""
        ...

    @abstractmethod
    def list_open_live(self, since: datetime, limit: int = 50) -> list[Order]:
        """Órdenes live sent/partially_filled desde `since` (reconciliación)."""
        ...

    @abstractmethod
    def create(self, order: Order) -> Order:
        """Persiste una nueva orden. Retorna la entidad con ID asignado."""
        ...

    @abstractmethod
    def update(self, order: Order) -> Order:
        """Actualiza una orden existente. Lanza ValueError si no existe."""
        ...
