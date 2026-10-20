# -*- coding: utf-8 -*-

# ======================================================================
# tests/bots/test_sync_bot_market_data_service.py
# ======================================================================

from unittest.mock import MagicMock

from app.common.contracts import ServiceResult
from app.modules.bots.services.bots import sync_bot_market_data_service as module
from app.modules.bots.services.bots.sync_bot_market_data_service import SyncBotMarketDataService


def _make_bot(feature_set_id=4):
    bot = MagicMock()
    bot.id = 10
    bot.symbol_id = 1
    bot.timeframe_id = 2
    bot.feature_set_id = feature_set_id
    return bot


def _make_service(monkeypatch, bot, fetch_result=None, calc_result=None):
    monkeypatch.setattr(module, "find_accessible_bot", lambda *args: bot)
    fetch = MagicMock()
    fetch.fetch.return_value = fetch_result or ServiceResult.ok({"rows_fetched": 500})
    calc = MagicMock()
    calc.calculate.return_value = calc_result or ServiceResult.ok({"rows_calculated": 280})
    svc = SyncBotMarketDataService(
        bot_repo=MagicMock(),
        account_repo=MagicMock(),
        fetch_candles=fetch,
        calculate_features=calc,
    )
    return svc, fetch, calc


class TestSyncBotMarketDataService:

    def test_fetches_candles_and_calculates_features(self, monkeypatch):
        svc, fetch, calc = _make_service(monkeypatch, _make_bot())

        result = svc.sync(bot_id=10, owner_id=3)

        assert result.success is True
        assert result.data == {"rows_fetched": 500, "rows_calculated": 280}
        fetch.fetch.assert_called_once_with(symbol_id=1, timeframe_id=2, limit=500)
        calc.calculate.assert_called_once_with(symbol_id=1, timeframe_id=2, feature_set_id=4)

    def test_without_feature_set_only_fetches(self, monkeypatch):
        svc, _, calc = _make_service(monkeypatch, _make_bot(feature_set_id=None))

        result = svc.sync(bot_id=10, owner_id=3)

        assert result.data == {"rows_fetched": 500, "rows_calculated": None}
        calc.calculate.assert_not_called()

    def test_foreign_or_missing_bot_is_not_found(self, monkeypatch):
        svc, fetch, _ = _make_service(monkeypatch, bot=None)

        result = svc.sync(bot_id=10, owner_id=3)

        assert result.error.code == "BOT_NOT_FOUND"
        assert result.error.http_status == 404
        fetch.fetch.assert_not_called()

    def test_fetch_failure_is_returned_and_skips_calculation(self, monkeypatch):
        failure = ServiceResult.fail(code="CCXT_NETWORK_ERROR", http_status=503)
        svc, _, calc = _make_service(monkeypatch, _make_bot(), fetch_result=failure)

        result = svc.sync(bot_id=10, owner_id=3)

        assert result.error.code == "CCXT_NETWORK_ERROR"
        calc.calculate.assert_not_called()

    def test_calculation_failure_is_returned(self, monkeypatch):
        failure = ServiceResult.fail(code="INSUFFICIENT_CANDLES", http_status=422)
        svc, _, _ = _make_service(monkeypatch, _make_bot(), calc_result=failure)

        result = svc.sync(bot_id=10, owner_id=3)

        assert result.error.code == "INSUFFICIENT_CANDLES"
