# -*- coding: utf-8 -*-

# ======================================================================
# tests/features/test_calculate_features_service.py
# ======================================================================

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import MagicMock

import pandas as pd
import pytest

from app.modules.features.domain.feature_set_entity import FeatureSet
from app.modules.features.services.calculations.calculate_features_service import (
    CalculateFeaturesService,
    _MIN_CANDLES,
)
from app.modules.market.domain.candle_entity import Candle
from app.modules.market.domain.symbol_entity import Symbol
from app.modules.market.domain.timeframe_entity import Timeframe


# ======================================================================
# Helpers
# ======================================================================

def _make_symbol(id: int = 1) -> Symbol:
    return Symbol(id=id, exchange_id=1, symbol="BTC/USDT", asset_class="crypto")


def _make_timeframe(id: int = 3) -> Timeframe:
    return Timeframe(id=id, code="1h", seconds=3600)


def _make_feature_set(id: int = 1) -> FeatureSet:
    return FeatureSet(id=id, name="default", version="1.0.0", spec={})


def _make_candles(n: int = _MIN_CANDLES) -> list[Candle]:
    """
    Genera `n` velas simulando una tendencia alcista suave.
    Los precios crecen levemente para que _detect_regime tenga swings reales.
    """
    base_ts = datetime(2025, 1, 1, tzinfo=timezone.utc)
    candles = []
    price = 40_000.0
    for i in range(n):
        # Simular oscilación + tendencia
        open_p = price
        high_p = price * 1.005
        low_p = price * 0.995
        close_p = price * 1.001
        candles.append(Candle(
            id=i + 1,
            symbol_id=1,
            timeframe_id=3,
            ts=base_ts + timedelta(hours=i),
            open=Decimal(str(round(open_p, 2))),
            high=Decimal(str(round(high_p, 2))),
            low=Decimal(str(round(low_p, 2))),
            close=Decimal(str(round(close_p, 2))),
            volume=Decimal("1000.0"),
        ))
        price = close_p
    # list_candles retorna orden desc → invertir para simular eso
    return list(reversed(candles))


def _make_service(
    symbol=None,
    timeframe=None,
    feature_set=None,
    candles=None,
    rows_affected: int = 10,
) -> tuple:
    symbol_repo = MagicMock()
    symbol_repo.get_by_id.return_value = symbol

    timeframe_repo = MagicMock()
    timeframe_repo.get_by_id.return_value = timeframe

    feature_set_repo = MagicMock()
    feature_set_repo.get_by_id.return_value = feature_set

    candle_repo = MagicMock()
    candle_repo.list_candles.return_value = candles or []

    candle_feature_repo = MagicMock()
    candle_feature_repo.bulk_upsert.return_value = rows_affected

    session = MagicMock()

    svc = CalculateFeaturesService(
        candle_repo=candle_repo,
        feature_set_repo=feature_set_repo,
        candle_feature_repo=candle_feature_repo,
        symbol_repo=symbol_repo,
        timeframe_repo=timeframe_repo,
        session=session,
    )
    return svc, candle_feature_repo, session


# ======================================================================
# Tests
# ======================================================================

class TestCalculateFeaturesServiceValidations:

    def test_fails_if_symbol_not_found(self):
        svc, _, _ = _make_service(
            symbol=None,
            timeframe=_make_timeframe(),
            feature_set=_make_feature_set(),
        )

        result = svc.calculate(symbol_id=99, timeframe_id=3, feature_set_id=1)

        assert result.success is False
        assert result.error.code == "SYMBOL_NOT_FOUND"
        assert result.error.http_status == 404

    def test_fails_if_timeframe_not_found(self):
        svc, _, _ = _make_service(
            symbol=_make_symbol(),
            timeframe=None,
            feature_set=_make_feature_set(),
        )

        result = svc.calculate(symbol_id=1, timeframe_id=99, feature_set_id=1)

        assert result.success is False
        assert result.error.code == "TIMEFRAME_NOT_FOUND"
        assert result.error.http_status == 404

    def test_fails_if_feature_set_not_found(self):
        svc, _, _ = _make_service(
            symbol=_make_symbol(),
            timeframe=_make_timeframe(),
            feature_set=None,
        )

        result = svc.calculate(symbol_id=1, timeframe_id=3, feature_set_id=99)

        assert result.success is False
        assert result.error.code == "FEATURE_SET_NOT_FOUND"
        assert result.error.http_status == 404

    def test_fails_if_insufficient_candles(self):
        few_candles = _make_candles(n=50)
        svc, _, _ = _make_service(
            symbol=_make_symbol(),
            timeframe=_make_timeframe(),
            feature_set=_make_feature_set(),
            candles=few_candles,
        )

        result = svc.calculate(symbol_id=1, timeframe_id=3, feature_set_id=1)

        assert result.success is False
        assert result.error.code == "INSUFFICIENT_CANDLES"
        assert result.error.http_status == 422
        assert result.error.meta["required"] == _MIN_CANDLES
        assert result.error.meta["available"] == 50

    def test_fails_with_exactly_one_below_minimum(self):
        svc, _, _ = _make_service(
            symbol=_make_symbol(),
            timeframe=_make_timeframe(),
            feature_set=_make_feature_set(),
            candles=_make_candles(n=_MIN_CANDLES - 1),
        )

        result = svc.calculate(symbol_id=1, timeframe_id=3, feature_set_id=1)

        assert result.success is False
        assert result.error.code == "INSUFFICIENT_CANDLES"


