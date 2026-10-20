# -*- coding: utf-8 -*-

# ======================================================================
# tests/billing/test_capital_movements_service.py
#
# Aportes y retiros: ajustan la marca de agua y la apertura del período
# abierto para no cobrar comisión sobre dinero que no es ganancia.
# ======================================================================

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.modules.billing.domain.capital_movement_entity import CapitalMovement
from app.modules.billing.services.managed_accounts import (
    ListCapitalMovementsService,
    RecordCapitalMovementService,
)

D = Decimal


def _account(hwm="10000", active=True, investor_id=5):
    return SimpleNamespace(id=1, high_water_mark=D(hwm), is_active=active, investor_id=investor_id)


def _record_service(account, period=None):
    movement_repo = MagicMock()
    movement_repo.save.side_effect = lambda m: m
    managed_repo = MagicMock()
    managed_repo.find_by_id.return_value = account
    period_repo = MagicMock()
    period_repo.find_open_by_managed_account.return_value = period
    svc = RecordCapitalMovementService(
        movement_repo=movement_repo,
        managed_account_repo=managed_repo,
        period_repo=period_repo,
    )
    return svc, movement_repo, managed_repo, period_repo


class TestRecordCapitalMovementService:

    def test_deposit_raises_hwm_and_open_period_opening(self):
        # Aporte de 2.000 con HWM 10.000 y período abierto en 9.500
        period = SimpleNamespace(opening_equity=D("9500"))
        svc, movement_repo, managed_repo, period_repo = _record_service(_account(), period)

        result = svc.execute(managed_account_id=1, kind="deposit", amount=D("2000"))

        assert result.success is True
        managed_repo.update_high_water_mark.assert_called_once_with(1, D("12000"))
        assert period.opening_equity == D("11500")
        period_repo.update.assert_called_once_with(period)
        movement_repo.commit.assert_called_once()

    def test_withdrawal_lowers_hwm_without_going_negative(self):
        svc, _, managed_repo, _ = _record_service(_account(hwm="500"))

        svc.execute(managed_account_id=1, kind="withdrawal", amount=D("800"))

        managed_repo.update_high_water_mark.assert_called_once_with(1, D("0"))

    def test_without_open_period_only_hwm_changes(self):
        svc, _, _, period_repo = _record_service(_account(), period=None)

        svc.execute(managed_account_id=1, kind="deposit", amount=D("100"))

        period_repo.update.assert_not_called()

    def test_invalid_amount_and_kind(self):
        svc, movement_repo, _, _ = _record_service(_account())

        assert svc.execute(1, kind="deposit", amount=D("0")).error.code == "CAPITAL_INVALID_AMOUNT"
        assert svc.execute(1, kind="bonus", amount=D("5")).error.code == "CAPITAL_INVALID_KIND"
        movement_repo.save.assert_not_called()

    def test_inactive_or_missing_account(self):
        svc, movement_repo, managed_repo, _ = _record_service(_account(active=False))

        assert svc.execute(1, "deposit", D("5")).error.code == "BILLING_MANAGED_ACCOUNT_INACTIVE"
        managed_repo.find_by_id.return_value = None
        assert svc.execute(1, "deposit", D("5")).error.code == "BILLING_MANAGED_ACCOUNT_NOT_FOUND"
        movement_repo.commit.assert_not_called()

    def test_failure_rolls_back(self):
        svc, movement_repo, managed_repo, _ = _record_service(_account())
        managed_repo.update_high_water_mark.side_effect = RuntimeError("db")

        try:
            svc.execute(1, "deposit", D("5"))
        except RuntimeError:
            pass

        movement_repo.rollback.assert_called_once()
        movement_repo.commit.assert_not_called()


class TestListCapitalMovementsService:

    def _make(self, account, movements):
        movement_repo = MagicMock()
        movement_repo.list_by_managed_account.return_value = movements
        managed_repo = MagicMock()
        managed_repo.find_by_id.return_value = account
        return ListCapitalMovementsService(movement_repo=movement_repo, managed_account_repo=managed_repo)

    @staticmethod
    def _movement(kind, amount):
        return CapitalMovement(id=0, managed_account_id=1, kind=kind, amount=D(amount), ts=None)

    def test_totals(self):
        svc = self._make(
            _account(),
            [self._movement("deposit", "1000"), self._movement("withdrawal", "300"), self._movement("deposit", "50")],
        )

        summary = svc.execute(managed_account_id=1).data

        assert (summary.deposits, summary.withdrawals, summary.net) == (D("1050"), D("300"), D("750"))

    def test_investor_only_sees_own_account(self):
        svc = self._make(_account(investor_id=5), [])

        result = svc.execute(managed_account_id=1, investor_id=6)

        assert result.error.code == "BILLING_MANAGED_ACCOUNT_FORBIDDEN"
        assert result.error.http_status == 403
