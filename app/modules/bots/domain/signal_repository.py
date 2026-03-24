# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/domain/signal_repository.py
#
# Contrato (interfaz ABC) del repositorio de signals.
# ======================================================================

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from app.modules.bots.domain.signal_entity import Signal


class SignalRepository(ABC):

    @abstractmethod
    def get_by_id(self, signal_id: int) -> Signal | None:
        """Obtiene una signal por su ID. Retorna None si no existe."""
        ...

    @abstractmethod
    def list_by_bot(
        self,
        bot_id: int,
        action: str | None = None,
        from_ts: datetime | None = None,
        to_ts: datetime | None = None,
        limit: int = 50,
    ) -> list[Signal]:
        """
        Lista signals de un bot con filtros opcionales.

        Args:
            bot_id  : ID del bot propietario de las signals
            action  : filtrar por acción (buy/sell/hold)
            from_ts : timestamp de inicio del rango
            to_ts   : timestamp de fin del rango
            limit   : máximo de resultados (default 50, max 500)
        """
        ...

    @abstractmethod
    def create(self, signal: Signal) -> Signal:
        """Persiste una nueva signal. Retorna la entidad con ID asignado."""
        ...
