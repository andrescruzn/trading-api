# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/billing/domain/capital_movement_repository.py
#
# Contrato (Protocol) para el repositorio de CapitalMovement.
# ======================================================================

from __future__ import annotations

from typing import Protocol

from app.common.contracts import TransactionalRepository
from app.modules.billing.domain.capital_movement_entity import CapitalMovement


class CapitalMovementRepository(TransactionalRepository, Protocol):
    """Contrato para el repositorio de aportes y retiros."""

    def list_by_managed_account(self, managed_account_id: int) -> list[CapitalMovement]:
        """Movimientos de la cuenta, del más reciente al más antiguo."""
        ...

    def save(self, movement: CapitalMovement) -> CapitalMovement: ...
