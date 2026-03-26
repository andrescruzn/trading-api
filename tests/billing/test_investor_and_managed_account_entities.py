# -*- coding: utf-8 -*-

# ======================================================================
# tests/billing/test_investor_and_managed_account_entities.py
#
# Tests unitarios de las entidades Investor y ManagedAccount.
# Sin mocks ni I/O — Python puro.
# ======================================================================

from __future__ import annotations

from decimal import Decimal

import pytest

from app.modules.billing.domain.investor_entity import Investor
from app.modules.billing.domain.managed_account_entity import ManagedAccount


# ======================================================================
# Helpers
# ======================================================================

def make_investor(fee_pct: str = "0.2000", is_active: bool = True) -> Investor:
    return Investor(id=1, user_id=10, fee_pct=Decimal(fee_pct), is_active=is_active)


def make_account(
    initial_capital: str = "10000",
    high_water_mark: str = "10000",
    period_type: str = "monthly",
) -> ManagedAccount:
    return ManagedAccount(
        id=1,
        investor_id=1,
        account_id=5,
        name="Test Account",
        initial_capital=Decimal(initial_capital),
        high_water_mark=Decimal(high_water_mark),
        period_type=period_type,
    )


# ======================================================================
# TestInvestorEntity
# ======================================================================

class TestInvestorEntity:

    def test_valid_fee_pct_zero(self):
        assert make_investor("0.0000").is_valid_fee_pct() is True

    def test_valid_fee_pct_one(self):
        assert make_investor("1.0000").is_valid_fee_pct() is True

    def test_valid_fee_pct_typical(self):
        assert make_investor("0.2000").is_valid_fee_pct() is True

    def test_invalid_fee_pct_negative(self):
        inv = Investor(id=1, user_id=1, fee_pct=Decimal("-0.01"))
        assert inv.is_valid_fee_pct() is False

    def test_invalid_fee_pct_above_one(self):
        inv = Investor(id=1, user_id=1, fee_pct=Decimal("1.0001"))
        assert inv.is_valid_fee_pct() is False

    def test_fee_as_percentage_20_percent(self):
        assert make_investor("0.2000").fee_as_percentage() == "20.00%"

    def test_fee_as_percentage_zero(self):
        assert make_investor("0.0000").fee_as_percentage() == "0.00%"

    def test_fee_as_percentage_50_percent(self):
        assert make_investor("0.5000").fee_as_percentage() == "50.00%"


# ======================================================================
# TestManagedAccountEntity
# ======================================================================

class TestManagedAccountEntity:

    def test_valid_period_types(self):
        for pt in ("daily", "weekly", "monthly"):
            assert make_account(period_type=pt).is_valid_period_type() is True

    def test_invalid_period_type(self):
        acc = make_account(period_type="yearly")
        assert acc.is_valid_period_type() is False

    def test_update_hwm_increases_when_higher(self):
        acc = make_account(high_water_mark="10000")
        acc.update_high_water_mark(Decimal("11000"))
        assert acc.high_water_mark == Decimal("11000")

    def test_update_hwm_does_not_decrease(self):
        """HWM nunca debe bajar."""
        acc = make_account(high_water_mark="10000")
        acc.update_high_water_mark(Decimal("9000"))
        assert acc.high_water_mark == Decimal("10000")

    def test_update_hwm_same_value_unchanged(self):
        acc = make_account(high_water_mark="10000")
        acc.update_high_water_mark(Decimal("10000"))
        assert acc.high_water_mark == Decimal("10000")

    def test_is_active_default_true(self):
        assert make_account().is_active is True
