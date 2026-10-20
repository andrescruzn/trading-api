# -*- coding: utf-8 -*-

# ======================================================================
# tests/scheduler/test_execution_cycle.py
#
# Ciclo de ejecución del scheduler (execution_cycle.py), todos los pasos
# salvo el de alertas (ya cubierto en tests/alerts/test_execution_cycle_alerts.py):
#   1. señales automáticas (qué agentes, qué vela, tope diario, auto/approval)
#   2. caducar pendientes · 3. reconciliar · 4. proteger SL/TP · 6. Telegram
# y el orden completo de los pasos. Sin BD: SessionLocal, repositorios y
# factories van mockeados; nunca se llama a la IA ni al exchange.
# ======================================================================

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, call, patch

import pytest
from sqlalchemy.exc import IntegrityError

from app.common.config import settings
from app.common.contracts import ServiceResult
from app.modules.bots.domain.bot_entity import Bot
from app.modules.scheduler import execution_cycle

NOW = datetime(2026, 10, 20, 12, 7, tzinfo=timezone.utc)
HOUR = 3600
BOT_FACTORY = "app.modules.bots.providers.BotServiceFactory"
ORDER_FACTORY = "app.modules.orders.providers.OrderServiceFactory"


def _bot(id_=1, execution_mode="auto", feature_set_id=10, account_id=100, timeframe_id=1, mode="paper") -> Bot:
    return Bot(
        id=id_, name=f"bot {id_}", strategy_id=1, symbol_id=7, timeframe_id=timeframe_id,
        account_id=account_id, feature_set_id=feature_set_id, mode=mode, status="running",
        risk_params={"risk_pct": 0.01}, execution_mode=execution_mode,
    )


class _Sessions:
    """SessionLocal falso que guarda cada sesión creada."""

    def __init__(self):
        self.created: list[MagicMock] = []

    def __call__(self):
        session = MagicMock()
        self.created.append(session)
        return session


@pytest.fixture
def sessions(monkeypatch) -> _Sessions:
    fake = _Sessions()
    monkeypatch.setattr(execution_cycle, "SessionLocal", fake)
    monkeypatch.setattr(execution_cycle, "utc_now", lambda: NOW)
    return fake


# ======================================================================
# Orden de los pasos
# ======================================================================

class TestRunExecutionCycleOrder:

    def test_runs_all_steps_in_documented_order(self):
        expected = [
            "_generate_automatic_signals",
            "_expire_pending_signals",
            "_reconcile_orders",
            "_protect_positions",
            "_evaluate_alert_rules",
            "_poll_telegram",
        ]
        calls: list[str] = []
        mocks = {n: MagicMock(side_effect=lambda n=n: calls.append(n), __name__=n) for n in expected}

        with patch.multiple(execution_cycle, **mocks):
            execution_cycle.run_execution_cycle()

        assert calls == expected

    def test_signals_failure_does_not_stop_reconcile_or_protection(self):
        names = ["_expire_pending_signals", "_reconcile_orders", "_protect_positions",
                 "_evaluate_alert_rules", "_poll_telegram"]
        mocks = {n: MagicMock(__name__=n) for n in names}
        failing = MagicMock(side_effect=RuntimeError("IA caída"), __name__="_generate_automatic_signals")

        with patch.multiple(execution_cycle, _generate_automatic_signals=failing, **mocks):
            execution_cycle.run_execution_cycle()

        assert all(m.called for m in mocks.values())


# ======================================================================
# 1. Señales automáticas: selección de agentes y tope diario
# ======================================================================

