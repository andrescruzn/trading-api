# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/market/services/explorer/trend_metrics.py
#
# PROPÓSITO:
# - Medir qué tan "en tendencia" está un mercado con sus velas diarias,
#   para ordenar símbolos en el explorador y elegir dónde crear agentes.
#
# MÉTRICAS (velas 1d):
# - ret_30d / ret_90d : rendimiento del cierre en 30 y 90 días (fracción).
# - adx_14            : fuerza de tendencia (Wilder). >25 suele ser tendencia.
# - efficiency_30     : eficiencia de Kaufman, |cambio neto| / Σ|cambios|
#                       en 30 velas. 1 = línea recta, 0 = ruido puro.
# - atr_pct_14        : ATR / cierre: volatilidad diaria típica.
# - direction         : up | down según cierre, EMA50 y EMA200; sideways si
#                       no cuadran o si el ADX es < 20 (sin fuerza).
# - strength          : 0–100 = min(ADX/50, 1) × eficiencia. Exige a la vez
#                       fuerza (ADX) y limpieza del movimiento (eficiencia).
# - score             : strength con signo según la dirección (sideways = 0),
#                       para ordenar: alcistas fuertes arriba, bajistas abajo.
#
# NOTAS:
# - Función pura (pandas + pandas-ta): sin BD ni ccxt.
# - Con menos de 200 velas no hay EMA200: la dirección usa solo EMA50.
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pandas as pd
import pandas_ta  # noqa: F401  (registra el accessor df.ta)

from app.modules.market.domain.candle_entity import Candle

# Velas diarias mínimas para medir (ADX14 + eficiencia 30 + EMA50 estables)
MIN_CANDLES = 60

_ER_WINDOW = 30
_ADX_FULL = 50.0
# Por debajo de este ADX no hay tendencia, aunque las EMAs estén alineadas
_ADX_TREND_MIN = 20.0


@dataclass(frozen=True)
class TrendMetrics:
    candles: int
    last_close: float
    last_ts: datetime
    ret_30d: float | None
    ret_90d: float | None
    adx_14: float | None
    efficiency_30: float | None
    atr_pct_14: float | None
    direction: str
    strength: float
    score: float


def compute_trend_metrics(candles: list[Candle]) -> TrendMetrics | None:
    """Métricas de tendencia; None si no hay velas suficientes."""
    if len(candles) < MIN_CANDLES:
        return None

    ordered = sorted(candles, key=lambda c: c.ts)
    df = pd.DataFrame({
        "high": [float(c.high) for c in ordered],
        "low": [float(c.low) for c in ordered],
        "close": [float(c.close) for c in ordered],
    })
    close = df["close"]
    last = float(close.iloc[-1])

    adx = _last(df.ta.adx(length=14), "ADX_14")
    atr = _last_series(df.ta.atr(length=14))
    ema50 = _last_series(df.ta.ema(length=50))
    ema200 = _last_series(df.ta.ema(length=200)) if len(df) >= 200 else None

    efficiency = _efficiency_ratio(close, _ER_WINDOW)
    direction = _direction(last, ema50, ema200)
    if adx is None or adx < _ADX_TREND_MIN:
        direction = "sideways"

    strength = 0.0
    if adx is not None and efficiency is not None:
        strength = min(adx / _ADX_FULL, 1.0) * efficiency * 100
    sign = {"up": 1, "down": -1}.get(direction, 0)

    return TrendMetrics(
        candles=len(df),
        last_close=last,
        last_ts=ordered[-1].ts,
        ret_30d=_return(close, 30),
        ret_90d=_return(close, 90),
        adx_14=adx,
        efficiency_30=efficiency,
        atr_pct_14=(atr / last) if atr is not None and last > 0 else None,
        direction=direction,
        strength=round(strength, 2),
        score=round(sign * strength, 2),
    )


# ======================================================================
# Helpers
# ======================================================================

def _direction(close: float, ema50: float | None, ema200: float | None) -> str:
    if ema50 is None:
        return "sideways"
    if close > ema50 and (ema200 is None or ema50 > ema200):
        return "up"
    if close < ema50 and (ema200 is None or ema50 < ema200):
        return "down"
    return "sideways"


def _efficiency_ratio(close: pd.Series, window: int) -> float | None:
    if len(close) <= window:
        return None
    tail = close.iloc[-(window + 1):]
    path = tail.diff().abs().sum()
    if path <= 0:
        return None
    return float(abs(tail.iloc[-1] - tail.iloc[0]) / path)


def _return(close: pd.Series, days: int) -> float | None:
    if len(close) <= days:
        return None
    base = float(close.iloc[-(days + 1)])
    return (float(close.iloc[-1]) / base - 1) if base > 0 else None


def _last(df: pd.DataFrame | None, column: str) -> float | None:
    if df is None or column not in df:
        return None
    return _last_series(df[column])


def _last_series(series: pd.Series | None) -> float | None:
    if series is None or series.empty:
        return None
    value = series.iloc[-1]
    return None if pd.isna(value) else float(value)
