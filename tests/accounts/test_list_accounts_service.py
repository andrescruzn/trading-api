# -*- coding: utf-8 -*-

# ======================================================================
# tests/accounts/test_list_accounts_service.py
# ======================================================================

from datetime import datetime, timezone
from unittest.mock import MagicMock

from app.modules.accounts.domain.account_entity import Account
from app.modules.accounts.services.accounts.list_accounts_service import ListAccountsService


def _make_account(id: int = 1, user_id: int = 10, name: str = "Main") -> Account:
    return Account(
        id=id,
        user_id=user_id,
        name=name,
        mode="paper",
        meta={},
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


def _make_service(accounts_by_user=None, all_accounts=None):
    repo = MagicMock()
    repo.list_by_user_id.return_value = accounts_by_user or []
    repo.list_all.return_value = all_accounts or []
    return ListAccountsService(repo=repo), repo


class TestListAccountsService:

    def test_user_sees_only_own_accounts(self):
        own = [_make_account(id=1, user_id=10), _make_account(id=2, user_id=10)]
        svc, repo = _make_service(accounts_by_user=own)

        result = svc.list(user_id=10, is_admin=False)

        assert result.success is True
        assert len(result.data) == 2
        repo.list_by_user_id.assert_called_once_with(10)
        repo.list_all.assert_not_called()

    def test_admin_sees_all_accounts(self):
        all_accs = [
            _make_account(id=1, user_id=10),
            _make_account(id=2, user_id=20),
            _make_account(id=3, user_id=30),
        ]
        svc, repo = _make_service(all_accounts=all_accs)

        result = svc.list(user_id=99, is_admin=True)

        assert result.success is True
        assert len(result.data) == 3
        repo.list_all.assert_called_once()
        repo.list_by_user_id.assert_not_called()

    def test_returns_empty_list_when_no_accounts(self):
        svc, _ = _make_service(accounts_by_user=[])

        result = svc.list(user_id=10, is_admin=False)

        assert result.success is True
        assert result.data == []