class TestGenerateAutomaticSignals:

    def _patch(self, monkeypatch, bots, candle_ts=NOW - timedelta(hours=1, minutes=7), owners=None,
               counted=0, generate=None):
        bot_repo = MagicMock()
        bot_repo.list_by_statuses.return_value = bots
        monkeypatch.setattr(execution_cycle, "SqlAlchemyBotRepository", MagicMock(return_value=bot_repo))
        owners = owners or {}
        account_repo = MagicMock()
        account_repo.get_by_id.side_effect = lambda account_id: SimpleNamespace(user_id=owners.get(account_id, 1))
        monkeypatch.setattr(execution_cycle, "SqlAlchemyAccountRepository", MagicMock(return_value=account_repo))
        closed = MagicMock(return_value=candle_ts)
        count = MagicMock(return_value=counted)
        gen = generate or MagicMock()
        monkeypatch.setattr(execution_cycle, "_closed_candle_to_analyze", closed)
        monkeypatch.setattr(execution_cycle, "_count_owner_signals_since", count)
        monkeypatch.setattr(execution_cycle, "_generate_for_bot", gen)
        return bot_repo, closed, count, gen

    def test_only_running_automated_bots_with_feature_set_and_account(self, sessions, monkeypatch):
        bots = [
            _bot(1, "auto"), _bot(2, "approval"), _bot(3, "manual"),
            _bot(4, "auto", feature_set_id=None), _bot(5, "approval", account_id=None),
        ]
        bot_repo, closed, _, gen = self._patch(monkeypatch, bots)

        execution_cycle._generate_automatic_signals()

        bot_repo.list_by_statuses.assert_called_once_with(["running"])
        assert [c.args[1].id for c in gen.call_args_list] == [1, 2]
        assert [c.args[1].id for c in closed.call_args_list] == [1, 2]

    def test_no_automated_bots_opens_no_more_sessions(self, sessions, monkeypatch):
        self._patch(monkeypatch, [_bot(1, "manual")])

        execution_cycle._generate_automatic_signals()

        assert len(sessions.created) == 1
        sessions.created[0].close.assert_called_once()

    def test_bot_without_closed_candle_is_skipped(self, sessions, monkeypatch):
        _, _, count, gen = self._patch(monkeypatch, [_bot(1)], candle_ts=None)

        execution_cycle._generate_automatic_signals()

        gen.assert_not_called()
        count.assert_not_called()

    def test_passes_the_candle_ts_to_generate(self, sessions, monkeypatch):
        candle_ts = NOW - timedelta(hours=1, minutes=7)
        _, _, _, gen = self._patch(monkeypatch, [_bot(1)], candle_ts=candle_ts)

        execution_cycle._generate_automatic_signals()

        assert gen.call_args.args[2] == candle_ts

    def test_daily_cap_per_owner_counts_signals_generated_in_this_cycle(self, sessions, monkeypatch):
        # Tope 3; el dueño 1 ya lleva 2 hoy → solo 1 de sus 3 agentes analiza.
        # El dueño 2 empieza de 0 y no se ve afectado.
        monkeypatch.setattr(settings, "AGENT_MAX_AUTO_ANALYSES_PER_DAY", 3)
        bots = [_bot(1, account_id=100), _bot(2, account_id=100), _bot(3, account_id=100), _bot(4, account_id=200)]
        count = {1: 2, 2: 0}
        _, _, count_mock, gen = self._patch(monkeypatch, bots, owners={100: 1, 200: 2})
        count_mock.side_effect = lambda session, owner_id, since: count[owner_id]

        execution_cycle._generate_automatic_signals()

        assert [c.args[1].id for c in gen.call_args_list] == [1, 4]
        # Se cuenta una sola vez por dueño, desde las 00:00 UTC
        assert count_mock.call_count == 2
        day_start = datetime(2026, 10, 20, tzinfo=timezone.utc)
        assert {c.args[2] for c in count_mock.call_args_list} == {day_start}

    def test_owner_at_cap_gets_no_analysis(self, sessions, monkeypatch):
        monkeypatch.setattr(settings, "AGENT_MAX_AUTO_ANALYSES_PER_DAY", 96)
        _, _, _, gen = self._patch(monkeypatch, [_bot(1)], counted=96)

        execution_cycle._generate_automatic_signals()

        gen.assert_not_called()

    def test_error_in_one_bot_rolls_back_and_continues(self, sessions, monkeypatch):
        gen = MagicMock(side_effect=[RuntimeError("fallo"), None])
        self._patch(monkeypatch, [_bot(1), _bot(2)], generate=gen)

        execution_cycle._generate_automatic_signals()

        assert gen.call_count == 2
        failed_session = gen.call_args_list[0].args[0]
        failed_session.rollback.assert_called_once()
        assert all(s.close.called for s in sessions.created)

    def test_bot_that_raises_does_not_use_up_the_owner_quota(self, sessions, monkeypatch):
        # Si _generate_for_bot lanza, el contador no sube: el siguiente agente del dueño sí analiza
        monkeypatch.setattr(settings, "AGENT_MAX_AUTO_ANALYSES_PER_DAY", 1)
        gen = MagicMock(side_effect=[RuntimeError("fallo"), None])
        self._patch(monkeypatch, [_bot(1), _bot(2)], generate=gen)

        execution_cycle._generate_automatic_signals()

        assert gen.call_count == 2