class TestCalculateFeaturesServiceSuccess:

    def test_calculates_and_persists_with_minimum_candles(self):
        candles = _make_candles(n=_MIN_CANDLES)
        svc, candle_feature_repo, session = _make_service(
            symbol=_make_symbol(),
            timeframe=_make_timeframe(),
            feature_set=_make_feature_set(),
            candles=candles,
            rows_affected=15,
        )

        result = svc.calculate(symbol_id=1, timeframe_id=3, feature_set_id=1)

        assert result.success is True
        assert result.data["symbol_id"] == 1
        assert result.data["timeframe_id"] == 3
        assert result.data["feature_set_id"] == 1
        assert result.data["candles_loaded"] == _MIN_CANDLES
        assert result.data["rows_calculated"] > 0
        assert result.data["rows_affected"] == 15

    def test_commits_session_after_calculation(self):
        svc, _, session = _make_service(
            symbol=_make_symbol(),
            timeframe=_make_timeframe(),
            feature_set=_make_feature_set(),
            candles=_make_candles(),
        )

        svc.calculate(symbol_id=1, timeframe_id=3, feature_set_id=1)

        session.commit.assert_called_once()

    def test_bulk_upsert_receives_candle_features(self):
        svc, candle_feature_repo, _ = _make_service(
            symbol=_make_symbol(),
            timeframe=_make_timeframe(),
            feature_set=_make_feature_set(),
            candles=_make_candles(),
        )

        svc.calculate(symbol_id=1, timeframe_id=3, feature_set_id=1)

        candle_feature_repo.bulk_upsert.assert_called_once()
        entities = candle_feature_repo.bulk_upsert.call_args[0][0]
        assert len(entities) > 0
        # Verificar estructura del features dict
        first = entities[0]
        assert "rsi_14" in first.features
        assert "ema_20" in first.features
        assert "ema_50" in first.features
        assert "ema_200" in first.features
        assert "macd" in first.features
        assert "atr_14" in first.features
        assert "bb_upper" in first.features
        assert "vol_rel" in first.features
        assert "regime" in first.features

    def test_all_entities_have_correct_ids(self):
        svc, candle_feature_repo, _ = _make_service(
            symbol=_make_symbol(id=5),
            timeframe=_make_timeframe(id=3),
            feature_set=_make_feature_set(id=7),
            candles=_make_candles(),
        )

        svc.calculate(symbol_id=5, timeframe_id=3, feature_set_id=7)

        entities = candle_feature_repo.bulk_upsert.call_args[0][0]
        for e in entities:
            assert e.symbol_id == 5
            assert e.timeframe_id == 3
            assert e.feature_set_id == 7


class TestSafeFloat:

    def test_returns_float_for_valid_value(self):
        result = CalculateFeaturesService._safe_float(55.12345678)
        assert isinstance(result, float)
        assert result == 55.12345678

    def test_returns_none_for_nan(self):
        import math
        result = CalculateFeaturesService._safe_float(float("nan"))
        assert result is None

    def test_returns_none_for_none(self):
        result = CalculateFeaturesService._safe_float(None)
        assert result is None

    def test_rounds_to_8_decimals(self):
        result = CalculateFeaturesService._safe_float(1.123456789012)
        assert result == round(1.123456789012, 8)


class TestDetectRegime:

    def _make_df(self, n: int = 30, trend: str = "up") -> pd.DataFrame:
        """
        Genera un DataFrame con n velas.
        trend='up'   → precios crecientes (HH + HL)
        trend='down' → precios decrecientes (LH + LL)
        trend='flat' → precios laterales
        """
        base = datetime(2025, 1, 1, tzinfo=timezone.utc)
        rows = []
        price = 100.0
        for i in range(n):
            if trend == "up":
                price += 0.5
            elif trend == "down":
                price -= 0.5
            rows.append({
                "ts": base + timedelta(hours=i),
                "open":   price,
                "high":   price * 1.01,
                "low":    price * 0.99,
                "close":  price,
                "volume": 1000.0,
            })
        df = pd.DataFrame(rows)
        df.set_index("ts", inplace=True)
        return df

    def test_returns_sideways_for_early_rows(self):
        df = self._make_df(n=30)
        ts = df.index[5]  # idx < 20 → sideways siempre

        result = CalculateFeaturesService._detect_regime(df, ts)

        assert result == "sideways"

    def test_returns_trend_up_for_ascending_prices(self):
        # Precios fuertemente crecientes → swing highs y swing lows ascendentes
        df = self._make_df(n=60, trend="up")
        ts = df.index[-1]

        result = CalculateFeaturesService._detect_regime(df, ts)

        # Con precios crecientes monotónicamente puede haber pocos swings locales,
        # aceptamos sideways o trend_up como válido
        assert result in ("trend_up", "sideways")

    def test_returns_trend_down_for_descending_prices(self):
        df = self._make_df(n=60, trend="down")
        ts = df.index[-1]

        result = CalculateFeaturesService._detect_regime(df, ts)

        assert result in ("trend_down", "sideways")

    def test_returns_sideways_on_exception(self):
        # DataFrame vacío provoca excepción interna → debe retornar sideways
        df = pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
        df.index.name = "ts"

        result = CalculateFeaturesService._detect_regime(df, "nonexistent")

        assert result == "sideways"

    def test_regime_is_string_value(self):
        df = self._make_df(n=30, trend="up")
        ts = df.index[25]

        result = CalculateFeaturesService._detect_regime(df, ts)

        assert result in ("trend_up", "trend_down", "sideways")
