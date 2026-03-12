# -*- coding: utf-8 -*-

# ======================================================================
# tests/accounts/test_list_balances_service.py
# ======================================================================

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock

from app.modules.accounts.domain.account_balance_entity import AccountBalance
from app.modules.accounts.domain.account_entity import Account
from app.modules.accounts.services.balances.list_balances_service import ListBalancesService


def _make_account(id: int = 1, user_id: int = 10) -> Account:
    return Account(id=id, user_id=user_id, name="Test", mode="paper", meta={})


def _make_balance(asset: str = "USDT") -> AccountBalance:
    return AccountBalance(
        id=1, account_id=1, asset=asset,
        free=Decimal("1000"), locked=Decimal("0"),
        ts=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


def _make_service(account=None, balances=None):
    account_repo = MagicMock()
    account_repo.get_by_id.return_value = account

    balance_repo = MagicMock()
    balance_repo.list_by_account.return_value = balances or []

    return ListBalancesService(account_repo=account_repo, balance_repo=balance_repo)


class TestListBalancesService:

    def test_owner_can_list_balances(self):
        balances = [_make_balance("USDT"), _make_balance("BTC")]
        svc = _make_service(account=_make_account(user_id=10), balances=balances)

        result = svc.list(account_id=1, requester_user_id=10)

        assert result.success is True
        assert len(result.data) == 2

    def test_admin_can_list_any_account_balances(self):
        svc = _make_service(account=_make_account(user_id=10), balances=[_make_balance()])

        result = svc.list(account_id=1, requester_user_id=99, is_admin=True)

        assert result.success is True

    def test_returns_empty_list_when_no_balances(self):
        svc = _make_service(account=_make_account(user_id=10), balances=[])

        result = svc.list(account_id=1, requester_user_id=10)

        assert result.success is True
        assert result.data == []

    def test_fails_if_account_not_found(self):
        svc = _make_service(account=None)

        result = svc.list(account_id=99, requester_user_id=10)

        assert result.success is False
        assert result.error.code == "ACCOUNT_NOT_FOUND"
        assert result.error.http_status == 404

    def test_fails_if_not_owner_and_not_admin(self):
        svc = _make_service(account=_make_account(user_id=10))

        result = svc.list(account_id=1, requester_user_id=55, is_admin=False)

        assert result.success is False
        assert result.error.code == "ACCOUNT_FORBIDDEN"
        assert result.error.http_status == 403
