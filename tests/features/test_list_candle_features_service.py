# -*- coding: utf-8 -*-

# ======================================================================
# tests/features/test_list_candle_features_service.py
# ======================================================================

from datetime import datetime, timezone
from unittest.mock import MagicMock

from app.modules.features.domain.candle_feature_entity import CandleFeature
from app.modules.features.domain.feature_set_entity import FeatureSet
from app.modules.features.services.candle_features.list_candle_features_service import (
    ListCandleFeaturesService,
)
from app.modules.market.domain.symbol_entity import Symbol
from app.modules.market.domain.timeframe_entity import Timeframe


def _make_symbol(id: int = 1) -> Symbol:
    return Symbol(
        id=id,
        exchange_id=1,
        symbol="BTC/USDT",
        asset_class="crypto",
        is_active=True,
    )


def _make_timeframe(id: int = 3) -> Timeframe:
    return Timeframe(id=id, code="1h", seconds=3600)


def _make_feature_set(id: int = 1) -> FeatureSet:
    return FeatureSet(id=id, name="default", version="1.0.0", spec={})


def _make_candle_feature(ts: datetime | None = None) -> CandleFeature:
    return CandleFeature(
        id=1,
        symbol_id=1,
        timeframe_id=3,
        ts=ts or datetime(2026, 1, 1, tzinfo=timezone.utc),
        feature_set_id=1,
        features={"rsi_14": 55.0, "regime": "trend_up"},
    )


def _make_service(symbol=None, timeframe=None, feature_set=None, features=None):
    candle_feature_repo = MagicMock()
    candle_feature_repo.list_features.return_value = features or []

    feature_set_repo = MagicMock()
    feature_set_repo.get_by_id.return_value = feature_set

    symbol_repo = MagicMock()
    symbol_repo.get_by_id.return_value = symbol

    timeframe_repo = MagicMock()
    timeframe_repo.get_by_id.return_value = timeframe

    return ListCandleFeaturesService(
        candle_feature_repo=candle_feature_repo,
        feature_set_repo=feature_set_repo,
        symbol_repo=symbol_repo,
        timeframe_repo=timeframe_repo,
    )


class TestListCandleFeaturesService:

    # ------------------------------------------------------------------
    # Éxito
    # ------------------------------------------------------------------

    def test_returns_features_when_all_valid(self):
        expected = [_make_candle_feature(), _make_candle_feature()]
        svc = _make_service(
            symbol=_make_symbol(),
            timeframe=_make_timeframe(),
            feature_set=_make_feature_set(),
            features=expected,
        )

        result = svc.list(symbol_id=1, timeframe_id=3, feature_set_id=1)

        assert result.success is True
        assert len(result.data) == 2

    def test_returns_empty_list_when_no_features_exist(self):
        svc = _make_service(
            symbol=_make_symbol(),
            timeframe=_make_timeframe(),
            feature_set=_make_feature_set(),
            features=[],
        )

        result = svc.list(symbol_id=1, timeframe_id=3, feature_set_id=1)

        assert result.success is True
        assert result.data == []

    # ------------------------------------------------------------------
    # Validaciones — entidades no encontradas
    # ------------------------------------------------------------------

    def test_fails_if_symbol_not_found(self):
        svc = _make_service(
            symbol=None,
            timeframe=_make_timeframe(),
            feature_set=_make_feature_set(),
        )

        result = svc.list(symbol_id=99, timeframe_id=3, feature_set_id=1)

        assert result.success is False
        assert result.error.code == "SYMBOL_NOT_FOUND"
        assert result.error.http_status == 404

    def test_fails_if_timeframe_not_found(self):
        svc = _make_service(
            symbol=_make_symbol(),
            timeframe=None,
            feature_set=_make_feature_set(),
        )

        result = svc.list(symbol_id=1, timeframe_id=99, feature_set_id=1)

        assert result.success is False
        assert result.error.code == "TIMEFRAME_NOT_FOUND"
        assert result.error.http_status == 404

    def test_fails_if_feature_set_not_found(self):
        svc = _make_service(
            symbol=_make_symbol(),
            timeframe=_make_timeframe(),
            feature_set=None,
        )

        result = svc.list(symbol_id=1, timeframe_id=3, feature_set_id=99)

        assert result.success is False
        assert result.error.code == "FEATURE_SET_NOT_FOUND"
        assert result.error.http_status == 404
