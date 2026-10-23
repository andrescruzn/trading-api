# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/rest/performance/routes.py
#
# ENDPOINTS:
# - GET /performance?bot_id=        → rendimiento de un agente (propio)
# - GET /performance/strategies     → track record por estrategia
#                                     (cualquier usuario con sesión; anónimo)
#
# NOTAS:
# - Los porcentajes van como fracción (0.05 = 5 %) y los montos en la
#   moneda de cotización del símbolo; como el resto de M8, en float.
# ======================================================================

from __future__ import annotations

from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.http import build_error_response, build_list_response, build_success_response
from app.common.security.jwt import read_scope, token_required_actual
from app.common.utils import to_iso_utc
from app.extensions.db import get_db
from app.modules.orders.providers import OrderServiceFactory, get_order_factory
from app.modules.orders.services.performance import BotPerformance, StrategyTrackRecord

from .error_messages import PERFORMANCE_ERROR_MESSAGES

router = APIRouter(prefix="/performance", tags=["Performance"])


def get_factory(db: Session = Depends(get_db)) -> OrderServiceFactory:
    return get_order_factory(db)


def _num(value: Decimal | None) -> float | None:
    return float(value) if value is not None else None


def _iso(value) -> str | None:
    return to_iso_utc(value)


def _bot_performance_to_dict(data: BotPerformance) -> dict[str, Any]:
    p = data.performance
    return {
        "trades":            p.trades,
        "wins":              p.wins,
        "losses":            p.losses,
        "win_rate":          _num(p.win_rate),
        "realized_pnl":      _num(p.realized_pnl),
        "gross_profit":      _num(p.gross_profit),
        "gross_loss":        _num(p.gross_loss),
        "profit_factor":     _num(p.profit_factor),
        "avg_win":           _num(p.avg_win),
        "avg_loss":          _num(p.avg_loss),
        "payoff_ratio":      _num(p.payoff_ratio),
        "avg_return_pct":    _num(p.avg_return_pct),
        "max_drawdown":      _num(p.max_drawdown),
        "total_fees":        _num(p.total_fees),
        "open_qty":          _num(p.open_qty),
        "open_avg_price":    _num(p.open_avg_price) if p.open_qty else None,
        "open_realized_pnl": _num(p.open_realized_pnl),
        "last_price":        _num(data.last_price),
        "unrealized_pnl":    _num(data.unrealized_pnl),
        "equity_curve":      [{"ts": _iso(ts), "pnl": _num(v)} for ts, v in p.equity_curve],
        "closed_trades": [
            {
                "opened_at":  _iso(t.opened_at),
                "closed_at":  _iso(t.closed_at),
                "qty":        _num(t.qty),
                "cost":       _num(t.cost),
                "pnl":        _num(t.pnl),
                "return_pct": _num(t.return_pct),
            }
            for t in reversed(p.closed_trades)  # la más reciente primero
        ],
    }


def _track_record_to_dict(r: StrategyTrackRecord) -> dict[str, Any]:
    return {
        "strategy_id":      r.strategy_id,
        "strategy_name":    r.strategy_name,
        "mode":             r.mode,
        "agents":           r.agents,
        "trades":           r.trades,
        "wins":             r.wins,
        "win_rate":         _num(r.win_rate),
        "avg_return_pct":   _num(r.avg_return_pct),
        "total_return_pct": _num(r.total_return_pct),
        "profit_factor":    _num(r.profit_factor),
        "max_drawdown_pct": _num(r.max_drawdown_pct),
        "best_trade_pct":   _num(r.best_trade_pct),
        "worst_trade_pct":  _num(r.worst_trade_pct),
        "curve":            [{"ts": _iso(ts), "return_pct": _num(v)} for ts, v in r.curve],
    }


# ======================================================================
# GET /performance?bot_id=
# ======================================================================

@router.get("", status_code=200)
def get_bot_performance(
    bot_id: int = Query(..., gt=0),
    identity: dict = Depends(token_required_actual),
    factory: OrderServiceFactory = Depends(get_factory),
):
    """Operaciones cerradas y métricas de un agente."""
    result = factory.bot_performance().get(bot_id=bot_id, owner_id=read_scope(identity))
    if not result.success:
        return build_error_response(result, PERFORMANCE_ERROR_MESSAGES)
    return build_success_response(data=_bot_performance_to_dict(result.data), msg="OK")


# ======================================================================
# GET /performance/strategies
# ======================================================================

@router.get("/strategies", status_code=200)
def list_strategy_track_record(
    mode: str | None = Query(default=None, pattern="^(paper|live)$"),
    _identity: dict = Depends(token_required_actual),
    factory: OrderServiceFactory = Depends(get_factory),
):
    """Track record anónimo por estrategia y modo."""
    result = factory.strategy_track_record().list(mode=mode)
    return build_list_response(items=[_track_record_to_dict(r) for r in (result.data or [])])
