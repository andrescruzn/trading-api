# -*- coding: utf-8 -*-

# ======================================================================
# database/seeds/strategies.py
#
# PROPÓSITO:
# - 6 estrategias de ejemplo del Módulo 5 para desarrollo y pruebas.
#
# NOTAS:
# - Clave natural: (name, version), igual que uq_strategies_name_version.
# - `regime_required` declara en qué régimen opera cada estrategia
#   (regla de negocio del filtro de régimen); None = sin restricción.
# ======================================================================

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.modules.strategies.infrastructure.strategy_model import StrategyModel
from database.seeds._helpers import SeedStats, get_or_create


def _rule(indicator: str, operator: str, value: Any) -> dict[str, Any]:
    return {"indicator": indicator, "operator": operator, "value": value}


STRATEGIES: list[dict[str, Any]] = [
    # ─── Trend Following ──────────────────────────────────────────────
    {
        "name": "EMA Trend Follower",
        "version": "1.0.0",
        "description": "Sigue tendencias alcistas usando cruce de EMAs y confirmación de régimen.",
        "parameters": {
            "strategy_type": "trend_following",
            "regime_required": "trend_up",
            "timeframe_code": "1h",
            "risk_pct": 0.01,
            "rules": [
                _rule("ema_20", "gt", "ema_50"),
                _rule("ema_50", "gt", "ema_200"),
                _rule("rsi_14", "gt", 50),
                _rule("macd", "gt", 0),
            ],
        },
    },
    {
        "name": "EMA Trend Follower",
        "version": "2.0.0",
        "description": "Versión mejorada: añade filtro ATR para evitar rangos de baja volatilidad.",
        "parameters": {
            "strategy_type": "trend_following",
            "regime_required": "trend_up",
            "timeframe_code": "4h",
            "risk_pct": 0.01,
            "rules": [
                _rule("ema_20", "gt", "ema_50"),
                _rule("ema_50", "gt", "ema_200"),
                _rule("rsi_14", "gt", 55),
                _rule("atr_14", "gt", 0.005),
                _rule("vol_rel", "gt", 1.2),
            ],
        },
    },
    {
        "name": "Bearish EMA Follower",
        "version": "1.0.0",
        "description": "Estrategia bajista: opera en tendencias descendentes con confirmación de EMAs.",
        "parameters": {
            "strategy_type": "trend_following",
            "regime_required": "trend_down",
            "timeframe_code": "1h",
            "risk_pct": 0.01,
            "rules": [
                _rule("ema_20", "lt", "ema_50"),
                _rule("ema_50", "lt", "ema_200"),
                _rule("rsi_14", "lt", 45),
                _rule("macd", "lt", 0),
            ],
        },
    },
    # ─── Mean Reversion ───────────────────────────────────────────────
    {
        "name": "RSI Mean Reversion",
        "version": "1.0.0",
        "description": "Compra cuando el precio está sobrevendido en mercados laterales (RSI < 30).",
        "parameters": {
            "strategy_type": "mean_reversion",
            "regime_required": "sideways",
            "timeframe_code": "15m",
            "risk_pct": 0.005,
            "rules": [
                _rule("rsi_14", "lt", 30),
                _rule("bb_lower", "gt", 0),
                _rule("vol_rel", "lt", 1.5),
            ],
        },
    },
    {
        "name": "Bollinger Band Reversion",
        "version": "1.0.0",
        "description": "Opera rebotes en las bandas de Bollinger durante mercados en rango lateral.",
        "parameters": {
            "strategy_type": "mean_reversion",
            "regime_required": "sideways",
            "timeframe_code": "1h",
            "risk_pct": 0.008,
            "rules": [
                _rule("rsi_14", "lt", 35),
                _rule("rsi_14", "gt", 20),
                _rule("macd", "gt", -0.001),
                _rule("vol_rel", "lt", 2.0),
            ],
        },
    },
    # ─── Sin restricción de régimen ───────────────────────────────────
    {
        "name": "MACD Crossover",
        "version": "1.0.0",
        "description": "Estrategia universal basada en cruce del MACD. Sin restricción de régimen.",
        "parameters": {
            "strategy_type": "trend_following",
            "regime_required": None,
            "timeframe_code": "4h",
            "risk_pct": 0.01,
            "rules": [
                _rule("macd", "gt", 0),
                _rule("macd_hist", "gt", 0),
                _rule("rsi_14", "gt", 45),
                _rule("rsi_14", "lt", 70),
            ],
        },
    },
]


def run(session: Session) -> SeedStats:
    stats = SeedStats()

    for strategy in STRATEGIES:
        get_or_create(
            session,
            StrategyModel,
            lookup={"name": strategy["name"], "version": strategy["version"]},
            values={
                "description": strategy["description"],
                "parameters": strategy["parameters"],
            },
            stats=stats,
        )

    return stats
