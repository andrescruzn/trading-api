# -*- coding: utf-8 -*-

# ======================================================================
# tests/accounts/test_get_account_service.py
# ======================================================================

from unittest.mock import MagicMock

from app.modules.accounts.domain.account_entity import Account
from app.modules.accounts.services.accounts.get_account_service import GetAccountService


def _make_account(id: int = 1, user_id: int = 10) -> Account:
    return Account(id=id, user_id=user_id, name="Test", mode="paper", meta={})


def _make_service(account=None):
    repo = MagicMock()
    repo.get_by_id.return_value = account
    return GetAccountService(repo=repo)


class TestGetAccountService:

    def test_owner_can_get_own_account(self):
        account = _make_account(id=1, user_id=10)
        svc = _make_service(account)

        result = svc.get(account_id=1, requester_user_id=10)

        assert result.success is True
        assert result.data.id == 1

    def test_admin_can_get_any_account(self):
        account = _make_account(id=1, user_id=10)
        svc = _make_service(account)

        result = svc.get(account_id=1, requester_user_id=99, is_admin=True)

        assert result.success is True
        assert result.data.user_id == 10

    def test_fails_if_account_not_found(self):
        svc = _make_service(account=None)

        result = svc.get(account_id=99, requester_user_id=10)

        assert result.success is False
        assert result.error.code == "ACCOUNT_NOT_FOUND"
        assert result.error.http_status == 404

    def test_fails_if_not_owner_and_not_admin(self):
        account = _make_account(id=1, user_id=10)
        svc = _make_service(account)

        result = svc.get(account_id=1, requester_user_id=99, is_admin=False)

        assert result.success is False
        assert result.error.code == "ACCOUNT_FORBIDDEN"
        assert result.error.http_status == 403
