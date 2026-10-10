# -*- coding: utf-8 -*-

# ======================================================================
# database/seeds/bots.py
#
# PROPÓSITO:
# - Agentes (bots) de ejemplo del Módulo 7 para el usuario demo, para no
#   arrancar con la pantalla de agentes vacía: uno sobre oro (perpetuo
#   TradFi) y otro sobre BTC.
#
# NOTAS:
# - Requiere los seeds `market_data`, `strategies`, `feature_sets` y
#   `accounts`. Si falta alguna referencia, ese agente se omite.
# - Se crean en `paper` y `stopped`: nadie opera hasta que el usuario
#   los inicia desde la app.
# - Clave natural: (account_id, name).
# - Mismas reglas que CreateBotService: modo igual al de la cuenta,
#   risk_pct <= 0.01 (regla del 1 %) y conjunto de indicadores compatible
#   con las reglas de la estrategia (por eso ambos usan "Tendencia").
# ======================================================================

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.accounts.infrastructure.account_model import AccountModel
from app.modules.bots.infrastructure.bot_model import BotModel
from app.modules.features.infrastructure.feature_set_model import FeatureSetModel
from app.modules.market.infrastructure.exchange_model import ExchangeModel
from app.modules.market.infrastructure.symbol_model import SymbolModel
from app.modules.market.infrastructure.timeframe_model import TimeframeModel
from app.modules.strategies.infrastructure.strategy_model import StrategyModel
from app.modules.users.infrastructure.user_model import UserModel
from database.seeds._helpers import SeedStats, get_or_create

DEMO_USER_EMAIL = "andrescruznovoa@gmail.com"

BOTS: list[dict[str, Any]] = [
    {
        "name": "Oro — tendencia 4h",
        "account": "Binance Paper — Demo",
        "exchange": "Binance",
        "symbol": "XAU/USDT:USDT",
        "strategy": ("Tendencia Metales", "1.0.0"),
        "timeframe": "4h",
        "feature_set": ("Tendencia", "1.0.0"),
        "risk_pct": 0.01,
    },
    {
        "name": "BTC — tendencia 1h",
        "account": "Binance Paper — Demo",
        "exchange": "Binance",
        "symbol": "BTC/USDT",
        "strategy": ("EMA Trend Follower", "1.0.0"),
        "timeframe": "1h",
        "feature_set": ("Tendencia", "1.0.0"),
        "risk_pct": 0.01,
    },
]


def run(session: Session) -> SeedStats:
    stats = SeedStats()

    user = session.execute(
        select(UserModel).filter_by(email=DEMO_USER_EMAIL)
    ).scalar_one_or_none()
    if user is None:
        stats.notes.append(f"omitido: no existe el usuario {DEMO_USER_EMAIL}")
        return stats

    for spec in BOTS:
        refs = _resolve_refs(session, user.id, spec)
        if refs is None:
            stats.notes.append(f"omitido '{spec['name']}': falta alguna referencia")
            continue

        get_or_create(
            session,
            BotModel,
            lookup={"account_id": refs["account_id"], "name": spec["name"]},
            values={
                "strategy_id": refs["strategy_id"],
                "symbol_id": refs["symbol_id"],
                "timeframe_id": refs["timeframe_id"],
                "feature_set_id": refs["feature_set_id"],
                "mode": "paper",
                "status": "stopped",
                "risk_params": {"risk_pct": spec["risk_pct"]},
            },
            stats=stats,
        )

    return stats


def _resolve_refs(session: Session, user_id: int, spec: dict[str, Any]) -> dict[str, int] | None:
    """IDs de cuenta, símbolo, estrategia, timeframe y conjunto; None si falta uno."""
    strategy_name, strategy_version = spec["strategy"]
    set_name, set_version = spec["feature_set"]

    account = session.execute(
        select(AccountModel).filter_by(user_id=user_id, name=spec["account"], mode="paper")
    ).scalar_one_or_none()
    symbol = session.execute(
        select(SymbolModel)
        .join(ExchangeModel, ExchangeModel.id == SymbolModel.exchange_id)
        .where(ExchangeModel.name == spec["exchange"], SymbolModel.symbol == spec["symbol"])
    ).scalar_one_or_none()
    strategy = session.execute(
        select(StrategyModel).filter_by(name=strategy_name, version=strategy_version)
    ).scalar_one_or_none()
    timeframe = session.execute(
        select(TimeframeModel).filter_by(code=spec["timeframe"])
    ).scalar_one_or_none()
    feature_set = session.execute(
        select(FeatureSetModel).filter_by(name=set_name, version=set_version)
    ).scalar_one_or_none()

    if None in (account, symbol, strategy, timeframe, feature_set) or not symbol.is_active:
        return None
    return {
        "account_id": account.id,
        "symbol_id": symbol.id,
        "strategy_id": strategy.id,
        "timeframe_id": timeframe.id,
        "feature_set_id": feature_set.id,
    }
