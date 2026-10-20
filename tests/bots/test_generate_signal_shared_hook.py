# -*- coding: utf-8 -*-

# ======================================================================
# tests/bots/test_generate_signal_shared_hook.py
#
# Hook `notify_subscribers` de GenerateSignalService (señales compartidas):
# - Se llama solo si el agente comparte y la señal es BUY/SELL aprobada,
#   después de persistir y confirmar la señal.
# - Un fallo del hook no afecta a la señal.
# ======================================================================

from __future__ import annotations

from unittest.mock import MagicMock

from app.common.contracts import ServiceResult
from app.modules.bots.domain.signal_entity import Signal
from app.modules.bots.services.signals.generate_signal_service import GenerateSignalService
from tests.bots.test_generate_signal_service import make_analysis_result, make_bot


# ======================================================================
# Helpers
# ======================================================================

def _make_service(share_signals: bool, analysis=None, notify=None):
    bot = make_bot()
    bot.share_signals = share_signals
    bot_repo = MagicMock()
    bot_repo.get_by_id.return_value = bot

    signal_repo = MagicMock()

    def _create(s: Signal) -> Signal:
        s.id = 10
        return s

    signal_repo.create.side_effect = _create

    analyze = MagicMock()
    analyze.analyze.return_value = ServiceResult.ok(data=analysis or make_analysis_result())

    notify = notify if notify is not None else MagicMock()
    service = GenerateSignalService(
        bot_repo=bot_repo,
        signal_repo=signal_repo,
        analyze_service=analyze,
        account_repo=MagicMock(),
        notify_subscribers=notify,
    )
    return service, notify, signal_repo


# ======================================================================
# Tests
# ======================================================================

class TestNotifySubscribersHook:

    def test_called_for_shared_bot_with_approved_buy(self):
        service, notify, _ = _make_service(share_signals=True)

        result = service.generate(bot_id=1)

        assert result.success is True
        notify.assert_called_once()
        signal, bot = notify.call_args.args
        assert signal.action == "buy"
        assert bot.share_signals is True

    def test_called_for_shared_bot_with_approved_sell(self):
        analysis = make_analysis_result(entry=50000.0, stop_loss=51000.0, take_profit=48000.0)
        service, notify, _ = _make_service(share_signals=True, analysis=analysis)

        service.generate(bot_id=1)

        assert notify.call_args.args[0].action == "sell"

    def test_called_after_commit(self):
        calls: list[str] = []
        service, _, signal_repo = _make_service(
            share_signals=True, notify=lambda s, b: calls.append("notify")
        )
        signal_repo.commit.side_effect = lambda: calls.append("commit")

        service.generate(bot_id=1)

        assert calls == ["commit", "notify"]

    def test_not_called_when_bot_does_not_share(self):
        service, notify, _ = _make_service(share_signals=False)

        service.generate(bot_id=1)

        notify.assert_not_called()

    def test_not_called_for_rejected_signal(self):
        service, notify, _ = _make_service(
            share_signals=True, analysis=make_analysis_result(approved=False)
        )

        result = service.generate(bot_id=1)

        assert result.data.action == "hold"
        notify.assert_not_called()

    def test_not_called_for_approved_hold_without_prices(self):
        analysis = make_analysis_result(entry=None, stop_loss=None, take_profit=None)
        service, notify, _ = _make_service(share_signals=True, analysis=analysis)

        service.generate(bot_id=1)

        notify.assert_not_called()

    def test_hook_failure_does_not_affect_the_signal(self):
        service, notify, signal_repo = _make_service(
            share_signals=True, notify=MagicMock(side_effect=RuntimeError("telegram down"))
        )

        result = service.generate(bot_id=1)

        assert result.success is True
        assert result.data.id == 10
        signal_repo.commit.assert_called_once()
        signal_repo.rollback.assert_not_called()
