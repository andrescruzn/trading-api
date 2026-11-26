# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/accounts/domain/account_balance_entity.py
#
# Entidad de dominio: AccountBalance.
# Representa un snapshot del saldo de un activo en una cuenta.
# ======================================================================

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional


class AccountBalance:
    """
    Entidad de dominio: AccountBalance.

    Cada registro es un snapshot puntual del saldo de un activo (asset)
    dentro de una cuenta. La serie temporal de snapshots forma la
    curva de equity por activo.

    Invariantes:
    - free >= 0
    - locked >= 0
    """

    def __init__(
        self,
        id: int,
        account_id: int,
        asset: str,
        free: Decimal,
        locked: Decimal,
        ts: Optional[datetime] = None,
    ):
        self.id = id
        self.account_id = account_id
        self.asset = asset
        self.free = free
        self.locked = locked
        self.ts = ts

    @property
    def total(self) -> Decimal:
        """Balance total = libre + bloqueado."""
        return self.free + self.locked
