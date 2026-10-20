# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/strategies/rest/backtests/routes.py
#
# ENDPOINTS:
# - POST /backtests → probar una estrategia en el pasado (sin IA)
#
# NOTAS:
# - No guarda nada: trae la historia del exchange, simula y responde.
# - Rate limit por usuario (cada backtest pide miles de velas al exchange).
# - Porcentajes como fracción (0.05 = 5 %), montos en la cotización.
# ======================================================================

from __future__ import annotations

from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.http import build_error_response, build_success_response
from app.common.security.jwt import token_required_actual
from app.common.security.rate_limiter import backtest_rate_limiter, check_user_rate_limit
from app.extensions.db import get_db
from app.modules.strategies.providers.strategy_provider import StrategyServiceFactory
from app.modules.strategies.services.backtests import BacktestReport

from .error_messages import BACKTEST_ERROR_MESSAGES
from .schemas import RunBacktestRequest

router = APIRouter(prefix="/backtests", tags=["Backtests"])


def get_factory(db: Session = Depends(get_db)) -> StrategyServiceFactory:
    return StrategyServiceFactory(session=db)


def _num(value: Decimal | None) -> float | None:
    return float(value) if value is not None else None


def _iso(value) -> str | None:
    return value.isoformat() if value else None


def _report_to_dict(r: BacktestReport) -> dict[str, Any]:
    p = r.performance
    res = r.result
    initial = r.config.initial_capital
    return {
        "strategy_name":      r.strategy_name,
        "regime_required":    r.regime_required,
        "from_ts":            _iso(r.first_ts),
        "to_ts":              _iso(r.last_ts),
        "bars":               res.bars,
        "signals":            res.signals,
        "skipped_in_position": res.skipped_in_position,
        "initial_capital":    _num(initial),
        "final_capital":      _num(res.final_capital),
        "return_pct":         _num((res.final_capital - initial) / initial) if initial else None,
        "buy_and_hold_pct":   _num(res.buy_and_hold_pct),
        "risk_pct":           _num(r.config.risk_pct),
        "fee_pct":            _num(r.config.fee_pct),
        "sl_atr":             _num(r.config.sl_atr),
        "tp_atr":             _num(r.config.tp_atr),
        "trades":             p.trades,
        "wins":               p.wins,
        "losses":             p.losses,
        "win_rate":           _num(p.win_rate),
        "profit_factor":      _num(p.profit_factor),
        "payoff_ratio":       _num(p.payoff_ratio),
        "avg_return_pct":     _num(p.avg_return_pct),
        "max_drawdown":       _num(p.max_drawdown),
        "total_fees":         _num(p.total_fees),
        "equity_curve":       [{"ts": _iso(ts), "capital": _num(v)} for ts, v in res.equity_curve],
        "closed_trades": [
            {
                "entry_ts":    _iso(t.entry_ts),
                "exit_ts":     _iso(t.exit_ts),
                "entry_price": _num(t.entry_price),
                "exit_price":  _num(t.exit_price),
                "qty":         _num(t.qty),
                "stop_loss":   _num(t.stop_loss),
                "take_profit": _num(t.take_profit),
                "exit_reason": t.exit_reason,
                "pnl":         _num(t.pnl),
                "return_pct":  _num(t.return_pct),
            }
            for t in reversed(res.trades)  # la más reciente primero
        ],
    }


@router.post("", status_code=200)
def run_backtest(
    payload: RunBacktestRequest,
    identity: dict = Depends(token_required_actual),
    factory: StrategyServiceFactory = Depends(get_factory),
):
    """Simula la estrategia sobre las últimas `bars` velas del exchange."""
    check_user_rate_limit(backtest_rate_limiter, identity["user_id"])

    result = factory.run_backtest().run(
        strategy_id=payload.strategy_id,
        symbol_id=payload.symbol_id,
        timeframe_id=payload.timeframe_id,
        bars=payload.bars,
        initial_capital=payload.initial_capital,
        fee_pct=payload.fee_pct,
    )
    if not result.success:
        return build_error_response(result, BACKTEST_ERROR_MESSAGES)
    return build_success_response(data=_report_to_dict(result.data), msg="Backtest listo.")
