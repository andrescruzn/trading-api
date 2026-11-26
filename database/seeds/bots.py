# -*- coding: utf-8 -*-

# ======================================================================
# database/seeds/bots.py
#
# PROPÓSITO:
# - Agentes demo (dinero simulado) de ejemplo del Módulo 7 para el super
#   admin, para no arrancar con "Agentes demo" vacío: uno sobre oro
#   (perpetuo TradFi) y otro sobre BTC.
#
# NOTAS:
# - Requiere los seeds `market_data`, `strategies` y `feature_sets`. Si
#   falta alguna referencia, ese agente se omite.
# - Se crean en `paper` (demo) y `stopped`: nadie opera hasta que el
#   usuario los inicia desde la app.
# - Igual que CreateBotService: cada agente demo tiene su propia cuenta de
#   práctica interna ("Demo · <nombre>") con el monto como balance inicial
#   y en `meta["demo_capital"]`.
# - Clave natural: cuenta = (user_id, name); agente = (account_id, name).
# - risk_pct <= 0.01 (regla del 1 %) y conjunto de indicadores compatible
#   con las reglas de la estrategia (por eso ambos usan "Tendencia").
# ======================================================================

from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.accounts.infrastructure.account_balance_model import AccountBalanceModel
from app.modules.accounts.infrastructure.account_model import AccountModel
from app.modules.bots.services.bots.demo_capital import DEMO_CAPITAL_META_KEY
from app.modules.bots.infrastructure.bot_model import BotModel
from app.modules.features.infrastructure.feature_set_model import FeatureSetModel
from app.modules.market.infrastructure.exchange_model import ExchangeModel
from app.modules.market.infrastructure.symbol_model import SymbolModel
from app.modules.market.infrastructure.timeframe_model import TimeframeModel
from app.modules.strategies.infrastructure.strategy_model import StrategyModel
from app.modules.users.infrastructure.user_model import UserModel
from database.seeds._helpers import SeedStats, get_or_create

DEMO_USER_EMAIL = "andrescruznovoa@gmail.com"
DEMO_CAPITAL = Decimal("10000")

BOTS: list[dict[str, Any]] = [
    {
        "name": "Oro — tendencia 4h",
        "exchange": "Binance",
        "symbol": "XAU/USDT:USDT",
        "strategy": ("Tendencia Metales", "1.0.0"),
        "timeframe": "4h",
        "feature_set": ("Tendencia", "1.0.0"),
        "risk_pct": 0.01,
    },
    {
        "name": "BTC — tendencia 1h",
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
        refs = _resolve_refs(session, spec)
        if refs is None:
            stats.notes.append(f"omitido '{spec['name']}': falta alguna referencia")
            continue

        account_id = _demo_account(session, user.id, spec["name"], refs["quote_asset"], stats)
        get_or_create(
            session,
            BotModel,
            lookup={"account_id": account_id, "name": spec["name"]},
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


def _demo_account(
    session: Session, user_id: int, bot_name: str, quote_asset: str, stats: SeedStats
) -> int:
    """Cuenta de práctica del agente demo con su monto inicial (crea la que falte)."""
    account = get_or_create(
        session,
        AccountModel,
        lookup={"user_id": user_id, "name": f"Demo · {bot_name}"},
        values={
            "mode": "paper",
            "base_currency": quote_asset,
            "status": "active",
            "credentials_ref": None,
            "meta": {DEMO_CAPITAL_META_KEY: str(DEMO_CAPITAL)},
        },
        stats=stats,
    )
    has_balance = session.execute(
        select(AccountBalanceModel.id).filter_by(account_id=account.id).limit(1)
    ).first() is not None
    if not has_balance:
        session.add(
            AccountBalanceModel(
                account_id=account.id, asset=quote_asset, free=DEMO_CAPITAL, locked=Decimal("0")
            )
        )
        session.flush()
    stats.track(AccountBalanceModel.__tablename__, created=not has_balance)
    return account.id


def _resolve_refs(session: Session, spec: dict[str, Any]) -> dict[str, Any] | None:
    """IDs de símbolo, estrategia, timeframe y conjunto; None si falta uno."""
    strategy_name, strategy_version = spec["strategy"]
    set_name, set_version = spec["feature_set"]

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

    if None in (symbol, strategy, timeframe, feature_set) or not symbol.is_active:
        return None
    return {
        "quote_asset": (symbol.quote_asset or "USDT").upper(),
        "symbol_id": symbol.id,
        "strategy_id": strategy.id,
        "timeframe_id": timeframe.id,
        "feature_set_id": feature_set.id,
    }
