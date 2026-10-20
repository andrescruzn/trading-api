# -*- coding: utf-8 -*-

# ======================================================================
# tests/bots/test_signal_subscription_services.py
#
# Tests unitarios de las señales compartidas (suscripciones):
# - ListSharedBotsService: vista pública, is_mine, is_subscribed, conteo.
# - SubscribeToBotService: agente privado/inexistente, propio, Telegram,
#   idempotencia y commit.
# - UnsubscribeFromBotService: borra aunque ya no se comparta, idempotente,
#   no revela agentes privados.
#
# Repositorios MagicMock: sin BD ni red.
# ======================================================================

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from app.modules.bots.domain.bot_entity import Bot
from app.modules.bots.services.subscriptions import (
    ListSharedBotsService,
    SubscribeToBotService,
    UnsubscribeFromBotService,
)
from tests.conftest import make_user

OWNER_ID = 7
OWNER_ACCOUNT_ID = 70
USER_ID = 3
USER_ACCOUNT_ID = 30


# ======================================================================
# Helpers
# ======================================================================

def _make_bot(
    id: int = 1,
    share_signals: bool = True,
    account_id: int = OWNER_ACCOUNT_ID,
) -> Bot:
    return Bot(
        id=id,
        name="Agente de Juan",
        strategy_id=10,
        symbol_id=5,
        timeframe_id=3,
        account_id=account_id,
        feature_set_id=1,
        mode="paper",
        status="running",
        risk_params={"risk_pct": 0.01},
        share_signals=share_signals,
    )


def _account_repo() -> MagicMock:
    accounts = {
        OWNER_ACCOUNT_ID: SimpleNamespace(id=OWNER_ACCOUNT_ID, user_id=OWNER_ID),
        USER_ACCOUNT_ID: SimpleNamespace(id=USER_ACCOUNT_ID, user_id=USER_ID),
    }
    repo = MagicMock()
    repo.get_by_id.side_effect = accounts.get
    repo.list_by_user_id.side_effect = lambda uid: [a for a in accounts.values() if a.user_id == uid]
    return repo


def _user(chat_id: int | None = 555) -> object:
    user = make_user(id=USER_ID)
    user.telegram_chat_id = chat_id
    return user


def _subscribe_service(bot: Bot | None, exists: bool = False, chat_id: int | None = 555):
    bot_repo = MagicMock()
    bot_repo.get_by_id.return_value = bot
    sub_repo = MagicMock()
    sub_repo.exists.return_value = exists
    sub_repo.count_by_bot_ids.return_value = {1: 4}
    user_repo = MagicMock()
    user_repo.get_by_id.return_value = _user(chat_id)
    service = SubscribeToBotService(
        bot_repo=bot_repo,
        subscription_repo=sub_repo,
        account_repo=_account_repo(),
        user_repo=user_repo,
    )
    return service, sub_repo


def _unsubscribe_service(bot: Bot | None, exists: bool):
    bot_repo = MagicMock()
    bot_repo.get_by_id.return_value = bot
    sub_repo = MagicMock()
    sub_repo.exists.return_value = exists
    sub_repo.count_by_bot_ids.return_value = {}
    return UnsubscribeFromBotService(bot_repo=bot_repo, subscription_repo=sub_repo), sub_repo


# ======================================================================
# ListSharedBotsService
# ======================================================================

class TestListSharedBotsService:

    def _make(self, bots: list[Bot], followed: list[int], counts: dict[int, int]):
        bot_repo = MagicMock()
        bot_repo.list_shared.return_value = bots
        sub_repo = MagicMock()
        sub_repo.list_bot_ids_by_user.return_value = followed
        sub_repo.count_by_bot_ids.return_value = counts
        strategy_repo = MagicMock()
        strategy_repo.get_by_id.return_value = SimpleNamespace(name="EMA Trend Follower")
        symbol_repo = MagicMock()
        symbol_repo.get_by_id.return_value = SimpleNamespace(symbol="BTC/USDT")
        timeframe_repo = MagicMock()
        timeframe_repo.get_by_id.return_value = SimpleNamespace(code="1h")
        service = ListSharedBotsService(
            bot_repo=bot_repo,
            subscription_repo=sub_repo,
            account_repo=_account_repo(),
            strategy_repo=strategy_repo,
            symbol_repo=symbol_repo,
            timeframe_repo=timeframe_repo,
        )
        return service, strategy_repo

    def test_returns_public_view_with_flags_and_counts(self):
        bots = [_make_bot(id=1), _make_bot(id=2, account_id=USER_ACCOUNT_ID)]
        service, _ = self._make(bots, followed=[1], counts={1: 4})

        result = service.list(user_id=USER_ID)

        assert result.success is True
        first, second = result.data
        assert first.bot_id == 1
        assert first.strategy_name == "EMA Trend Follower"
        assert first.symbol == "BTC/USDT"
        assert first.timeframe == "1h"
        assert first.subscribers_count == 4
        assert first.is_subscribed is True
        assert first.is_mine is False
        assert second.is_mine is True
        assert second.is_subscribed is False
        assert second.subscribers_count == 0

    def test_does_not_expose_agent_name_or_account(self):
        service, _ = self._make([_make_bot()], followed=[], counts={})

        item = service.list(user_id=USER_ID).data[0]

        assert not hasattr(item, "name")
        assert not hasattr(item, "account_id")

    def test_looks_up_each_catalog_once_per_distinct_id(self):
        service, strategy_repo = self._make(
            [_make_bot(id=1), _make_bot(id=2)], followed=[], counts={}
        )

        service.list(user_id=USER_ID)

        strategy_repo.get_by_id.assert_called_once_with(10)

    def test_empty_when_no_shared_bots(self):
        service, _ = self._make([], followed=[], counts={})

        result = service.list(user_id=USER_ID)

        assert result.success is True
        assert result.data == []


