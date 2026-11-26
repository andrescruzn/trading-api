# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/domain/funding_repository.py
#
# Contrato del repositorio de pagos de funding (perpetuos en live).
# ======================================================================

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal

from app.common.contracts import TransactionalRepository
from app.modules.orders.domain.funding_entity import FundingPayment


class FundingRepository(TransactionalRepository, ABC):

    @abstractmethod
    def latest_ts(self, bot_id: int) -> datetime | None:
        """Fecha del último funding guardado del bot (para pedir solo lo nuevo)."""
        ...

    @abstractmethod
    def add_new(self, payments: list[FundingPayment]) -> int:
        """
        Guarda los que no existan (UNIQUE cuenta + id del exchange) y devuelve
        cuántos se guardaron. Sin commit.
        """
        ...

    @abstractmethod
    def total_after(self, bot_id: int, after_id: int) -> tuple[Decimal, int]:
        """
        Suma del funding del bot con id > `after_id` y el último id sumado
        (`after_id` si no hay nuevos). Lo usa el fondo común.
        """
        ...

    @abstractmethod
    def total_by_bot(self, bot_id: int) -> Decimal:
        """Todo el funding del bot (rendimiento)."""
        ...
