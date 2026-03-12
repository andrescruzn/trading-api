# -*- coding: utf-8 -*-

# ======================================================================
# tests/accounts/test_create_account_service.py
# ======================================================================

from unittest.mock import MagicMock

from app.modules.accounts.domain.account_entity import Account
from app.modules.accounts.services.accounts.create_account_service import CreateAccountService
from app.modules.market.domain.exchange_entity import Exchange


def _make_exchange(id: int = 1) -> Exchange:
    return Exchange(id=id, name="Binance", type="crypto_exchange", is_active=True)


def _make_created_account(**kwargs) -> Account:
    defaults = dict(id=1, user_id=5, name="Mi cuenta", mode="paper", meta={})
    defaults.update(kwargs)
    return Account(**defaults)


def _make_service(exchange=None, created_account=None):
    account_repo = MagicMock()
    account_repo.create.return_value = created_account or _make_created_account()

    exchange_repo = MagicMock()
    exchange_repo.get_by_id.return_value = exchange

    session = MagicMock()
    cipher = MagicMock()
    cipher.encrypt.return_value = "encrypted_token"

    svc = CreateAccountService(
        account_repo=account_repo,
        exchange_repo=exchange_repo,
        session=session,
        cipher=cipher,
    )
    return svc, account_repo, exchange_repo, session, cipher


class TestCreateAccountService:

    # ------------------------------------------------------------------
    # Éxito — paper sin credenciales
    # ------------------------------------------------------------------

    def test_creates_paper_account_without_credentials(self):
        svc, repo, _, session, cipher = _make_service()

        result = svc.create(user_id=5, name="Paper Trading", mode="paper")

        assert result.success is True
        assert result.data.id == 1
        repo.create.assert_called_once()
        session.commit.assert_called_once()
        cipher.encrypt.assert_not_called()

    # ------------------------------------------------------------------
    # Éxito — live con credenciales
    # ------------------------------------------------------------------

    def test_creates_live_account_with_credentials(self):
        created = _make_created_account(
            mode="live",
            credentials_ref="encrypted",
            meta={"enc_creds": "encrypted_token"},
        )
        svc, repo, _, session, cipher = _make_service(
            exchange=_make_exchange(),
            created_account=created,
        )

        result = svc.create(
            user_id=5,
            name="Live Binance",
            mode="live",
            exchange_id=1,
            api_key="my_key",
            api_secret="my_secret",
        )

        assert result.success is True
        cipher.encrypt.assert_called_once_with(api_key="my_key", api_secret="my_secret")
        session.commit.assert_called_once()

    # ------------------------------------------------------------------
    # Éxito — con exchange válido
    # ------------------------------------------------------------------

    def test_creates_account_with_valid_exchange(self):
        svc, repo, exchange_repo, _, _ = _make_service(exchange=_make_exchange(id=2))

        result = svc.create(user_id=5, name="Bybit", mode="paper", exchange_id=2)

        assert result.success is True
        exchange_repo.get_by_id.assert_called_once_with(2)

    # ------------------------------------------------------------------
    # Error — modo inválido
    # ------------------------------------------------------------------

    def test_fails_with_invalid_mode(self):
        svc, repo, _, session, _ = _make_service()

        result = svc.create(user_id=5, name="Test", mode="invalid")

        assert result.success is False
        assert result.error.code == "ACCOUNT_INVALID_MODE"
        assert result.error.http_status == 422
        repo.create.assert_not_called()
        session.commit.assert_not_called()

    # ------------------------------------------------------------------
    # Error — exchange no encontrado
    # ------------------------------------------------------------------

    def test_fails_if_exchange_not_found(self):
        svc, repo, _, session, _ = _make_service(exchange=None)

        result = svc.create(user_id=5, name="Test", mode="paper", exchange_id=99)

        assert result.success is False
        assert result.error.code == "EXCHANGE_NOT_FOUND"
        assert result.error.http_status == 404
        repo.create.assert_not_called()
        session.commit.assert_not_called()

    # ------------------------------------------------------------------
    # Normalización
    # ------------------------------------------------------------------

    def test_normalizes_base_currency_to_uppercase(self):
        svc, repo, _, _, _ = _make_service()
        svc.create(user_id=5, name="Test", mode="paper", base_currency="usdt")

        call_args = repo.create.call_args[0][0]
        assert call_args.base_currency == "USDT"

    def test_strips_whitespace_from_name(self):
        svc, repo, _, _, _ = _make_service()
        svc.create(user_id=5, name="  Mi cuenta  ", mode="paper")

        call_args = repo.create.call_args[0][0]
        assert call_args.name == "Mi cuenta"