# ======================================================================
# SubscribeToBotService
# ======================================================================

class TestSubscribeToBotService:

    def test_missing_bot_returns_not_found(self):
        service, sub_repo = _subscribe_service(bot=None)

        result = service.subscribe(bot_id=1, user_id=USER_ID)

        assert result.success is False
        assert result.error.code == "BOT_NOT_FOUND"
        assert result.error.http_status == 404
        sub_repo.create.assert_not_called()

    def test_private_bot_returns_not_found(self):
        service, sub_repo = _subscribe_service(bot=_make_bot(share_signals=False))

        result = service.subscribe(bot_id=1, user_id=USER_ID)

        assert result.error.code == "BOT_NOT_FOUND"
        assert result.error.http_status == 404
        sub_repo.commit.assert_not_called()

    def test_own_bot_returns_422(self):
        service, sub_repo = _subscribe_service(bot=_make_bot())

        result = service.subscribe(bot_id=1, user_id=OWNER_ID)

        assert result.error.code == "SUBSCRIPTION_OWN_BOT"
        assert result.error.http_status == 422
        sub_repo.create.assert_not_called()

    def test_without_telegram_returns_422(self):
        service, sub_repo = _subscribe_service(bot=_make_bot(), chat_id=None)

        result = service.subscribe(bot_id=1, user_id=USER_ID)

        assert result.error.code == "SUBSCRIPTION_TELEGRAM_REQUIRED"
        assert result.error.http_status == 422
        sub_repo.create.assert_not_called()
        sub_repo.commit.assert_not_called()

    def test_creates_subscription_and_commits(self):
        service, sub_repo = _subscribe_service(bot=_make_bot())

        result = service.subscribe(bot_id=1, user_id=USER_ID)

        assert result.success is True
        assert result.data.is_subscribed is True
        assert result.data.subscribers_count == 4
        created = sub_repo.create.call_args.args[0]
        assert (created.bot_id, created.user_id) == (1, USER_ID)
        sub_repo.commit.assert_called_once()

    def test_already_subscribed_is_ok_without_new_row(self):
        service, sub_repo = _subscribe_service(bot=_make_bot(), exists=True)

        result = service.subscribe(bot_id=1, user_id=USER_ID)

        assert result.success is True
        assert result.data.is_subscribed is True
        sub_repo.create.assert_not_called()
        sub_repo.commit.assert_not_called()


# ======================================================================
# UnsubscribeFromBotService
# ======================================================================

class TestUnsubscribeFromBotService:

    def test_deletes_existing_subscription_and_commits(self):
        service, sub_repo = _unsubscribe_service(bot=_make_bot(), exists=True)

        result = service.unsubscribe(bot_id=1, user_id=USER_ID)

        assert result.success is True
        assert result.data.is_subscribed is False
        sub_repo.delete.assert_called_once_with(1, USER_ID)
        sub_repo.commit.assert_called_once()

    def test_deletes_even_if_sharing_was_turned_off(self):
        service, sub_repo = _unsubscribe_service(bot=_make_bot(share_signals=False), exists=True)

        result = service.unsubscribe(bot_id=1, user_id=USER_ID)

        assert result.success is True
        sub_repo.delete.assert_called_once()

    def test_without_subscription_on_shared_bot_is_ok(self):
        service, sub_repo = _unsubscribe_service(bot=_make_bot(), exists=False)

        result = service.unsubscribe(bot_id=1, user_id=USER_ID)

        assert result.success is True
        sub_repo.delete.assert_not_called()
        sub_repo.commit.assert_not_called()

    def test_without_subscription_on_private_bot_returns_not_found(self):
        service, _ = _unsubscribe_service(bot=_make_bot(share_signals=False), exists=False)

        result = service.unsubscribe(bot_id=1, user_id=USER_ID)

        assert result.error.code == "BOT_NOT_FOUND"
        assert result.error.http_status == 404
