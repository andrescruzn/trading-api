# -*- coding: utf-8 -*-

# ======================================================================
# tests/market/test_market_domain.py
#
# Reglas puras del dominio de M2: exchanges con descarga automática
# (ccxt), perpetuos vs spot, validación OHLCV de una vela y tipos/clases
# válidos de exchanges, símbolos y timeframes.
# ======================================================================

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.modules.market.domain.candle_entity import Candle
from app.modules.market.domain.ccxt_exchanges import ccxt_id_for, is_perpetual, supports_auto_fetch
from app.modules.market.domain.exchange_entity import Exchange
from app.modules.market.domain.symbol_entity import Symbol
from app.modules.market.domain.timeframe_entity import Timeframe

D = Decimal
T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _candle(o="100", h="110", low="90", c="105", v="1") -> Candle:
    return Candle(id=0, symbol_id=1, timeframe_id=1, ts=T0, open=D(o), high=D(h), low=D(low), close=D(c), volume=D(v))


# ======================================================================
# ccxt_exchanges
# ======================================================================

class TestIsPerpetual:

    @pytest.mark.parametrize("symbol", ["XAU/USDT:USDT", "NVDA/USDT:USDT", "BTC/USD:BTC"])
    def test_contracts_with_settle_currency_are_perpetual(self, symbol):
        assert is_perpetual(symbol) is True

    @pytest.mark.parametrize("symbol", ["BTC/USDT", "PAXG/USDT", "", None])
    def test_spot_empty_or_missing_symbols_are_not_perpetual(self, symbol):
        assert is_perpetual(symbol) is False


class TestCcxtExchangeMap:

    @pytest.mark.parametrize("name", ["Binance", "BINANCE", "binance"])
    def test_binance_maps_to_ccxt_id_ignoring_case(self, name):
        assert ccxt_id_for(name) == "binance"
        assert supports_auto_fetch(name) is True

    @pytest.mark.parametrize("name", ["Bybit", "OKX", "TradingView", "Desconocido", "", None])
    def test_unsupported_exchanges_have_no_auto_fetch(self, name):
        assert ccxt_id_for(name) is None
        assert supports_auto_fetch(name) is False


# ======================================================================
# Candle.is_valid_ohlcv
# ======================================================================

class TestCandleIsValidOhlcv:

    def test_normal_candle_is_valid(self):
        assert _candle().is_valid_ohlcv() is True

    def test_flat_candle_with_zero_volume_is_valid(self):
        assert _candle(o="100", h="100", low="100", c="100", v="0").is_valid_ohlcv() is True

    def test_high_below_low_is_invalid(self):
        assert _candle(h="89", low="90").is_valid_ohlcv() is False

    @pytest.mark.parametrize("field", ["o", "h", "low", "c", "v"])
    def test_negative_values_are_invalid(self, field):
        values = {"o": "100", "h": "110", "low": "90", "c": "105", "v": "1"}
        values[field] = "-1"
        if field == "h":
            values["low"] = "-2"  # aísla la regla del negativo de la de high >= low
        assert _candle(**values).is_valid_ohlcv() is False

    @pytest.mark.parametrize("field", ["o", "h", "low", "c", "v"])
    def test_non_finite_values_are_invalid_instead_of_raising(self, field):
        # Decimal('NaN') en una comparación de orden lanza InvalidOperation:
        # una vela así debe descartarse, no tumbar la descarga entera.
        values = {"o": "100", "h": "110", "low": "90", "c": "105", "v": "1"}
        values[field] = "NaN"
        assert _candle(**values).is_valid_ohlcv() is False

    def test_infinite_price_is_invalid(self):
        assert _candle(h="Infinity").is_valid_ohlcv() is False


# ======================================================================
# Tipos y clases válidas
# ======================================================================

class TestCatalogValidation:

    @pytest.mark.parametrize("type_", ["crypto_exchange", "broker", "data_vendor"])
    def test_valid_exchange_types(self, type_):
        assert Exchange(id=0, name="X", type=type_).is_valid_type() is True

    def test_invalid_exchange_type(self):
        assert Exchange(id=0, name="X", type="bank").is_valid_type() is False

    def test_exchange_activate_and_deactivate(self):
        exchange = Exchange(id=1, name="Binance", type="crypto_exchange")
        exchange.deactivate()
        assert exchange.is_active is False
        exchange.activate()
        assert exchange.is_active is True

    @pytest.mark.parametrize("asset_class", ["crypto", "metal", "commodity", "index", "etf", "stock", "forex"])
    def test_valid_asset_classes(self, asset_class):
        assert Symbol(id=0, exchange_id=1, symbol="X/USDT", asset_class=asset_class).is_valid_asset_class()

    def test_invalid_asset_class(self):
        assert Symbol(id=0, exchange_id=1, symbol="X/USDT", asset_class="bond").is_valid_asset_class() is False

    def test_timeframe_needs_code_and_positive_seconds(self):
        assert Timeframe(id=1, code="1h", seconds=3600).is_valid() is True
        assert Timeframe(id=1, code="  ", seconds=3600).is_valid() is False
        assert Timeframe(id=1, code="1h", seconds=0).is_valid() is False
