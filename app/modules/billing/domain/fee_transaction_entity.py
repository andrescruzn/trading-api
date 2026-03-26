# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/billing/domain/fee_transaction_entity.py
#
# Entidad de dominio: FeeTransaction.
# Registro auditable de cada cobro de performance fee.
# Un billing_period cerrado con fee > 0 genera exactamente una FeeTransaction.
# ======================================================================

from __future__ import annotations

from datetime import datetime
from decimal import Decimal


class FeeTransaction:
    """
    Entidad de dominio: FeeTransaction.

    Estado:
    - pending  → fee calculada, aún no cobrada
    - charged  → fee efectivamente cobrada / descontada del capital
    - waived   → fee condonada por decisión administrativa
    """

    STATUS_PENDING = "pending"
    STATUS_CHARGED = "charged"
    STATUS_WAIVED = "waived"

    def __init__(
        self,
        id: int,
        billing_period_id: int,
        managed_account_id: int,
        amount: Decimal,
        status: str = "pending",
        charged_at: datetime | None = None,
        notes: str | None = None,
        created_at: datetime | None = None,
    ):
        self.id = id
        self.billing_period_id = billing_period_id
        self.managed_account_id = managed_account_id
        self.amount = amount
        self.status = status
        self.charged_at = charged_at
        self.notes = notes
        self.created_at = created_at

    def is_pending(self) -> bool:
        return self.status == self.STATUS_PENDING

    def is_charged(self) -> bool:
        return self.status == self.STATUS_CHARGED

    def mark_as_charged(self, charged_at: datetime) -> None:
        """Marca la fee como cobrada."""
        self.status = self.STATUS_CHARGED
        self.charged_at = charged_at

    def waive(self, notes: str | None = None) -> None:
        """Condona la fee con notas opcionales."""
        self.status = self.STATUS_WAIVED
        self.notes = notes
