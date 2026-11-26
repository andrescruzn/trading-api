# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/domain/performance.py
#
# PROPÓSITO:
# - Métricas de rendimiento de un agente a partir de sus ejecuciones
#   (fills), sin BD: win rate, P&L, profit factor, R/R real y drawdown.
#
# CÓMO SE CUENTA UNA OPERACIÓN:
# - Se reproducen los fills en orden cronológico con la misma regla de la
#   posición (precio promedio ponderado al comprar, P&L al vender).
# - Una operación abre cuando la posición pasa de 0 a > 0 y cierra cuando
#   vuelve a 0. Compras intermedias suman a la misma operación.
# - El P&L es por precio (como `Position`): las comisiones se informan
#   aparte porque pueden venir en el activo base o en la cotización.
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

_ZERO = Decimal("0")


@dataclass(frozen=True)
class TradeFill:
    """Una ejecución con el lado de su orden."""
    side: str
    qty: Decimal
    price: Decimal
    fee: Decimal
    ts: datetime | None


@dataclass
class ClosedTrade:
    """Operación completa: de posición en 0 a posición en 0."""
    opened_at: datetime | None
    closed_at: datetime | None
    qty: Decimal          # cantidad máxima que llegó a tener
    cost: Decimal         # total invertido en las compras
    pnl: Decimal

    @property
    def return_pct(self) -> Decimal | None:
        """Retorno sobre lo invertido (0.05 = +5 %)."""
        return self.pnl / self.cost if self.cost > _ZERO else None


@dataclass
class Performance:
    closed_trades: list[ClosedTrade] = field(default_factory=list)
    realized_pnl: Decimal = _ZERO
    gross_profit: Decimal = _ZERO
    gross_loss: Decimal = _ZERO   # positivo: suma de las pérdidas
    total_fees: Decimal = _ZERO
    max_drawdown: Decimal = _ZERO  # positivo: mayor caída del P&L acumulado
    open_qty: Decimal = _ZERO
    open_avg_price: Decimal = _ZERO
    # Ventas parciales de la operación aún abierta (no cuentan como cerrada)
    open_realized_pnl: Decimal = _ZERO
    equity_curve: list[tuple[datetime | None, Decimal]] = field(default_factory=list)

    @property
    def trades(self) -> int:
        return len(self.closed_trades)

    @property
    def wins(self) -> int:
        return sum(1 for t in self.closed_trades if t.pnl > _ZERO)

    @property
    def losses(self) -> int:
        return sum(1 for t in self.closed_trades if t.pnl < _ZERO)

    @property
    def win_rate(self) -> Decimal | None:
        """Operaciones ganadoras / cerradas (0.6 = 60 %)."""
        return Decimal(self.wins) / Decimal(self.trades) if self.trades else None

    @property
    def profit_factor(self) -> Decimal | None:
        """Ganancias / pérdidas. > 1 = la estrategia gana más de lo que pierde."""
        return self.gross_profit / self.gross_loss if self.gross_loss > _ZERO else None

    @property
    def avg_win(self) -> Decimal | None:
        return self.gross_profit / Decimal(self.wins) if self.wins else None

    @property
    def avg_loss(self) -> Decimal | None:
        """Positivo: pérdida media."""
        return self.gross_loss / Decimal(self.losses) if self.losses else None

    @property
    def payoff_ratio(self) -> Decimal | None:
        """R/R real: ganancia media / pérdida media (el plan pide ≥ 2)."""
        if self.avg_win is None or self.avg_loss is None:
            return None
        return self.avg_win / self.avg_loss

    @property
    def avg_return_pct(self) -> Decimal | None:
        returns = [r for r in (t.return_pct for t in self.closed_trades) if r is not None]
        return sum(returns, _ZERO) / Decimal(len(returns)) if returns else None


def compute_performance(fills: list[TradeFill]) -> Performance:
    """Métricas de una lista de fills (en cualquier orden: se ordenan por fecha)."""
    perf = Performance()
    ordered = sorted(fills, key=lambda f: (f.ts is None, f.ts))

    qty = _ZERO
    avg = _ZERO
    trade: ClosedTrade | None = None
    cumulative = _ZERO
    peak = _ZERO

    for fill in ordered:
        perf.total_fees += fill.fee or _ZERO

        if fill.side == "buy":
            if trade is None:
                trade = ClosedTrade(fill.ts, None, _ZERO, _ZERO, _ZERO)
            avg = (qty * avg + fill.qty * fill.price) / (qty + fill.qty)
            qty += fill.qty
            trade.qty = max(trade.qty, qty)
            trade.cost += fill.qty * fill.price
            continue

        # Venta: en spot solo cierra lo que había
        sold = min(fill.qty, qty)
        if trade is None or sold <= _ZERO:
            continue
        trade.pnl += (fill.price - avg) * sold
        qty -= sold
        if qty > _ZERO:
            continue

        # Posición en 0: la operación terminó
        trade.closed_at = fill.ts
        perf.closed_trades.append(trade)
        perf.realized_pnl += trade.pnl
        if trade.pnl > _ZERO:
            perf.gross_profit += trade.pnl
        elif trade.pnl < _ZERO:
            perf.gross_loss += -trade.pnl

        cumulative += trade.pnl
        peak = max(peak, cumulative)
        perf.max_drawdown = max(perf.max_drawdown, peak - cumulative)
        perf.equity_curve.append((fill.ts, cumulative))

        trade, qty, avg = None, _ZERO, _ZERO

    perf.open_qty = qty
    perf.open_avg_price = avg
    perf.open_realized_pnl = trade.pnl if trade is not None else _ZERO
    return perf
