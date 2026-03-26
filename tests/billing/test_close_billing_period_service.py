# -*- coding: utf-8 -*-

# ======================================================================
# tests/billing/test_close_billing_period_service.py
#
# Tests unitarios de CloseBillingPeriodService.
#
# ESTRATEGIA:
# - Repos 100% mockeados (MagicMock).
# - Se verifica el flujo de lógica de negocio: HWM, creación de
#   FeeTransaction, actualización del HWM, commit y errores.
#
# NOMENCLATURA:
#   test_<condición>_<resultado_esperado>
# ======================================================================

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, call

import pytest

from app.modules.billing.domain.billing_period_entity import BillingPeriod
from app.modules.billing.domain.managed_account_entity import ManagedAccount
from app.modules.billing.services.billing.close_billing_period_service import (
    CloseBillingPeriodService,
)


# ======================================================================
# Helpers
# ======================================================================

def make_open_period(
    opening_equity: str = "10000",
    fee_pct: str = "0.2000",
    managed_account_id: int = 1,
) -> BillingPeriod:
    return BillingPeriod(
        id=5,
        managed_account_id=managed_account_id,
        opening_equity=Decimal(opening_equity),
        fee_pct=Decimal(fee_pct),
        status=BillingPeriod.STATUS_OPEN,
    )


def make_managed_account(high_water_mark: str = "10000") -> ManagedAccount:
    return ManagedAccount(
        id=1,
        investor_id=2,
        account_id=3,
        name="Test",
        initial_capital=Decimal("10000"),
        high_water_mark=Decimal(high_water_mark),
    )


def make_service(
    period: BillingPeriod | None,
    account: ManagedAccount | None,
) -> tuple[CloseBillingPeriodService, MagicMock, MagicMock, MagicMock, MagicMock]:
    period_repo = MagicMock()
    fee_tx_repo = MagicMock()
    ma_repo = MagicMock()
    session = MagicMock()

    period_repo.find_by_id.return_value = period
    ma_repo.find_by_id.return_value = account

    svc = CloseBillingPeriodService(
        period_repo=period_repo,
        fee_tx_repo=fee_tx_repo,
        managed_account_repo=ma_repo,
        session=session,
    )
    return svc, period_repo, fee_tx_repo, ma_repo, session


# ======================================================================
# TestCloseBillingPeriodService — errores
# ======================================================================

class TestCloseBillingPeriodErrors:

    def test_period_not_found_returns_fail(self):
        svc, *_ = make_service(period=None, account=None)
        result = svc.execute(period_id=99, closing_equity=Decimal("11000"))
        assert result.success is False
        assert result.error.code == "BILLING_PERIOD_NOT_FOUND"

    def test_already_closed_period_returns_fail(self):
        period = make_open_period()
        period.status = BillingPeriod.STATUS_CLOSED
        svc, *_ = make_service(period=period, account=make_managed_account())
        result = svc.execute(period_id=5, closing_equity=Decimal("11000"))
        assert result.success is False
        assert result.error.code == "BILLING_PERIOD_ALREADY_CLOSED"

    def test_managed_account_not_found_returns_fail(self):
        svc, *_ = make_service(period=make_open_period(), account=None)
        result = svc.execute(period_id=5, closing_equity=Decimal("11000"))
        assert result.success is False
        assert result.error.code == "BILLING_MANAGED_ACCOUNT_NOT_FOUND"


# ======================================================================
# TestCloseBillingPeriodService — flujo con ganancia
# ======================================================================

class TestClosePeriodWithGain:

    def setup_method(self):
        self.period = make_open_period(opening_equity="10000", fee_pct="0.2000")
        self.account = make_managed_account(high_water_mark="10000")
        self.svc, self.period_repo, self.fee_tx_repo, self.ma_repo, self.session = \
            make_service(self.period, self.account)

    def test_returns_success(self):
        result = self.svc.execute(period_id=5, closing_equity=Decimal("11000"))
        assert result.success is True

    def test_period_status_is_closed(self):
        result = self.svc.execute(period_id=5, closing_equity=Decimal("11000"))
        assert result.data.status == BillingPeriod.STATUS_CLOSED

    def test_fee_amount_calculated(self):
        """Ganancia 1000, fee 20% → fee_amount = 200."""
        result = self.svc.execute(period_id=5, closing_equity=Decimal("11000"))
        assert result.data.fee_amount == Decimal("200.000000")

    def test_net_pnl_calculated(self):
        result = self.svc.execute(period_id=5, closing_equity=Decimal("11000"))
        assert result.data.net_pnl == Decimal("800.000000")

    def test_fee_transaction_created(self):
        """Debe crearse una FeeTransaction cuando hay fee > 0."""
        self.svc.execute(period_id=5, closing_equity=Decimal("11000"))
        self.fee_tx_repo.save.assert_called_once()

    def test_hwm_updated_when_gain(self):
        """Debe actualizarse el HWM al closing_equity cuando hay ganancia."""
        self.svc.execute(period_id=5, closing_equity=Decimal("11000"))
        self.ma_repo.update_high_water_mark.assert_called_once_with(
            managed_account_id=1,
            new_hwm=Decimal("11000"),
        )

    def test_session_commit_called(self):
        self.svc.execute(period_id=5, closing_equity=Decimal("11000"))
        self.session.commit.assert_called_once()

    def test_period_updated_in_repo(self):
        self.svc.execute(period_id=5, closing_equity=Decimal("11000"))
        self.period_repo.update.assert_called_once()


