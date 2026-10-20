# -*- coding: utf-8 -*-

# ======================================================================
# tests/bots/test_shared_signal_notifier.py
#
# Tests unitarios de SharedSignalNotifier (M9, hook de M7):
# - Envía a los suscriptores con chat vinculado, sin botones.
# - Omite al dueño, a quien no tiene chat, las señales HOLD/rechazadas,
#   los agentes que ya no comparten y la falta de token.
# - Un fallo de envío no corta el reparto ni lanza.
#
# telegram_api se parchea: sin red.
# ======================================================================

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.modules.alerts.services.telegram.shared_signal_notifier import SharedSignalNotifier
from app.modules.bots.domain.bot_entity import Bot
from app.modules.bots.domain.signal_entity import Signal
from app.modules.bots.domain.signal_subscription_entity import SignalSubscription

OWNER_ID = 7
_TELEGRAM_API = "app.modules.alerts.services.telegram.shared_signal_notifier.telegram_api"


# ======================================================================
# Helpers
# ======================================================================

def _make_bot(share_signals: bool = True) -> Bot:
    return Bot(
        id=1,
        name="Agente de Juan",
        strategy_id=10,
        symbol_id=5,
        timeframe_id=3,
        account_id=70,
        feature_set_id=1,
        mode="paper",
        status="running",
        risk_params={"risk_pct": 0.01},
        share_signals=share_signals,
    )


def _make_signal(action: str = "buy", approved: bool = True) -> Signal:
    return Signal(
        id=99,
        bot_id=1,
        ts=datetime(2026, 10, 20, tzinfo=timezone.utc),
        action=action,
        approved=approved,
        reasons={},
        entry_price=Decimal("50000"),
        stop_loss=Decimal("49000"),
        take_profit=Decimal("52000"),
        position_size=Decimal("0.123456"),
        rr_ratio=Decimal("2.0"),
    )


def _make_notifier(
    subscriber_ids: list[int],
    chats: dict[int, int | None],
    token: str = "TOKEN",
) -> SharedSignalNotifier:
    sub_repo = MagicMock()
    sub_repo.list_by_bot.return_value = [
        SignalSubscription(id=i, bot_id=1, user_id=uid) for i, uid in enumerate(subscriber_ids)
    ]
    account_repo = MagicMock()
    account_repo.get_by_id.return_value = SimpleNamespace(id=70, user_id=OWNER_ID)
    user_repo = MagicMock()
    user_repo.get_by_id.side_effect = lambda uid: (
        SimpleNamespace(id=uid, telegram_chat_id=chats[uid]) if uid in chats else None
    )
    symbol_repo = MagicMock()
    symbol_repo.get_by_id.return_value = SimpleNamespace(symbol="BTC/USDT", base_asset="BTC")
    timeframe_repo = MagicMock()
    timeframe_repo.get_by_id.return_value = SimpleNamespace(code="1h")
    strategy_repo = MagicMock()
    strategy_repo.get_by_id.return_value = SimpleNamespace(name="EMA Trend Follower")
    return SharedSignalNotifier(
        subscription_repo=sub_repo,
        account_repo=account_repo,
        user_repo=user_repo,
        symbol_repo=symbol_repo,
        timeframe_repo=timeframe_repo,
        strategy_repo=strategy_repo,
        settings=SimpleNamespace(TELEGRAM_BOT_TOKEN=token),
    )


# ======================================================================
# Tests
# ======================================================================

class TestSharedSignalNotifier:

    def test_sends_to_each_linked_subscriber_without_buttons(self):
        notifier = _make_notifier([3, 4], chats={3: 300, 4: 400})

        with patch(_TELEGRAM_API, return_value={"message_id": 1}) as api:
            sent = notifier.notify(_make_signal(), _make_bot())

        assert sent == 2
        chat_ids = [c.args[2]["chat_id"] for c in api.call_args_list]
        assert chat_ids == [300, 400]
        payload = api.call_args_list[0].args[2]
        assert "reply_markup" not in payload
        assert "BTC/USDT" in payload["text"]
        assert "R/R 2,0:1" in payload["text"]

    def test_message_hides_agent_name_and_position_size(self):
        notifier = _make_notifier([3], chats={3: 300})

        with patch(_TELEGRAM_API, return_value={"message_id": 1}) as api:
            notifier.notify(_make_signal(), _make_bot())

        text = api.call_args.args[2]["text"]
        assert "Juan" not in text
        assert "0,123456" not in text

    def test_skips_subscribers_without_chat(self):
        notifier = _make_notifier([3, 4, 5], chats={3: None, 4: 400})

        with patch(_TELEGRAM_API, return_value={"message_id": 1}) as api:
            sent = notifier.notify(_make_signal(), _make_bot())

        assert sent == 1
        assert api.call_count == 1
        assert api.call_args.args[2]["chat_id"] == 400

    def test_never_notifies_the_owner(self):
        notifier = _make_notifier([OWNER_ID, 3], chats={OWNER_ID: 700, 3: 300})

        with patch(_TELEGRAM_API, return_value={"message_id": 1}) as api:
            sent = notifier.notify(_make_signal(), _make_bot())

        assert sent == 1
        assert api.call_args.args[2]["chat_id"] == 300

    def test_hold_signal_is_not_sent(self):
        notifier = _make_notifier([3], chats={3: 300})

        with patch(_TELEGRAM_API) as api:
            sent = notifier.notify(_make_signal(action="hold"), _make_bot())

        assert sent == 0
        api.assert_not_called()

    def test_rejected_signal_is_not_sent(self):
        notifier = _make_notifier([3], chats={3: 300})

        with patch(_TELEGRAM_API) as api:
            sent = notifier.notify(_make_signal(approved=False), _make_bot())

        assert sent == 0
        api.assert_not_called()

    def test_bot_that_stopped_sharing_is_not_sent(self):
        notifier = _make_notifier([3], chats={3: 300})

        with patch(_TELEGRAM_API) as api:
            sent = notifier.notify(_make_signal(), _make_bot(share_signals=False))

        assert sent == 0
        api.assert_not_called()

    def test_without_token_nothing_is_sent(self):
        notifier = _make_notifier([3], chats={3: 300}, token="")

        with patch(_TELEGRAM_API) as api:
            sent = notifier.notify(_make_signal(), _make_bot())

        assert sent == 0
        api.assert_not_called()

    def test_send_failure_is_swallowed_and_others_still_receive(self):
        notifier = _make_notifier([3, 4], chats={3: 300, 4: 400})

        with patch(_TELEGRAM_API, side_effect=[RuntimeError("boom"), {"message_id": 2}]) as api:
            sent = notifier.notify(_make_signal(), _make_bot())

        assert sent == 1
        assert api.call_count == 2

    def test_unexpected_error_never_raises(self):
        notifier = _make_notifier([3], chats={3: 300})
        notifier._subscription_repo.list_by_bot.side_effect = RuntimeError("db down")

        sent = notifier.notify(_make_signal(), _make_bot())

        assert sent == 0