# ======================================================================
# 1b. ¿Qué vela cerrada toca analizar?
# ======================================================================

class TestClosedCandleToAnalyze:

    def _patch(self, monkeypatch, timeframe_seconds=HOUR, candle_ts=None, feature_ts="same", exists=False):
        monkeypatch.setattr(execution_cycle, "utc_now", lambda: NOW)
        monkeypatch.setattr(settings, "SIGNALS_AUTO_MIN_TIMEFRAME_SECONDS", 900)
        tf_repo = MagicMock()
        tf_repo.get_by_id.return_value = (
            SimpleNamespace(id=1, seconds=timeframe_seconds) if timeframe_seconds else None
        )
        candle_repo = MagicMock()
        candle_repo.list_candles.return_value = [SimpleNamespace(ts=candle_ts)] if candle_ts else []
        feature_repo = MagicMock()
        if feature_ts == "same":
            feature_ts = candle_ts
        feature_repo.list_features.return_value = [SimpleNamespace(ts=feature_ts)] if feature_ts else []
        signal_repo = MagicMock()
        signal_repo.exists_for_candle.return_value = exists
        monkeypatch.setattr(execution_cycle, "SqlAlchemyTimeframeRepository", MagicMock(return_value=tf_repo))
        monkeypatch.setattr(execution_cycle, "SqlAlchemyCandleRepository", MagicMock(return_value=candle_repo))
        monkeypatch.setattr(execution_cycle, "SqlAlchemyCandleFeatureRepository", MagicMock(return_value=feature_repo))
        monkeypatch.setattr(execution_cycle, "SqlAlchemySignalRepository", MagicMock(return_value=signal_repo))
        return candle_repo, feature_repo, signal_repo

    def test_returns_last_closed_candle_with_features_and_no_signal(self, monkeypatch):
        # 12:07 con velas de 1h: la de las 11:00 cerró a las 12:00
        candle_ts = datetime(2026, 10, 20, 11, 0, tzinfo=timezone.utc)
        candle_repo, feature_repo, signal_repo = self._patch(monkeypatch, candle_ts=candle_ts)

        result = execution_cycle._closed_candle_to_analyze(MagicMock(), _bot())

        assert result == candle_ts
        # Solo velas que abrieron hace al menos un timeframe completo (cerradas)
        assert candle_repo.list_candles.call_args.kwargs["to_ts"] == NOW - timedelta(hours=1)
        assert candle_repo.list_candles.call_args.kwargs["limit"] == 1
        assert feature_repo.list_features.call_args.kwargs["feature_set_id"] == 10
        signal_repo.exists_for_candle.assert_called_once_with(1, candle_ts)

    def test_timeframe_below_minimum_is_never_analyzed(self, monkeypatch):
        candle_repo, _, _ = self._patch(monkeypatch, timeframe_seconds=300, candle_ts=NOW - timedelta(minutes=10))

        assert execution_cycle._closed_candle_to_analyze(MagicMock(), _bot()) is None
        candle_repo.list_candles.assert_not_called()

    def test_exactly_the_minimum_timeframe_is_analyzed(self, monkeypatch):
        candle_ts = datetime(2026, 10, 20, 11, 45, tzinfo=timezone.utc)
        self._patch(monkeypatch, timeframe_seconds=900, candle_ts=candle_ts)

        assert execution_cycle._closed_candle_to_analyze(MagicMock(), _bot()) == candle_ts

    def test_unknown_timeframe_returns_none(self, monkeypatch):
        self._patch(monkeypatch, timeframe_seconds=None)

        assert execution_cycle._closed_candle_to_analyze(MagicMock(), _bot()) is None

    def test_no_closed_candle_returns_none(self, monkeypatch):
        self._patch(monkeypatch, candle_ts=None)

        assert execution_cycle._closed_candle_to_analyze(MagicMock(), _bot()) is None

    def test_stale_candle_older_than_two_timeframes_is_skipped(self, monkeypatch):
        # Descarga caída: la última cerrada abrió hace 2h 7min (> 2 × 1h)
        self._patch(monkeypatch, candle_ts=datetime(2026, 10, 20, 10, 0, tzinfo=timezone.utc))

        assert execution_cycle._closed_candle_to_analyze(MagicMock(), _bot()) is None

    def test_candle_exactly_two_timeframes_old_is_still_analyzed(self, monkeypatch):
        candle_ts = NOW - timedelta(hours=2)
        self._patch(monkeypatch, candle_ts=candle_ts)

        assert execution_cycle._closed_candle_to_analyze(MagicMock(), _bot()) == candle_ts

    def test_features_not_yet_calculated_for_that_candle(self, monkeypatch):
        candle_ts = datetime(2026, 10, 20, 11, 0, tzinfo=timezone.utc)
        self._patch(monkeypatch, candle_ts=candle_ts, feature_ts=candle_ts - timedelta(hours=1))

        assert execution_cycle._closed_candle_to_analyze(MagicMock(), _bot()) is None

    def test_no_features_at_all(self, monkeypatch):
        self._patch(monkeypatch, candle_ts=datetime(2026, 10, 20, 11, 0, tzinfo=timezone.utc), feature_ts=None)

        assert execution_cycle._closed_candle_to_analyze(MagicMock(), _bot()) is None

    def test_naive_timestamps_from_mysql_are_compared_as_utc(self, monkeypatch):
        naive = datetime(2026, 10, 20, 11, 0)
        self._patch(monkeypatch, candle_ts=naive, feature_ts=naive)

        result = execution_cycle._closed_candle_to_analyze(MagicMock(), _bot())

        assert result == datetime(2026, 10, 20, 11, 0, tzinfo=timezone.utc)

    def test_candle_that_already_has_a_signal_is_not_analyzed_again(self, monkeypatch):
        self._patch(monkeypatch, candle_ts=datetime(2026, 10, 20, 11, 0, tzinfo=timezone.utc), exists=True)

        assert execution_cycle._closed_candle_to_analyze(MagicMock(), _bot()) is None


