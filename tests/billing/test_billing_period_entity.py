# -*- coding: utf-8 -*-

# ======================================================================
# tests/billing/test_billing_period_entity.py
#
# Tests unitarios de la entidad BillingPeriod.
#
# ESTRATEGIA:
# - Sin mocks ni I/O. Solo Python puro.
# - Foco en la lógica de High-Water Mark (el corazón del módulo 10).
#
# NOMENCLATURA:
#   test_<método>_<condición>_<resultado_esperado>
# ======================================================================

from __future__ import annotations

from decimal import Decimal

import pytest

from app.modules.billing.domain.billing_period_entity import BillingPeriod


# ======================================================================
# Helpers
# ======================================================================

def make_period(
    opening_equity: str = "10000",
    fee_pct: str = "0.2000",
    status: str = "open",
) -> BillingPeriod:
    return BillingPeriod(
        id=1,
        managed_account_id=1,
        opening_equity=Decimal(opening_equity),
        fee_pct=Decimal(fee_pct),
        status=status,
    )


# ======================================================================
# TestBillingPeriodStatus — is_open / is_closed
# ======================================================================

class TestBillingPeriodStatus:

    def test_new_period_is_open(self):
        p = make_period(status="open")
        assert p.is_open() is True
        assert p.is_closed() is False

    def test_closed_period_is_closed(self):
        p = make_period(status="closed")
        assert p.is_closed() is True
        assert p.is_open() is False


# ======================================================================
# TestCalculateFee — lógica HWM (caso principal del módulo)
# ======================================================================

class TestCalculateFeeHWMLogic:
    """
    Escenarios del High-Water Mark:

      ① Ganancia normal (closing > opening y HWM):
         fee = (closing - max(opening, hwm)) * fee_pct

      ② HWM mayor que opening:
         Solo se cobra fee sobre el excedente al HWM, no al opening.

      ③ Pérdida: closing < opening → fee = 0

      ④ Neutro: closing == opening → fee = 0

      ⑤ Recuperación sin superar HWM: fee = 0
    """

    def test_normal_gain_charges_fee_on_profit(self):
        """Ganancia normal: 10000 → 10800. HWM=10000. Fee 20% sobre 800 = 160."""
        p = make_period(opening_equity="10000", fee_pct="0.2000")
        p.calculate_fee(Decimal("10800"), Decimal("10000"))

        assert p.gross_pnl == Decimal("800")
        assert p.fee_amount == Decimal("160.000000")
        assert p.net_pnl == Decimal("640.000000")

    def test_hwm_higher_than_opening_reduces_fee_base(self):
        """
        HWM > opening: el período abre en $9000 pero el HWM previo era $10000.
        Closing = $10500. Solo cobra fee sobre $500 (no sobre $1500).
        """
        p = make_period(opening_equity="9000", fee_pct="0.2000")
        p.calculate_fee(Decimal("10500"), high_water_mark=Decimal("10000"))

        # baseline = max(9000, 10000) = 10000
        assert p.gross_pnl == Decimal("500")
        assert p.fee_amount == Decimal("100.000000")
        assert p.net_pnl == Decimal("400.000000")

    def test_loss_results_in_zero_fee(self):
        """Pérdida: 10000 → 9500. Fee = 0."""
        p = make_period(opening_equity="10000", fee_pct="0.2000")
        p.calculate_fee(Decimal("9500"), Decimal("10000"))

        assert p.gross_pnl == Decimal("-500")
        assert p.fee_amount == Decimal("0")
        assert p.net_pnl == Decimal("-500")

    def test_neutral_break_even_results_in_zero_fee(self):
        """Sin ganancia ni pérdida: closing == opening. Fee = 0."""
        p = make_period(opening_equity="10000", fee_pct="0.2000")
        p.calculate_fee(Decimal("10000"), Decimal("10000"))

        assert p.gross_pnl == Decimal("0")
        assert p.fee_amount == Decimal("0")
        assert p.net_pnl == Decimal("0")

    def test_recovery_below_hwm_results_in_zero_fee(self):
        """
        Recuperación sin superar HWM: abre en $9000, HWM previo $11000,
        cierra en $10500 (subió pero NO superó el HWM). Fee = 0.
        """
        p = make_period(opening_equity="9000", fee_pct="0.2000")
        p.calculate_fee(Decimal("10500"), high_water_mark=Decimal("11000"))

        # baseline = max(9000, 11000) = 11000
        # gross_pnl = 10500 - 11000 = -500 → fee = 0
        assert p.gross_pnl == Decimal("-500")
        assert p.fee_amount == Decimal("0")

    def test_closing_equity_is_stored(self):
        """calculate_fee debe almacenar el closing_equity recibido."""
        p = make_period(opening_equity="10000")
        p.calculate_fee(Decimal("11000"), Decimal("10000"))
        assert p.closing_equity == Decimal("11000")

    def test_fee_pct_zero_generates_no_fee(self):
        """fee_pct = 0 → fee_amount = 0 aunque haya ganancia."""
        p = make_period(opening_equity="10000", fee_pct="0.0000")
        p.calculate_fee(Decimal("12000"), Decimal("10000"))

        assert p.fee_amount == Decimal("0.000000")
        assert p.net_pnl == Decimal("2000")

    def test_fee_pct_full_100_percent(self):
        """fee_pct = 1.0 (100%) → el inversor no recibe nada de la ganancia."""
        p = make_period(opening_equity="10000", fee_pct="1.0000")
        p.calculate_fee(Decimal("11000"), Decimal("10000"))

        assert p.fee_amount == Decimal("1000.000000")
        assert p.net_pnl == Decimal("0.000000")


# ======================================================================
# TestHasFeeToCarge
# ======================================================================

class TestHasFeeToCarge:

    def test_returns_true_when_fee_positive(self):
        p = make_period(opening_equity="10000", fee_pct="0.2000")
        p.calculate_fee(Decimal("11000"), Decimal("10000"))
        assert p.has_fee_to_charge() is True

    def test_returns_false_when_fee_zero(self):
        p = make_period(opening_equity="10000", fee_pct="0.2000")
        p.calculate_fee(Decimal("9500"), Decimal("10000"))
        assert p.has_fee_to_charge() is False

    def test_returns_false_before_calculate_fee(self):
        """Antes de llamar calculate_fee, fee_amount es None."""
        p = make_period()
        assert p.has_fee_to_charge() is False
