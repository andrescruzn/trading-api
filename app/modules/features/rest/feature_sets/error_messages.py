# -*- coding: utf-8 -*-

FEATURE_SET_ERROR_MESSAGES: dict[str, str] = {
    "FEATURE_SET_ALREADY_EXISTS": "Ya existe un conjunto de indicadores con ese nombre y versión.",
    "FEATURE_SET_NOT_FOUND": "No encontramos ese conjunto de indicadores.",
    "FEATURE_SET_INVALID_INDICATORS": (
        "El conjunto pide indicadores que no sabemos calcular. "
        "Usa solo: rsi, ema, macd, atr, bbands, vol_rel."
    ),
    "FEATURE_SET_INVALID_FOCUS": (
        "El enfoque debe ser all, trend_following o mean_reversion."
    ),
}
