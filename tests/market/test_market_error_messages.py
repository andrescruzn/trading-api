# -*- coding: utf-8 -*-

# ======================================================================
# tests/market/test_market_error_messages.py
#
# Todo código de error que devuelven los servicios de M2 tiene su texto
# en el `error_messages.py` del recurso que lo expone. Si falta, la UI
# mostraría un mensaje genérico en lugar del texto en español.
# ======================================================================

from __future__ import annotations

import pytest

from app.modules.market.rest.candles.error_messages import CANDLE_ERROR_MESSAGES
from app.modules.market.rest.exchanges.error_messages import EXCHANGE_ERROR_MESSAGES
from app.modules.market.rest.explorer.error_messages import EXPLORER_ERROR_MESSAGES
from app.modules.market.rest.symbols.error_messages import SYMBOL_ERROR_MESSAGES
from app.modules.market.rest.timeframes.error_messages import TIMEFRAME_ERROR_MESSAGES

CODES_BY_RESOURCE = {
    "candles": (CANDLE_ERROR_MESSAGES, [
        "SYMBOL_NOT_FOUND", "TIMEFRAME_NOT_FOUND", "EXCHANGE_NOT_FOUND",
        "EXCHANGE_NOT_SUPPORTED_CCXT", "CCXT_SYMBOL_NOT_FOUND", "CCXT_NETWORK_ERROR",
        "CCXT_FETCH_ERROR", "CANDLES_EMPTY_PAYLOAD", "CANDLES_INVALID_ROW", "CANDLES_INVALID_OHLCV",
    ]),
    "exchanges": (EXCHANGE_ERROR_MESSAGES, ["EXCHANGE_NOT_FOUND", "EXCHANGE_NAME_EXISTS", "EXCHANGE_INVALID_TYPE"]),
    "symbols": (SYMBOL_ERROR_MESSAGES, [
        "SYMBOL_NOT_FOUND", "SYMBOL_ALREADY_EXISTS", "SYMBOL_INVALID_ASSET_CLASS", "EXCHANGE_NOT_FOUND",
    ]),
    "timeframes": (TIMEFRAME_ERROR_MESSAGES, ["TIMEFRAME_CODE_EXISTS", "TIMEFRAME_INVALID_SECONDS"]),
    "explorer": (EXPLORER_ERROR_MESSAGES, ["EXPLORER_TIMEFRAME_MISSING"]),
}


@pytest.mark.parametrize(
    "resource, code",
    [(resource, code) for resource, (_, codes) in CODES_BY_RESOURCE.items() for code in codes],
)
def test_every_service_error_code_has_a_ui_message(resource, code):
    messages, _ = CODES_BY_RESOURCE[resource]

    assert messages.get(code, "").strip(), f"{resource}: falta el texto de {code}"