class TestCountOwnerSignalsSince:

    def test_counts_signals_of_all_bots_of_all_owner_accounts(self, monkeypatch):
        account_repo = MagicMock()
        account_repo.list_by_user_id.return_value = [SimpleNamespace(id=100), SimpleNamespace(id=101)]
        bot_repo = MagicMock()
        bot_repo.list_by_account_ids.return_value = [SimpleNamespace(id=1), SimpleNamespace(id=2)]
        signal_repo = MagicMock()
        signal_repo.count_created_since.return_value = 7
        monkeypatch.setattr(execution_cycle, "SqlAlchemyAccountRepository", MagicMock(return_value=account_repo))
        monkeypatch.setattr(execution_cycle, "SqlAlchemyBotRepository", MagicMock(return_value=bot_repo))
        monkeypatch.setattr(execution_cycle, "SqlAlchemySignalRepository", MagicMock(return_value=signal_repo))
        since = datetime(2026, 10, 20, tzinfo=timezone.utc)

        assert execution_cycle._count_owner_signals_since(MagicMock(), 5, since) == 7
        account_repo.list_by_user_id.assert_called_once_with(5)
        bot_repo.list_by_account_ids.assert_called_once_with([100, 101])
        signal_repo.count_created_since.assert_called_once_with([1, 2], since)


