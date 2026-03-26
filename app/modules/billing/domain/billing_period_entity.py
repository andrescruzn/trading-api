# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/billing/domain/billing_period_entity.py
#
# Entidad de dominio: BillingPeriod.
# Representa un período de facturación con su cálculo de PnL y fee.
# ======================================================================

from __future__ import annotations

from datetime import datetime
from decimal import Decimal


class BillingPeriod:
    """
    Entidad de dominio: BillingPeriod.

    Estado:
    - open   → período en curso, sin fee calculado todavía
    - closed → período cerrado, fee calculado y fee_transaction creada

    Lógica de cálculo al cierre (High-Water Mark):
        gross_pnl = closing_equity - max(opening_equity, high_water_mark)
        Si gross_pnl > 0:
            fee_amount = gross_pnl × fee_pct
            net_pnl    = gross_pnl - fee_amount
        Si gross_pnl <= 0:
            fee_amount = 0
            net_pnl    = gross_pnl  (pérdida, no se cobra)
    """

    STATUS_OPEN = "open"
    STATUS_CLOSED = "closed"

    def __init__(
        self,
        id: int,
        managed_account_id: int,
        opening_equity: Decimal,
        fee_pct: Decimal,
        status: str = "open",
        start_ts: datetime | None = None,
        end_ts: datetime | None = None,
        closing_equity: Decimal | None = None,
        gross_pnl: Decimal | None = None,
        fee_amount: Decimal | None = None,
        net_pnl: Decimal | None = None,
        created_at: datetime | None = None,
        closed_at: datetime | None = None,
    ):
        self.id = id
        self.managed_account_id = managed_account_id
        self.start_ts = start_ts
        self.end_ts = end_ts
        self.opening_equity = opening_equity
        self.closing_equity = closing_equity
        self.gross_pnl = gross_pnl
        self.fee_pct = fee_pct
        self.fee_amount = fee_amount
        self.net_pnl = net_pnl
        self.status = status
        self.created_at = created_at
        self.closed_at = closed_at

    def is_open(self) -> bool:
        return self.status == self.STATUS_OPEN

    def is_closed(self) -> bool:
        return self.status == self.STATUS_CLOSED

    def calculate_fee(self, closing_equity: Decimal, high_water_mark: Decimal) -> None:
        """
        Calcula y aplica la lógica de HWM al cerrar el período.

        El gross_pnl se mide contra el máximo entre opening_equity y el HWM,
        de modo que el inversor solo paga fee sobre ganancias NUEVAS.

        Args:
            closing_equity:   equity al momento del cierre
            high_water_mark:  HWM actual de la managed_account
        """
        self.closing_equity = closing_equity
        baseline = max(self.opening_equity, high_water_mark)
        self.gross_pnl = closing_equity - baseline

        if self.gross_pnl > Decimal("0"):
            self.fee_amount = (self.gross_pnl * self.fee_pct).quantize(Decimal("0.000001"))
            self.net_pnl = self.gross_pnl - self.fee_amount
        else:
            # Pérdida o neutro → sin fee
            self.fee_amount = Decimal("0")
            self.net_pnl = self.gross_pnl

    def has_fee_to_charge(self) -> bool:
        """Devuelve True si hay fee positivo para registrar."""
        return self.fee_amount is not None and self.fee_amount > Decimal("0")
