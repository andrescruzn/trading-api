# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/strategies/rest/backtests/error_messages.py
# ======================================================================

BACKTEST_ERROR_MESSAGES: dict[str, str] = {
    "STRATEGY_NOT_FOUND":              "No encontramos esa estrategia.",
    "BACKTEST_STRATEGY_WITHOUT_RULES": "Esta estrategia no tiene reglas: no hay nada que probar.",
    "BACKTEST_NOT_ENOUGH_HISTORY": (
        "El exchange no tiene suficiente historia de este símbolo y timeframe para "
        "calcular los indicadores. Prueba con un timeframe más corto o menos velas."
    ),
    "SYMBOL_NOT_FOUND":                "No encontramos ese símbolo.",
    "TIMEFRAME_NOT_FOUND":             "No encontramos ese timeframe.",
    "EXCHANGE_NOT_SUPPORTED_CCXT":     "No podemos traer la historia de este exchange automáticamente.",
    "CCXT_SYMBOL_NOT_FOUND":           "El exchange no ofrece este símbolo.",
    "CCXT_NETWORK_ERROR":              "No pudimos conectar con el exchange. Intenta de nuevo en un momento.",
    "CCXT_FETCH_ERROR":                "El exchange no devolvió la historia. Intenta de nuevo en un momento.",
}