# ======================================================================
# TestClosePeriodWithLoss — sin ganancia, sin fee
# ======================================================================

class TestClosePeriodWithLoss:

    def setup_method(self):
        self.period = make_open_period(opening_equity="10000", fee_pct="0.2000")
        self.account = make_managed_account(high_water_mark="10000")
        self.svc, self.period_repo, self.fee_tx_repo, self.ma_repo, self.session = \
            make_service(self.period, self.account)

    def test_returns_success(self):
        result = self.svc.execute(period_id=5, closing_equity=Decimal("9000"))
        assert result.success is True

    def test_fee_amount_is_zero_on_loss(self):
        result = self.svc.execute(period_id=5, closing_equity=Decimal("9000"))
        assert result.data.fee_amount == Decimal("0")

    def test_no_fee_transaction_created_on_loss(self):
        self.svc.execute(period_id=5, closing_equity=Decimal("9000"))
        self.fee_tx_repo.save.assert_not_called()

    def test_hwm_not_updated_on_loss(self):
        self.svc.execute(period_id=5, closing_equity=Decimal("9000"))
        self.ma_repo.update_high_water_mark.assert_not_called()

    def test_session_commit_still_called(self):
        """Aunque no haya fee, el período se cierra y hay commit."""
        self.svc.execute(period_id=5, closing_equity=Decimal("9000"))
        self.session.commit.assert_called_once()


# ======================================================================
# TestClosePeriodWithHWMAboveOpening — escenario de recuperación
# ======================================================================

class TestClosePeriodFeePctZero:
    """fee_pct=0: no se genera FeeTransaction pero el HWM sí debe actualizarse."""

    def test_hwm_updates_even_when_fee_pct_is_zero(self):
        period = make_open_period(opening_equity="10000", fee_pct="0.0000")
        account = make_managed_account(high_water_mark="10000")
        svc, _, fee_tx_repo, ma_repo, _ = make_service(period, account)

        result = svc.execute(period_id=5, closing_equity=Decimal("11000"))

        assert result.success is True
        assert result.data.fee_amount == Decimal("0.000000")
        fee_tx_repo.save.assert_not_called()
        ma_repo.update_high_water_mark.assert_called_once_with(
            managed_account_id=1,
            new_hwm=Decimal("11000"),
        )


class TestClosePeriodHWMAboveOpening:

    def test_fee_only_on_new_high(self):
        """
        Período abre en $9000, HWM previo = $11000.
        Closing = $12000. Fee solo sobre $1000 (excedente al HWM), no sobre $3000.
        """
        period = make_open_period(opening_equity="9000", fee_pct="0.2000")
        account = make_managed_account(high_water_mark="11000")
        svc, *_ = make_service(period, account)

        result = svc.execute(period_id=5, closing_equity=Decimal("12000"))

        # baseline = max(9000, 11000) = 11000
        # gross_pnl = 12000 - 11000 = 1000
        # fee = 1000 * 0.20 = 200
        assert result.data.gross_pnl == Decimal("1000")
        assert result.data.fee_amount == Decimal("200.000000")

    def test_no_fee_when_recovery_below_hwm(self):
        """
        Período abre en $9000, HWM = $11000. Closing = $10500.
        No hay nuevos máximos → fee = 0.
        """
        period = make_open_period(opening_equity="9000", fee_pct="0.2000")
        account = make_managed_account(high_water_mark="11000")
        svc, _, fee_tx_repo, ma_repo, _ = make_service(period, account)

        result = svc.execute(period_id=5, closing_equity=Decimal("10500"))

        assert result.data.fee_amount == Decimal("0")
        fee_tx_repo.save.assert_not_called()

    def test_hwm_not_decreased_on_partial_recovery(self):
        """
        Período abre en $9000, HWM = $11000. Closing = $10500.
        gross_pnl = 1500 > 0, pero closing < HWM → el HWM NO debe actualizarse
        (evitar decrecer el HWM de 11000 a 10500).
        """
        period = make_open_period(opening_equity="9000", fee_pct="0.2000")
        account = make_managed_account(high_water_mark="11000")
        svc, _, _, ma_repo, _ = make_service(period, account)

        svc.execute(period_id=5, closing_equity=Decimal("10500"))

        ma_repo.update_high_water_mark.assert_not_called()
