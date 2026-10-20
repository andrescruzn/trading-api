# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/features/domain/indicator_engine.py
#
# Cálculo de indicadores y régimen sobre velas en memoria, sin BD.
# Lo usan:
# - CalculateFeaturesService: calcula y guarda en `candle_features`.
# - El backtesting de M5: calcula sobre historia traída del exchange sin
#   guardarla (la retención del scheduler solo deja unas 500 velas).
#
# Indicadores (pandas-ta): RSI(14), EMA(20/50/200), MACD(12,26,9),
# ATR(14), Bollinger(20,2), volumen relativo y régimen HH/HL.
# ======================================================================

from __future__ import annotations

import math
from datetime import datetime
from typing import Any, Protocol

import pandas as pd
import pandas_ta as ta  # noqa: F401  (registra el accessor `df.ta`)

from app.modules.features.domain.indicator_catalog import INDICATOR_GROUPS

# Número mínimo de velas para calcular EMA(200) con margen
MIN_CANDLES = 220

# Clave de salida → columna que genera pandas-ta
_OUTPUT_COLUMNS: dict[str, str] = {
    "rsi_14": "RSI_14",
    "ema_20": "EMA_20",
    "ema_50": "EMA_50",
    "ema_200": "EMA_200",
    "macd": "MACD_12_26_9",
    "macd_signal": "MACDs_12_26_9",
    "macd_hist": "MACDh_12_26_9",
    "atr_14": "ATRr_14",
    "bb_upper": "BBU_20_2.0_2.0",
    "bb_mid": "BBM_20_2.0_2.0",
    "bb_lower": "BBL_20_2.0_2.0",
    "bb_bandwidth": "BBB_20_2.0_2.0",
    "vol_rel": "vol_rel",
}

# Columna que debe existir sin NaN, por grupo, para considerar la fila válida
_REQUIRED_BY_GROUP: dict[str, tuple[str, ...]] = {
    "rsi": ("RSI_14",),
    "ema": ("EMA_20", "EMA_50", "EMA_200"),
    "atr": ("ATRr_14",),
}


class OhlcvBar(Protocol):
    ts: datetime
    open: Any
    high: Any
    low: Any
    close: Any
    volume: Any


def compute_feature_rows(
    candles: list[OhlcvBar], groups: list[str]
) -> list[tuple[datetime, dict]]:
    """
    Indicadores de los `groups` (y el régimen, siempre) para cada vela con
    datos completos. Las velas deben venir de la más antigua a la más nueva.
    """
    output_keys = [key for group in groups for key in INDICATOR_GROUPS[group]]

    df = pd.DataFrame([{
        "ts": c.ts,
        "open": float(c.open),
        "high": float(c.high),
        "low": float(c.low),
        "close": float(c.close),
        "volume": float(c.volume),
    } for c in candles])
    df.set_index("ts", inplace=True)

    df.ta.rsi(length=14, append=True)
    df.ta.ema(length=20, append=True)
    df.ta.ema(length=50, append=True)
    df.ta.ema(length=200, append=True)
    df.ta.macd(fast=12, slow=26, signal=9, append=True)
    df.ta.atr(length=14, append=True)
    df.ta.bbands(length=20, std=2, append=True)

    # Volumen relativo: vol / media_móvil_vol_20
    df["vol_rel"] = df["volume"] / df["volume"].rolling(20).mean()

    df["regime"] = [_detect_regime(df, i) for i in range(len(df))]

    required_cols = [col for group in groups for col in _REQUIRED_BY_GROUP.get(group, ())]
    df_valid = df.dropna(subset=required_cols) if required_cols else df

    rows: list[tuple[datetime, dict]] = []
    for ts, row in df_valid.iterrows():
        features: dict = {key: _safe_float(row.get(_OUTPUT_COLUMNS[key])) for key in output_keys}
        features["regime"] = row.get("regime", "sideways")
        rows.append((ts, features))
    return rows


def _safe_float(value) -> float | None:
    """Convierte a float; None si es NaN o no numérico."""
    try:
        v = float(value)
        return None if math.isnan(v) else round(v, 8)
    except (TypeError, ValueError):
        return None


def _detect_regime(df: pd.DataFrame, idx: int) -> str:
    """
    Régimen con lógica HH/HL sobre las 20 velas ANTERIORES (sin mirar la
    actual, para no usar información del futuro en el backtest):
    - trend_up:   los 2 últimos máximos y mínimos de swing suben
    - trend_down: los 2 últimos máximos y mínimos de swing bajan
    - sideways:   cualquier otro caso
    """
    try:
        if idx < 20:
            return "sideways"

        window = df.iloc[idx - 20: idx]
        highs = window["high"].values
        lows = window["low"].values

        # Swing highs y swing lows locales (ventana de 3)
        swing_highs = [
            highs[i] for i in range(1, len(highs) - 1)
            if highs[i] > highs[i - 1] and highs[i] > highs[i + 1]
        ]
        swing_lows = [
            lows[i] for i in range(1, len(lows) - 1)
            if lows[i] < lows[i - 1] and lows[i] < lows[i + 1]
        ]

        if len(swing_highs) >= 2 and len(swing_lows) >= 2:
            hh = swing_highs[-1] > swing_highs[-2]
            hl = swing_lows[-1] > swing_lows[-2]
            lh = swing_highs[-1] < swing_highs[-2]
            ll = swing_lows[-1] < swing_lows[-2]

            if hh and hl:
                return "trend_up"
            if lh and ll:
                return "trend_down"

        return "sideways"
    except Exception:
        return "sideways"
