# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/billing/domain/managed_account_repository.py
#
# Contrato (Protocol) para el repositorio de ManagedAccount.
# ======================================================================

from __future__ import annotations

from decimal import Decimal
from typing import Protocol

from app.modules.billing.domain.managed_account_entity import ManagedAccount


class ManagedAccountRepository(Protocol):
    """Contrato para el repositorio de cuentas gestionadas."""

    def find_by_id(self, managed_account_id: int) -> ManagedAccount | None: ...

    def list_by_investor(self, investor_id: int) -> list[ManagedAccount]: ...

    def list_all(self, only_active: bool = False) -> list[ManagedAccount]: ...

    def save(self, managed_account: ManagedAccount) -> ManagedAccount: ...

    def update_high_water_mark(
        self, managed_account_id: int, new_hwm: Decimal
    ) -> None: ...
