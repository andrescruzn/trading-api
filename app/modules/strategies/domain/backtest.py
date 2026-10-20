# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/strategies/domain/backtest.py
#
# Motor de backtesting SIN IA: simula una estrategia vela a vela sobre
# historia con indicadores ya calculados. Mide si las REGLAS tienen
# ventaja (edge); no simula las decisiones del LLM.
#
# REGLAS DE LA SIMULACIÓN:
# - Señal al CIERRE de una vela: régimen requerido + todas las reglas
#   (strategies/domain/rule_evaluation.py, la misma de la IA) y ATR > 0.
# - Entrada en la APERTURA de la vela siguiente (sin mirar el futuro).
# - Solo largos (spot): una estrategia que pide trend_down no abre nada.
# - SL = entrada − sl_atr × ATR · TP = entrada + tp_atr × ATR (2:1 con
#   1,5 y 3). Tamaño: capital × risk_pct / (entrada − SL), sin pasar del
#   capital disponible (sin apalancamiento).
# - Salida: si la vela toca el SL sale en el SL (o en la apertura si abrió
#   por debajo: hueco de precio); si toca el TP sale en el TP. Si toca los
#   dos en la misma vela gana el SL (peor caso, igual que la app).
# - Comisión `fee_pct` por lado sobre el monto operado.
# - Una sola posición a la vez; al final, la abierta se cierra al último
#   cierre para no dejar resultado sin contar.
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from app.modules.strategies.domain.rule_evaluation import rules_pass

_ZERO = Decimal("0")


@dataclass(frozen=True)
class BacktestBar:
    ts: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    features: dict | None  # None si la vela no tiene indicadores completos


@dataclass(frozen=True)
class BacktestConfig:
    initial_capital: Decimal = Decimal("10000")
    risk_pct: Decimal = Decimal("0.01")
    sl_atr: Decimal = Decimal("1.5")
    tp_atr: Decimal = Decimal("3")
    fee_pct: Decimal = Decimal("0.001")


@dataclass
class BacktestTrade:
    entry_ts: datetime
    entry_price: Decimal
    qty: Decimal
    stop_loss: Decimal
    take_profit: Decimal
    exit_ts: datetime | None = None
    exit_price: Decimal | None = None
    exit_reason: str | None = None  # stop_loss | take_profit | end
    fees: Decimal = _ZERO

    @property
    def pnl(self) -> Decimal:
        """Resultado neto (después de comisiones)."""
        if self.exit_price is None:
            return _ZERO
        return (self.exit_price - self.entry_price) * self.qty - self.fees

    @property
    def return_pct(self) -> Decimal:
        cost = self.entry_price * self.qty
        return self.pnl / cost if cost > _ZERO else _ZERO


@dataclass
class BacktestResult:
    trades: list[BacktestTrade] = field(default_factory=list)
    final_capital: Decimal = _ZERO
    bars: int = 0
    signals: int = 0            # velas que cumplieron régimen + reglas
    skipped_in_position: int = 0
    buy_and_hold_pct: Decimal | None = None
    equity_curve: list[tuple[datetime, Decimal]] = field(default_factory=list)


def run_backtest(
    bars: list[BacktestBar],
    rules: list[dict],
    regime_required: str | None,
    config: BacktestConfig,
) -> BacktestResult:
    """Simula la estrategia sobre `bars` (de la más antigua a la más nueva)."""
    result = BacktestResult(final_capital=config.initial_capital, bars=len(bars))
    capital = config.initial_capital
    open_trade: BacktestTrade | None = None

    for i, bar in enumerate(bars):
        # 1) Gestionar la posición abierta con el rango de esta vela
        if open_trade is not None and bar.ts >= open_trade.entry_ts:
            exit_price, reason = _check_exit(open_trade, bar)
            if exit_price is not None:
                capital = _close(open_trade, bar.ts, exit_price, reason, capital, config, result)
                open_trade = None

        # 2) Señal al cierre → entrada en la apertura de la siguiente
        if not _signal(bar, rules, regime_required):
            continue
        result.signals += 1
        if open_trade is not None:
            result.skipped_in_position += 1
            continue
        if i + 1 >= len(bars):
            break
        open_trade = _open(bars[i + 1], Decimal(str(bar.features["atr_14"])), capital, config)

    # 3) Lo que quede abierto se cierra al último cierre
    if open_trade is not None and bars:
        last = bars[-1]
        capital = _close(open_trade, last.ts, last.close, "end", capital, config, result)

    result.final_capital = capital
    if bars and bars[0].open > _ZERO:
        result.buy_and_hold_pct = (bars[-1].close - bars[0].open) / bars[0].open
    return result


def _signal(bar: BacktestBar, rules: list[dict], regime_required: str | None) -> bool:
    features = bar.features
    if not features:
        return False
    regime = features.get("regime")
    # Spot: solo largos. Una estrategia de tendencia bajista nunca abre.
    if regime_required == "trend_down":
        return False
    if regime_required is not None and regime != regime_required:
        return False
    atr = features.get("atr_14")
    if atr is None or float(atr) <= 0:
        return False
    return rules_pass(rules, features)


def _open(
    bar: BacktestBar, atr: Decimal, capital: Decimal, config: BacktestConfig
) -> BacktestTrade | None:
    entry = bar.open
    stop = entry - config.sl_atr * atr
    if stop <= _ZERO or entry <= _ZERO:
        return None
    risk_per_unit = entry - stop
    qty = capital * config.risk_pct / risk_per_unit
    # Spot sin apalancamiento: no se compra más de lo que hay (con comisión)
    max_qty = capital / (entry * (Decimal("1") + config.fee_pct))
    qty = min(qty, max_qty)
    if qty <= _ZERO:
        return None
    return BacktestTrade(
        entry_ts=bar.ts,
        entry_price=entry,
        qty=qty,
        stop_loss=stop,
        take_profit=entry + config.tp_atr * atr,
        fees=entry * qty * config.fee_pct,
    )


def _check_exit(trade: BacktestTrade, bar: BacktestBar) -> tuple[Decimal | None, str | None]:
    # La vela de entrada cuenta entera (se entró en su apertura); en las
    # siguientes, un hueco de apertura más allá del nivel sale en la apertura.
    if bar.low <= trade.stop_loss:
        # Hueco: si abrió por debajo del SL, se sale en la apertura
        price = bar.open if bar.open < trade.stop_loss and bar.ts != trade.entry_ts else trade.stop_loss
        return price, "stop_loss"
    if bar.high >= trade.take_profit:
        price = bar.open if bar.open > trade.take_profit and bar.ts != trade.entry_ts else trade.take_profit
        return price, "take_profit"
    return None, None


def _close(
    trade: BacktestTrade,
    ts: datetime,
    price: Decimal,
    reason: str,
    capital: Decimal,
    config: BacktestConfig,
    result: BacktestResult,
) -> Decimal:
    trade.exit_ts = ts
    trade.exit_price = price
    trade.exit_reason = reason
    trade.fees += price * trade.qty * config.fee_pct
    result.trades.append(trade)
    capital += trade.pnl
    result.equity_curve.append((ts, capital))
    return capital
