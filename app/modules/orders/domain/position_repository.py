# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/domain/position_repository.py
#
# Contrato (interfaz ABC) del repositorio de posiciones.
# Las posiciones se crean la primera vez y luego se actualizan;
# no se eliminan (historial de P&L).
# ======================================================================

from __future__ import annotations

from abc import ABC, abstractmethod

from app.modules.orders.domain.position_entity import Position


class PositionRepository(ABC):

    @abstractmethod
    def get_by_bot_and_symbol(self, bot_id: int, symbol_id: int) -> Position | None:
        """
        Obtiene la posición abierta de un bot en un símbolo.
        Retorna None si el bot nunca ha operado ese símbolo.
        """
        ...

    @abstractmethod
    def list_by_bot(self, bot_id: int) -> list[Position]:
        """Lista todas las posiciones abiertas de un bot."""
        ...

    @abstractmethod
    def list_all(self) -> list[Position]:
        """Lista todas las posiciones del sistema (uso admin)."""
        ...

    @abstractmethod
    def create(self, position: Position) -> Position:
        """Persiste una nueva posición. Retorna la entidad con ID asignado."""
        ...

    @abstractmethod
    def update(self, position: Position) -> Position:
        """Actualiza una posición existente. Lanza ValueError si no existe."""
        ...