# ======================================================================
# 1c. Generar la señal y, en auto, ejecutarla
# ======================================================================

class TestGenerateForBot:

    CANDLE = datetime(2026, 10, 20, 11, 0, tzinfo=timezone.utc)

    def _run(self, bot, generate_result=None, generate_error=None, execute_result=None):
        generate = MagicMock()
        if generate_error is not None:
            generate.generate.side_effect = generate_error
        else:
            generate.generate.return_value = generate_result
        bot_factory = MagicMock()
        bot_factory.return_value.generate_signal.return_value = generate
        execute = MagicMock()
        execute.execute.return_value = execute_result or ServiceResult.ok(None)
        order_factory = MagicMock()
        order_factory.return_value.execute_signal.return_value = execute
        session = MagicMock()

        with patch(BOT_FACTORY, bot_factory), patch(ORDER_FACTORY, order_factory):
            execution_cycle._generate_for_bot(session, bot, self.CANDLE)

        return session, generate, execute

    @staticmethod
    def _signal(status="pending", id_=55):
        return SimpleNamespace(id=id_, action="BUY", decision_status=status, is_pending=lambda: status == "pending")

    def test_generates_for_the_candle_without_owner_check(self):
        _, generate, _ = self._run(_bot(1, "approval"), ServiceResult.ok(self._signal()))

        generate.generate.assert_called_once_with(1, owner_id=None, candle_ts=self.CANDLE)

    def test_auto_mode_executes_pending_signal_in_the_same_cycle(self):
        _, _, execute = self._run(_bot(1, "auto"), ServiceResult.ok(self._signal(id_=55)))

        execute.execute.assert_called_once_with(55, owner_id=None, decided_by_user_id=None, channel="auto")

    def test_approval_mode_leaves_signal_pending_for_a_person(self):
        _, _, execute = self._run(_bot(1, "approval"), ServiceResult.ok(self._signal()))

        execute.execute.assert_not_called()

    @pytest.mark.parametrize("status", ["rejected", "expired", "executed"])
    def test_auto_mode_does_not_execute_non_pending_signals(self, status):
        # p. ej. HOLD o R/R < 2:1 → la IA la rechaza y no hay orden
        _, _, execute = self._run(_bot(1, "auto"), ServiceResult.ok(self._signal(status)))

        execute.execute.assert_not_called()

    def test_generation_failure_creates_no_order(self):
        _, _, execute = self._run(_bot(1, "auto"), ServiceResult.fail(code="AGENT_LLM_UNAVAILABLE", http_status=503))

        execute.execute.assert_not_called()

    def test_duplicate_signal_for_the_candle_rolls_back_quietly(self):
        session, _, execute = self._run(
            _bot(1, "auto"), generate_error=IntegrityError("INSERT", {}, Exception("uq_signals_bot_candle"))
        )

        session.rollback.assert_called_once()
        execute.execute.assert_not_called()

    def test_failed_execution_does_not_raise(self):
        self._run(
            _bot(1, "auto"), ServiceResult.ok(self._signal()),
            execute_result=ServiceResult.fail(code="RISK_KILL_SWITCH", http_status=423),
        )


# ======================================================================
# 2–4. Caducar, reconciliar, proteger
# ======================================================================

