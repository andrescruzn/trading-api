# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/billing/domain/managed_account_entity.py
#
# Entidad de dominio: ManagedAccount.
# Une a un inversor con la cuenta de trading que el bot opera.
# Guarda el High-Water Mark (HWM) para el cálculo de performance fee.
# ======================================================================

from __future__ import annotations

from datetime import datetime
from decimal import Decimal


class ManagedAccount:
    """
    Entidad de dominio: ManagedAccount.

    Vincula:
    - investor_id → quién aportó el capital
    - account_id  → cuenta de trading M4 donde se opera
    - bot_id      → bot que ejecuta las órdenes (nullable)

    High-Water Mark (HWM):
    Solo se cobra fee sobre equity que supere el HWM.
    Al cerrar un período con ganancia, el HWM se actualiza al closing_equity.

    period_type: frecuencia de facturación (daily | weekly | monthly).
    """

    VALID_PERIOD_TYPES = ("daily", "weekly", "monthly")

    def __init__(
        self,
        id: int,
        investor_id: int,
        account_id: int,
        name: str,
        initial_capital: Decimal,
        high_water_mark: Decimal,
        period_type: str = "monthly",
        bot_id: int | None = None,
        is_active: bool = True,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        self.id = id
        self.investor_id = investor_id
        self.account_id = account_id
        self.bot_id = bot_id
        self.name = name
        self.initial_capital = initial_capital
        self.high_water_mark = high_water_mark
        self.period_type = period_type
        self.is_active = is_active
        self.created_at = created_at
        self.updated_at = updated_at

    def is_valid_period_type(self) -> bool:
        return self.period_type in self.VALID_PERIOD_TYPES

    def update_high_water_mark(self, new_equity: Decimal) -> None:
        """
        Actualiza el HWM solo si new_equity supera el valor actual.
        Se llama al cerrar un período con gross_pnl > 0.
        """
        if new_equity > self.high_water_mark:
            self.high_water_mark = new_equity
