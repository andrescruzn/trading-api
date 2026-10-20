# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/billing/domain/capital_movement_entity.py
#
# Aporte (deposit) o retiro (withdrawal) del inversor en una cuenta
# gestionada.
# ======================================================================

from __future__ import annotations

from datetime import datetime
from decimal import Decimal


class CapitalMovement:
    KINDS = ("deposit", "withdrawal")

    def __init__(
        self,
        id: int,
        managed_account_id: int,
        kind: str,
        amount: Decimal,
        ts: datetime,
        notes: str | None = None,
        created_by_user_id: int | None = None,
        created_at: datetime | None = None,
    ):
        self.id = id
        self.managed_account_id = managed_account_id
        self.kind = kind
        self.amount = amount
        self.ts = ts
        self.notes = notes
        self.created_by_user_id = created_by_user_id
        self.created_at = created_at

    def signed_amount(self) -> Decimal:
        """Positivo si entra dinero, negativo si sale."""
        return self.amount if self.kind == "deposit" else -self.amount
