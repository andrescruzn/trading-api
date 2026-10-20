# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/strategies/services/backtests/run_backtest_service.py
#
# CASO DE USO:
# - Probar una estrategia en el pasado (sin IA) sobre un símbolo y
#   timeframe: trae la historia del exchange sin guardarla, calcula los
#   indicadores en memoria y simula (domain/backtest.py).
#
# REGLAS:
# - Riesgo por operación: el `risk_pct` de la estrategia, nunca más del
#   1 % (regla del 1 %).
# - Se piden velas extra de calentamiento: la EMA(200) necesita historia
#   antes de la primera vela simulada.
# - Las métricas salen de la misma función que el rendimiento real de los
#   agentes (orders/domain/performance.py), para poder compararlas.
# - No se guarda nada: el resultado se devuelve y se descarta.
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.common.contracts import ServiceResult
from app.modules.features.domain.indicator_catalog import INDICATOR_GROUPS
from app.modules.features.domain.indicator_engine import MIN_CANDLES, compute_feature_rows
from app.modules.market.services.candles import FetchCandleHistoryService
from app.modules.orders.domain.performance import Performance, TradeFill, compute_performance
from app.modules.strategies.domain.backtest import (
    BacktestBar,
    BacktestConfig,
    BacktestResult,
    run_backtest,
)
from app.modules.strategies.domain.strategy_repository import StrategyRepository

# Velas extra para que EMA(200) y el régimen estén listos al empezar
_WARMUP = MIN_CANDLES + 30
_MAX_RISK = Decimal("0.01")
# En la compra la comisión ya va sumada en la venta del trade (trade.fees)
_ZERO_FEE = Decimal("0")


@dataclass
class BacktestReport:
    strategy_name: str
    regime_required: str | None
    config: BacktestConfig
    result: BacktestResult
    performance: Performance
    first_ts: object
    last_ts: object


class RunBacktestService:
    """Simula una estrategia sobre historia reciente del exchange."""

    def __init__(
        self,
        strategy_repo: StrategyRepository,
        fetch_history: FetchCandleHistoryService,
    ):
        self._strategy_repo = strategy_repo
        self._fetch_history = fetch_history

    def run(
        self,
        strategy_id: int,
        symbol_id: int,
        timeframe_id: int,
        bars: int,
        initial_capital: Decimal = Decimal("10000"),
        fee_pct: Decimal = Decimal("0.001"),
    ) -> ServiceResult[BacktestReport]:
        strategy = self._strategy_repo.get_by_id(strategy_id)
        if strategy is None:
            return ServiceResult.fail(code="STRATEGY_NOT_FOUND", http_status=404)
        if not strategy.rules:
            return ServiceResult.fail(code="BACKTEST_STRATEGY_WITHOUT_RULES", http_status=422)

        history = self._fetch_history.fetch(symbol_id, timeframe_id, bars + _WARMUP)
        if not history.success:
            return history  # type: ignore[return-value]
        candles = history.data
        if len(candles) < _WARMUP + 50:
            return ServiceResult.fail(
                code="BACKTEST_NOT_ENOUGH_HISTORY",
                http_status=422,
                meta={"available": len(candles), "required": _WARMUP + 50},
            )

        features_by_ts = dict(compute_feature_rows(candles, list(INDICATOR_GROUPS)))
        simulated = candles[-bars:]
        series = [
            BacktestBar(
                ts=c.ts,
                open=c.open,
                high=c.high,
                low=c.low,
                close=c.close,
                features=features_by_ts.get(c.ts),
            )
            for c in simulated
        ]

        risk_pct = min(Decimal(str(strategy.parameters.get("risk_pct", "0.01"))), _MAX_RISK)
        config = BacktestConfig(
            initial_capital=initial_capital, risk_pct=risk_pct, fee_pct=fee_pct
        )
        result = run_backtest(series, strategy.rules, strategy.regime_required, config)

        fills: list[TradeFill] = []
        for trade in result.trades:
            fills.append(TradeFill("buy", trade.qty, trade.entry_price, _ZERO_FEE, trade.entry_ts))
            fills.append(TradeFill("sell", trade.qty, trade.exit_price, trade.fees, trade.exit_ts))

        return ServiceResult.ok(
            data=BacktestReport(
                strategy_name=f"{strategy.name} v{strategy.version}",
                regime_required=strategy.regime_required,
                config=config,
                result=result,
                performance=compute_performance(fills),
                first_ts=series[0].ts if series else None,
                last_ts=series[-1].ts if series else None,
            )
        )

