# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/domain/signal_repository.py
#
# Contrato (interfaz ABC) del repositorio de signals.
# ======================================================================

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from app.modules.bots.domain.signal_entity import Signal
from app.common.contracts import TransactionalRepository


class SignalRepository(TransactionalRepository, ABC):

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
    def exists_for_candle(self, bot_id: int, candle_ts: datetime) -> bool:
        """True si el bot ya tiene una señal automática para esa vela."""
        ...

    @abstractmethod
    def count_created_since(self, bot_ids: list[int], since: datetime) -> int:
        """Señales creadas desde `since` por esos bots (límite diario de la IA)."""
        ...

    @abstractmethod
    def list_by_decision_status(
        self,
        decision_status: str,
        bot_ids: list[int] | None = None,
        limit: int = 100,
    ) -> list[Signal]:
        """Señales en un estado de decisión (bot_ids=None → de todos los bots)."""
        ...

    @abstractmethod
    def transition_decision(
        self,
        signal_id: int,
        from_statuses: tuple[str, ...],
        to_status: str,
        **fields: Any,
    ) -> bool:
        """
        Cambia decision_status solo si el actual está en `from_statuses`
        (UPDATE condicional). Devuelve False si otra decisión llegó antes.
        """
        ...

    @abstractmethod
    def expire_pending(self, now: datetime) -> list[int]:
        """Marca `expired` las pendientes vencidas y devuelve sus IDs."""
        ...

    @abstractmethod
    def create(self, signal: Signal) -> Signal:
        """Persiste una nueva signal. Retorna la entidad con ID asignado."""
        ...
