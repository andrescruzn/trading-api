# -*- coding: utf-8 -*-

# ======================================================================
# tests/accounts/test_record_balance_service.py
# ======================================================================

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock

from app.modules.accounts.domain.account_balance_entity import AccountBalance
from app.modules.accounts.domain.account_entity import Account
from app.modules.accounts.services.balances.record_balance_service import RecordBalanceService


def _make_account(id: int = 1, user_id: int = 10) -> Account:
    return Account(id=id, user_id=user_id, name="Test", mode="paper", meta={})


def _make_recorded_balance(asset: str = "USDT", free: str = "500", locked: str = "0") -> AccountBalance:
    return AccountBalance(
        id=1, account_id=1, asset=asset,
        free=Decimal(free), locked=Decimal(locked),
        ts=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


def _make_service(account=None, recorded=None):
    account_repo = MagicMock()
    account_repo.get_by_id.return_value = account

    balance_repo = MagicMock()
    balance_repo.record.return_value = recorded or _make_recorded_balance()

    session = MagicMock()

    svc = RecordBalanceService(
        account_repo=account_repo,
        balance_repo=balance_repo,
        session=session,
    )
    return svc, balance_repo, session


class TestRecordBalanceService:

    def test_records_balance_successfully(self):
        svc, repo, session = _make_service(account=_make_account(user_id=10))

        result = svc.record(
            account_id=1, requester_user_id=10,
            asset="USDT", free=Decimal("500"), locked=Decimal("0"),
        )

        assert result.success is True
        assert result.data.asset == "USDT"
        repo.record.assert_called_once()
        session.commit.assert_called_once()

    def test_records_balance_with_locked_amount(self):
        recorded = _make_recorded_balance(free="300", locked="200")
        svc, _, session = _make_service(account=_make_account(user_id=10), recorded=recorded)

        result = svc.record(
            account_id=1, requester_user_id=10,
            asset="BTC", free=Decimal("300"), locked=Decimal("200"),
        )

        assert result.success is True
        assert result.data.total == Decimal("500")

    def test_admin_can_record_balance_on_any_account(self):
        svc, _, session = _make_service(account=_make_account(user_id=10))

        result = svc.record(
            account_id=1, requester_user_id=99, is_admin=True,
            asset="ETH", free=Decimal("10"), locked=Decimal("0"),
        )

        assert result.success is True
        session.commit.assert_called_once()

    def test_fails_if_account_not_found(self):
        svc, repo, session = _make_service(account=None)

        result = svc.record(
            account_id=99, requester_user_id=10,
            asset="USDT", free=Decimal("100"), locked=Decimal("0"),
        )

        assert result.success is False
        assert result.error.code == "ACCOUNT_NOT_FOUND"
        assert result.error.http_status == 404
        repo.record.assert_not_called()
        session.commit.assert_not_called()

    def test_fails_if_not_owner_and_not_admin(self):
        svc, repo, session = _make_service(account=_make_account(user_id=10))

        result = svc.record(
            account_id=1, requester_user_id=55, is_admin=False,
            asset="USDT", free=Decimal("100"), locked=Decimal("0"),
        )

        assert result.success is False
        assert result.error.code == "ACCOUNT_FORBIDDEN"
        repo.record.assert_not_called()
        session.commit.assert_not_called()

    def test_fails_if_free_is_negative(self):
        svc, repo, session = _make_service(account=_make_account(user_id=10))

        result = svc.record(
            account_id=1, requester_user_id=10,
            asset="USDT", free=Decimal("-1"), locked=Decimal("0"),
        )

        assert result.success is False
        assert result.error.code == "BALANCE_NEGATIVE_AMOUNT"
        assert result.error.http_status == 422
        repo.record.assert_not_called()

    def test_fails_if_locked_is_negative(self):
        svc, repo, session = _make_service(account=_make_account(user_id=10))

        result = svc.record(
            account_id=1, requester_user_id=10,
            asset="USDT", free=Decimal("100"), locked=Decimal("-5"),
        )

        assert result.success is False
        assert result.error.code == "BALANCE_NEGATIVE_AMOUNT"
        repo.record.assert_not_called()

    def test_zero_balance_is_valid(self):
        svc, repo, _ = _make_service(account=_make_account(user_id=10))

        result = svc.record(
            account_id=1, requester_user_id=10,
            asset="BTC", free=Decimal("0"), locked=Decimal("0"),
        )

        assert result.success is True
        repo.record.assert_called_once()
