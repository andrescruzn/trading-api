# -*- coding: utf-8 -*-

# ======================================================================
# tests/scheduler/test_scheduler_service.py
#
# Ciclo de datos del scheduler (scheduler_service.run_cycle) y su regla
# de "¿hace falta descargar?" (_should_fetch). Sin BD ni exchange:
# SessionLocal, repositorios y factories van mockeados en el módulo.
# ======================================================================

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.common.config import settings
from app.common.contracts import ServiceResult
from app.modules.scheduler import scheduler_service

NOW = datetime(2026, 10, 20, 12, 0, tzinfo=timezone.utc)
HOUR = 3600


@pytest.fixture(autouse=True)
def _fixed_now(monkeypatch):
    monkeypatch.setattr(scheduler_service, "utc_now", lambda: NOW)


# ======================================================================
# _should_fetch
# ======================================================================

class TestShouldFetch:

    def test_without_candles_loads_500(self):
        assert scheduler_service._should_fetch(None, HOUR) == (True, 500)

    def test_last_candle_expired_fetches_3(self):
        assert scheduler_service._should_fetch(NOW - timedelta(hours=2), HOUR) == (True, 3)

    def test_exactly_one_timeframe_old_counts_as_expired(self):
        assert scheduler_service._should_fetch(NOW - timedelta(seconds=HOUR), HOUR) == (True, 3)

    def test_current_candle_needs_nothing(self):
        assert scheduler_service._should_fetch(NOW - timedelta(seconds=HOUR - 1), HOUR) == (False, 0)

    def test_daily_timeframe_with_candle_from_this_morning_needs_nothing(self):
        assert scheduler_service._should_fetch(NOW - timedelta(hours=12), 86400) == (False, 0)


# ======================================================================
# run_cycle
# ======================================================================

def _bot(symbol_id: int, timeframe_id: int, feature_set_id: int | None):
    return SimpleNamespace(symbol_id=symbol_id, timeframe_id=timeframe_id, feature_set_id=feature_set_id)


class _Cycle:
    """Monta los mocks de run_cycle y deja a mano las llamadas para verificar."""

    def __init__(
        self,
        monkeypatch,
        bots,
        latest: dict[tuple[int, int], datetime | None] | None = None,
        features_latest: dict[tuple[int, int, int], datetime] | None = None,
        fetch_fail: set[tuple[int, int]] | None = None,
        timeframe_seconds: dict[int, int] | None = None,
    ):
        latest = latest or {}
        features_latest = features_latest or {}
        fetch_fail = fetch_fail or set()
        seconds = timeframe_seconds or {1: HOUR, 2: 4 * HOUR}

        self.sessions: list[MagicMock] = []
        monkeypatch.setattr(scheduler_service, "SessionLocal", self._new_session)

        bot_repo = MagicMock()
        bot_repo.list_by_statuses.return_value = bots
        self.bot_repo_cls = MagicMock(return_value=bot_repo)

        tf_repo = MagicMock()
        tf_repo.get_by_id.side_effect = lambda tf_id: (
            SimpleNamespace(id=tf_id, seconds=seconds[tf_id]) if tf_id in seconds else None
        )

        self.candle_repo = MagicMock()
        self.candle_repo.get_latest_ts.side_effect = lambda s, t: latest.get((s, t))
        self.candle_repo.delete_beyond_retention.return_value = 0

        self.feature_repo = MagicMock()
        self.feature_repo.list_features.side_effect = lambda symbol_id, timeframe_id, feature_set_id, limit: (
            [SimpleNamespace(ts=features_latest[(symbol_id, timeframe_id, feature_set_id)])]
            if (symbol_id, timeframe_id, feature_set_id) in features_latest else []
        )
        self.feature_repo.delete_beyond_retention.return_value = 0

        self.fetch = MagicMock()
        self.fetch.fetch.side_effect = lambda symbol_id, timeframe_id, limit: (
            ServiceResult.fail(code="CCXT_NETWORK_ERROR", http_status=503)
            if (symbol_id, timeframe_id) in fetch_fail
            else ServiceResult.ok({"rows_fetched": limit})
        )
        market_factory = MagicMock()
        market_factory.fetch_candles.return_value = self.fetch

        self.calculate = MagicMock()
        self.calculate.calculate.return_value = ServiceResult.ok({"rows_calculated": 10})
        feature_factory = MagicMock()
        feature_factory.calculate_features.return_value = self.calculate

        monkeypatch.setattr(scheduler_service, "SqlAlchemyBotRepository", self.bot_repo_cls)
        monkeypatch.setattr(scheduler_service, "SqlAlchemyTimeframeRepository", MagicMock(return_value=tf_repo))
        monkeypatch.setattr(scheduler_service, "SqlAlchemyCandleRepository", MagicMock(return_value=self.candle_repo))
        monkeypatch.setattr(
            scheduler_service, "SqlAlchemyCandleFeatureRepository", MagicMock(return_value=self.feature_repo)
        )
        monkeypatch.setattr(scheduler_service, "MarketServiceFactory", MagicMock(return_value=market_factory))
        monkeypatch.setattr(scheduler_service, "FeatureServiceFactory", MagicMock(return_value=feature_factory))
        monkeypatch.setattr(settings, "SCHEDULER_RETENTION_CANDLES", 500)

    def _new_session(self):
        session = MagicMock()
        self.sessions.append(session)
        return session

    @property
    def fetched(self) -> dict[tuple[int, int], int]:
        return {(c.kwargs["symbol_id"], c.kwargs["timeframe_id"]): c.kwargs["limit"] for c in self.fetch.fetch.call_args_list}

    @property
    def calculated(self) -> set[tuple[int, int, int]]:
        return {
            (c.kwargs["symbol_id"], c.kwargs["timeframe_id"], c.kwargs["feature_set_id"])
            for c in self.calculate.calculate.call_args_list
        }


