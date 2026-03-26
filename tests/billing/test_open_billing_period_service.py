# -*- coding: utf-8 -*-

# ======================================================================
# tests/billing/test_open_billing_period_service.py
#
# Tests unitarios de OpenBillingPeriodService.
#
# ESTRATEGIA:
# - Repos 100% mockeados (MagicMock).
# - Verifica: validaciones de cuenta, unicidad de período abierto,
#   snapshot de fee_pct y commit.
# ======================================================================

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.modules.billing.domain.billing_period_entity import BillingPeriod
from app.modules.billing.domain.investor_entity import Investor
from app.modules.billing.domain.managed_account_entity import ManagedAccount
from app.modules.billing.services.billing.open_billing_period_service import (
    OpenBillingPeriodService,
)


# ======================================================================
# Helpers
# ======================================================================

def make_active_account(investor_id: int = 2) -> ManagedAccount:
    return ManagedAccount(
        id=1,
        investor_id=investor_id,
        account_id=3,
        name="Test",
        initial_capital=Decimal("10000"),
        high_water_mark=Decimal("10000"),
        is_active=True,
    )


def make_investor(fee_pct: str = "0.2000") -> Investor:
    return Investor(id=2, user_id=10, fee_pct=Decimal(fee_pct))


def make_saved_period(opening_equity: Decimal, fee_pct: Decimal) -> BillingPeriod:
    return BillingPeriod(
        id=7,
        managed_account_id=1,
        opening_equity=opening_equity,
        fee_pct=fee_pct,
        status=BillingPeriod.STATUS_OPEN,
    )


def make_service(
    account: ManagedAccount | None,
    existing_open: BillingPeriod | None,
    investor: Investor | None,
) -> tuple[OpenBillingPeriodService, MagicMock, MagicMock, MagicMock, MagicMock]:
    period_repo = MagicMock()
    ma_repo = MagicMock()
    inv_repo = MagicMock()
    session = MagicMock()

    ma_repo.find_by_id.return_value = account
    period_repo.find_open_by_managed_account.return_value = existing_open
    inv_repo.find_by_id.return_value = investor

    # save devuelve un período ya guardado (con id asignado)
    if account:
        period_repo.save.return_value = make_saved_period(
            opening_equity=Decimal("10000"),
            fee_pct=investor.fee_pct if investor else Decimal("0"),
        )

    svc = OpenBillingPeriodService(
        period_repo=period_repo,
        managed_account_repo=ma_repo,
        investor_repo=inv_repo,
        session=session,
    )
    return svc, period_repo, ma_repo, inv_repo, session


# ======================================================================
# TestOpenBillingPeriodErrors
# ======================================================================

class TestOpenBillingPeriodErrors:

    def test_account_not_found_returns_fail(self):
        svc, *_ = make_service(account=None, existing_open=None, investor=None)
        result = svc.execute(managed_account_id=99, opening_equity=Decimal("10000"))
        assert result.success is False
        assert result.error.code == "BILLING_MANAGED_ACCOUNT_NOT_FOUND"

    def test_inactive_account_returns_fail(self):
        acc = make_active_account()
        acc.is_active = False
        svc, *_ = make_service(account=acc, existing_open=None, investor=make_investor())
        result = svc.execute(managed_account_id=1, opening_equity=Decimal("10000"))
        assert result.success is False
        assert result.error.code == "BILLING_MANAGED_ACCOUNT_INACTIVE"

    def test_already_open_period_returns_fail(self):
        existing = BillingPeriod(
            id=3, managed_account_id=1,
            opening_equity=Decimal("10000"), fee_pct=Decimal("0.2"),
            status=BillingPeriod.STATUS_OPEN,
        )
        svc, *_ = make_service(
            account=make_active_account(),
            existing_open=existing,
            investor=make_investor(),
        )
        result = svc.execute(managed_account_id=1, opening_equity=Decimal("10000"))
        assert result.success is False
        assert result.error.code == "BILLING_PERIOD_ALREADY_OPEN"


# ======================================================================
# TestOpenBillingPeriodSuccess
# ======================================================================

class TestOpenBillingPeriodSuccess:

    def setup_method(self):
        self.svc, self.period_repo, self.ma_repo, self.inv_repo, self.session = \
            make_service(
                account=make_active_account(investor_id=2),
                existing_open=None,
                investor=make_investor(fee_pct="0.2000"),
            )

    def test_returns_success(self):
        result = self.svc.execute(managed_account_id=1, opening_equity=Decimal("10000"))
        assert result.success is True

    def test_period_saved_in_repo(self):
        self.svc.execute(managed_account_id=1, opening_equity=Decimal("10000"))
        self.period_repo.save.assert_called_once()

    def test_session_commit_called(self):
        self.svc.execute(managed_account_id=1, opening_equity=Decimal("10000"))
        self.session.commit.assert_called_once()

    def test_fee_pct_snapshot_from_investor(self):
        """El fee_pct del período debe ser el del inversor en el momento de apertura."""
        result = self.svc.execute(managed_account_id=1, opening_equity=Decimal("10000"))
        assert result.data.fee_pct == Decimal("0.2000")

    def test_investor_not_found_fee_pct_defaults_to_zero(self):
        svc, period_repo, *_ = make_service(
            account=make_active_account(),
            existing_open=None,
            investor=None,
        )
        # Ajustar save para devolver un período con fee_pct=0
        period_repo.save.return_value = make_saved_period(
            opening_equity=Decimal("10000"), fee_pct=Decimal("0")
        )
        result = svc.execute(managed_account_id=1, opening_equity=Decimal("10000"))
        assert result.success is True
        # El período fue creado con fee_pct=0
        saved_period = period_repo.save.call_args[0][0]
        assert saved_period.fee_pct == Decimal("0")
