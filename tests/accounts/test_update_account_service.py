# -*- coding: utf-8 -*-

# ======================================================================
# tests/accounts/test_update_account_service.py
# ======================================================================

from unittest.mock import MagicMock

from app.modules.accounts.domain.account_entity import Account
from app.modules.accounts.services.accounts.update_account_service import UpdateAccountService
from app.modules.market.domain.exchange_entity import Exchange


def _make_account(id: int = 1, user_id: int = 10) -> Account:
    return Account(id=id, user_id=user_id, name="Original", mode="paper",
                   status="active", base_currency="USD", meta={})


def _make_exchange(id: int = 2) -> Exchange:
    return Exchange(id=id, name="Bybit", type="crypto_exchange", is_active=True)


def _make_service(account=None, exchange=None):
    account_repo = MagicMock()
    account_repo.get_by_id.return_value = account
    account_repo.update.side_effect = lambda a: a   # retorna la entidad modificada

    exchange_repo = MagicMock()
    exchange_repo.get_by_id.return_value = exchange

    session = MagicMock()
    cipher = MagicMock()
    cipher.encrypt.return_value = "new_encrypted_token"

    svc = UpdateAccountService(
        account_repo=account_repo,
        exchange_repo=exchange_repo,
        session=session,
        cipher=cipher,
    )
    return svc, account_repo, session, cipher


class TestUpdateAccountService:

    def test_owner_can_update_name(self):
        svc, repo, session, _ = _make_service(account=_make_account(user_id=10))

        result = svc.update(account_id=1, requester_user_id=10, name="Nuevo nombre")

        assert result.success is True
        assert result.data.name == "Nuevo nombre"
        session.commit.assert_called_once()

    def test_admin_can_update_any_account(self):
        svc, _, session, _ = _make_service(account=_make_account(user_id=10))

        result = svc.update(account_id=1, requester_user_id=99, is_admin=True, status="suspended")

        assert result.success is True
        assert result.data.status == "suspended"

    def test_re_encrypts_credentials_when_provided(self):
        svc, _, session, cipher = _make_service(account=_make_account(user_id=10))

        result = svc.update(
            account_id=1, requester_user_id=10,
            api_key="new_key", api_secret="new_secret",
        )

        assert result.success is True
        cipher.encrypt.assert_called_once_with(api_key="new_key", api_secret="new_secret")
        assert result.data.meta["enc_creds"] == "new_encrypted_token"

    def test_does_not_re_encrypt_when_no_credentials_given(self):
        svc, _, _, cipher = _make_service(account=_make_account(user_id=10))

        svc.update(account_id=1, requester_user_id=10, name="Solo nombre")

        cipher.encrypt.assert_not_called()

    def test_fails_if_account_not_found(self):
        svc, _, session, _ = _make_service(account=None)

        result = svc.update(account_id=99, requester_user_id=10)

        assert result.success is False
        assert result.error.code == "ACCOUNT_NOT_FOUND"
        assert result.error.http_status == 404
        session.commit.assert_not_called()

    def test_fails_if_not_owner_and_not_admin(self):
        svc, _, session, _ = _make_service(account=_make_account(user_id=10))

        result = svc.update(account_id=1, requester_user_id=99, is_admin=False)

        assert result.success is False
        assert result.error.code == "ACCOUNT_FORBIDDEN"
        assert result.error.http_status == 403
        session.commit.assert_not_called()

    def test_fails_with_invalid_status(self):
        svc, _, session, _ = _make_service(account=_make_account(user_id=10))

        result = svc.update(account_id=1, requester_user_id=10, status="deleted")

        assert result.success is False
        assert result.error.code == "ACCOUNT_INVALID_STATUS"
        assert result.error.http_status == 422
        session.commit.assert_not_called()

    def test_fails_if_new_exchange_not_found(self):
        svc, _, session, _ = _make_service(account=_make_account(user_id=10), exchange=None)

        result = svc.update(account_id=1, requester_user_id=10, exchange_id=99)

        assert result.success is False
        assert result.error.code == "EXCHANGE_NOT_FOUND"
        session.commit.assert_not_called()

    def test_normalizes_base_currency_to_uppercase(self):
        svc, _, _, _ = _make_service(account=_make_account(user_id=10))

        result = svc.update(account_id=1, requester_user_id=10, base_currency="eur")

        assert result.success is True
        assert result.data.base_currency == "EUR"
