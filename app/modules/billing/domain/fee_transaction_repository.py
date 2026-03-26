# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/billing/domain/fee_transaction_repository.py
#
# Contrato (Protocol) para el repositorio de FeeTransaction.
# ======================================================================

from __future__ import annotations

from typing import Protocol

from app.modules.billing.domain.fee_transaction_entity import FeeTransaction


class FeeTransactionRepository(Protocol):
    """Contrato para el repositorio de transacciones de fee."""

    def find_by_id(self, fee_tx_id: int) -> FeeTransaction | None: ...

    def find_by_period(self, billing_period_id: int) -> FeeTransaction | None: ...

    def list_by_managed_account(
        self, managed_account_id: int, limit: int = 50
    ) -> list[FeeTransaction]: ...

    def save(self, fee_tx: FeeTransaction) -> FeeTransaction: ...

    def update(self, fee_tx: FeeTransaction) -> FeeTransaction: ...