class TestRunCycle:

    def test_without_active_bots_does_nothing(self, monkeypatch):
        cycle = _Cycle(monkeypatch, bots=[])

        scheduler_service.run_cycle()

        cycle.bot_repo_cls.return_value.list_by_statuses.assert_called_once_with(["running", "paused"])
        cycle.fetch.fetch.assert_not_called()
        assert all(s.close.called for s in cycle.sessions)

    def test_downloads_each_pair_once_with_the_right_limit(self, monkeypatch):
        bots = [_bot(1, 1, 10), _bot(1, 1, 11), _bot(2, 1, 10), _bot(3, 2, 10)]
        latest = {
            (1, 1): NOW - timedelta(hours=1, minutes=5),   # vencida → 3
            (2, 1): None,                                   # sin velas → 500
            (3, 2): NOW - timedelta(hours=1),               # 4h vigente → nada
        }
        features = {(3, 2, 10): NOW - timedelta(hours=1)}
        cycle = _Cycle(monkeypatch, bots, latest=latest, features_latest=features)

        scheduler_service.run_cycle()

        assert cycle.fetched == {(1, 1): 3, (2, 1): 500}

    def test_new_candles_recalculate_every_feature_set_of_the_pair_and_clean_up(self, monkeypatch):
        bots = [_bot(1, 1, 10), _bot(1, 1, 11), _bot(2, 1, None)]
        cycle = _Cycle(monkeypatch, bots, latest={(1, 1): None, (2, 1): None})

        scheduler_service.run_cycle()

        assert cycle.calculated == {(1, 1, 10), (1, 1, 11)}   # el bot sin feature set no calcula
        deleted_candles = {c.args for c in cycle.candle_repo.delete_beyond_retention.call_args_list}
        assert deleted_candles == {(1, 1, 500), (2, 1, 500)}
        deleted_features = {c.args for c in cycle.feature_repo.delete_beyond_retention.call_args_list}
        assert deleted_features == {(1, 1, 10, 500), (1, 1, 11, 500)}

    def test_stale_features_are_recalculated_without_downloading(self, monkeypatch):
        # Velas al día, pero el conjunto 11 nunca se calculó y el 10 va una vela atrás
        last_candle = NOW - timedelta(minutes=30)
        bots = [_bot(1, 1, 10), _bot(1, 1, 11), _bot(1, 1, 12)]
        features = {(1, 1, 10): last_candle - timedelta(hours=1), (1, 1, 12): last_candle}
        cycle = _Cycle(monkeypatch, bots, latest={(1, 1): last_candle}, features_latest=features)

        scheduler_service.run_cycle()

        cycle.fetch.fetch.assert_not_called()
        assert cycle.calculated == {(1, 1, 10), (1, 1, 11)}
        cycle.candle_repo.delete_beyond_retention.assert_not_called()

    def test_everything_up_to_date_skips_the_cycle(self, monkeypatch):
        last_candle = NOW - timedelta(minutes=30)
        cycle = _Cycle(
            monkeypatch, [_bot(1, 1, 10)],
            latest={(1, 1): last_candle}, features_latest={(1, 1, 10): last_candle},
        )

        scheduler_service.run_cycle()

        cycle.fetch.fetch.assert_not_called()
        cycle.calculate.calculate.assert_not_called()

    def test_failed_download_does_not_clean_or_calculate_and_does_not_stop_others(self, monkeypatch):
        bots = [_bot(1, 1, 10), _bot(2, 1, 10)]
        cycle = _Cycle(monkeypatch, bots, latest={(1, 1): None, (2, 1): None}, fetch_fail={(1, 1)})

        scheduler_service.run_cycle()

        assert set(cycle.fetched) == {(1, 1), (2, 1)}
        assert {c.args[:2] for c in cycle.candle_repo.delete_beyond_retention.call_args_list} == {(2, 1)}
        assert cycle.calculated == {(2, 1, 10)}

    def test_exception_in_one_download_is_isolated(self, monkeypatch):
        bots = [_bot(1, 1, 10), _bot(2, 1, 10)]
        cycle = _Cycle(monkeypatch, bots, latest={(1, 1): None, (2, 1): None})
        ok_effect = cycle.fetch.fetch.side_effect

        def flaky(symbol_id, timeframe_id, limit):
            if symbol_id == 1:
                raise RuntimeError("exchange caído")
            return ok_effect(symbol_id=symbol_id, timeframe_id=timeframe_id, limit=limit)

        cycle.fetch.fetch.side_effect = flaky

        scheduler_service.run_cycle()

        assert cycle.calculated == {(2, 1, 10)}
        assert all(s.close.called for s in cycle.sessions)

    def test_bot_with_unknown_timeframe_is_not_downloaded(self, monkeypatch):
        cycle = _Cycle(monkeypatch, [_bot(1, 99, 10)], latest={(1, 99): None})

        scheduler_service.run_cycle()

        cycle.fetch.fetch.assert_not_called()

    def test_uses_configured_retention(self, monkeypatch):
        cycle = _Cycle(monkeypatch, [_bot(1, 1, 10)], latest={(1, 1): None})
        monkeypatch.setattr(settings, "SCHEDULER_RETENTION_CANDLES", 1200)

        scheduler_service.run_cycle()

        cycle.candle_repo.delete_beyond_retention.assert_called_once_with(1, 1, 1200)
        cycle.feature_repo.delete_beyond_retention.assert_called_once_with(1, 1, 10, 1200)
        assert cycle.candle_repo.commit.called and cycle.feature_repo.commit.called