class TestExpireReconcileProtect:

    def test_expire_marks_pending_as_expired_at_now_and_commits(self, sessions, monkeypatch):
        signal_repo = MagicMock()
        signal_repo.expire_pending.return_value = [3, 4]
        monkeypatch.setattr(execution_cycle, "SqlAlchemySignalRepository", MagicMock(return_value=signal_repo))

        execution_cycle._expire_pending_signals()

        signal_repo.expire_pending.assert_called_once_with(NOW)
        signal_repo.commit.assert_called_once()
        sessions.created[0].close.assert_called_once()

    def test_expire_closes_session_even_on_error(self, sessions, monkeypatch):
        signal_repo = MagicMock()
        signal_repo.expire_pending.side_effect = RuntimeError("BD caída")
        monkeypatch.setattr(execution_cycle, "SqlAlchemySignalRepository", MagicMock(return_value=signal_repo))

        with pytest.raises(RuntimeError):
            execution_cycle._expire_pending_signals()

        signal_repo.commit.assert_not_called()
        sessions.created[0].close.assert_called_once()

    @pytest.mark.parametrize("step, service_name, report", [
        ("_reconcile_orders", "reconcile_orders", SimpleNamespace(checked=3, updated=[1])),
        ("_protect_positions", "protect_positions", SimpleNamespace(checked=2, closed=[9], failed=[])),
    ])
    def test_order_steps_run_their_service_with_own_session(self, sessions, step, service_name, report):
        factory = MagicMock()
        getattr(factory.return_value, service_name).return_value.run.return_value = ServiceResult.ok(report)

        with patch(ORDER_FACTORY, factory):
            getattr(execution_cycle, step)()

        factory.assert_called_once_with(session=sessions.created[0])
        getattr(factory.return_value, service_name).return_value.run.assert_called_once()
        sessions.created[0].close.assert_called_once()

    @pytest.mark.parametrize("step, service_name", [
        ("_reconcile_orders", "reconcile_orders"),
        ("_protect_positions", "protect_positions"),
    ])
    def test_order_steps_close_session_on_error(self, sessions, step, service_name):
        factory = MagicMock()
        getattr(factory.return_value, service_name).return_value.run.side_effect = RuntimeError("exchange caído")

        with patch(ORDER_FACTORY, factory), pytest.raises(RuntimeError):
            getattr(execution_cycle, step)()

        sessions.created[0].close.assert_called_once()


# ======================================================================
# 6. Telegram (polling)
# ======================================================================

POLLER = "app.modules.alerts.channels.telegram_poller.fetch_updates"
BUILD_TELEGRAM = "app.modules.alerts.providers.telegram_provider.build_telegram_update_service"


class TestPollTelegram:

    @pytest.mark.parametrize("mode, token", [("off", "tkn"), ("webhook", "tkn"), ("polling", "")])
    def test_does_nothing_unless_polling_with_token(self, sessions, monkeypatch, mode, token):
        monkeypatch.setattr(settings, "TELEGRAM_UPDATES_MODE", mode)
        monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", token)

        with patch(POLLER) as fetch:
            execution_cycle._poll_telegram()

        fetch.assert_not_called()
        assert sessions.created == []

    def test_each_update_is_handled_in_its_own_session(self, sessions, monkeypatch):
        monkeypatch.setattr(settings, "TELEGRAM_UPDATES_MODE", "polling")
        monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", "tkn")
        service = MagicMock()
        updates = [{"update_id": 1}, {"update_id": 2}]

        with patch(POLLER, return_value=updates) as fetch, patch(BUILD_TELEGRAM, return_value=service):
            execution_cycle._poll_telegram()

        fetch.assert_called_once_with("tkn")
        assert service.handle.call_args_list == [call(updates[0]), call(updates[1])]
        assert len(sessions.created) == 2
        assert all(s.close.called for s in sessions.created)

    def test_failing_update_rolls_back_and_the_next_one_is_processed(self, sessions, monkeypatch):
        monkeypatch.setattr(settings, "TELEGRAM_UPDATES_MODE", "polling")
        monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", "tkn")
        service = MagicMock()
        service.handle.side_effect = [RuntimeError("callback roto"), None]

        with patch(POLLER, return_value=[{"update_id": 1}, {"update_id": 2}]), \
                patch(BUILD_TELEGRAM, return_value=service):
            execution_cycle._poll_telegram()

        assert service.handle.call_count == 2
        sessions.created[0].rollback.assert_called_once()
        sessions.created[1].rollback.assert_not_called()

    def test_without_service_updates_are_skipped(self, sessions, monkeypatch):
        monkeypatch.setattr(settings, "TELEGRAM_UPDATES_MODE", "polling")
        monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", "tkn")

        with patch(POLLER, return_value=[{"update_id": 1}]), patch(BUILD_TELEGRAM, return_value=None):
            execution_cycle._poll_telegram()

        sessions.created[0].close.assert_called_once()
