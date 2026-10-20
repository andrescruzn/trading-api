# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/domain/rule_conditions.py
#
# PROPÓSITO:
# - Condiciones de las reglas que se revisan en cada ciclo del scheduler
#   (price, pnl, drawdown) y el antispam (cooldown). Puro: sin BD.
#
# P&L Y DRAWDOWN DE UN AGENTE (sobre domain/performance.py de M8):
# - P&L total = P&L realizado de las operaciones cerradas
#               + ventas parciales de la operación abierta
#               + no realizado de la posición abierta al último cierre.
# - Capital invertido (la base de los %) = la mayor inversión que el
#   agente tuvo en una sola operación: el costo de compra de cada
#   operación cerrada y el costo de lo que tiene abierto ahora. En spot
#   el agente tiene una operación a la vez, así que es "lo que pone en
#   juego"; sumar todas las compras diluiría el % con cada operación.
# - Drawdown actual = máximo del P&L acumulado (curva de operaciones
#   cerradas, desde 0) − P&L total de ahora. Es la caída desde el mejor
#   momento que todavía no se recuperó.
#
# EJEMPLO: operaciones cerradas de +40 y −20 (costos 1.000 y 800), posición
# abierta de 0,01 a 60.000 (costo 600) con último cierre 57.000 (−30):
#   P&L total = 40 − 20 − 30 = −10 → −10 / 1.000 = −1 %
#   pico = 40 → drawdown = 40 − (−10) = 50 → 50 / 1.000 = 5 %
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from app.common.utils import ensure_aware_utc
from app.modules.orders.domain.performance import Performance

_ZERO = Decimal("0")
_HUNDRED = Decimal("100")

PERIODIC_RULE_TYPES = ("price", "pnl", "drawdown")
PRICE_OPERATORS = ("lt", "lte", "gt", "gte")
PNL_PERIODS = ("daily", "total")


# ======================================================================
# Precio
# ======================================================================

def price_condition_met(price: Decimal, operator: str, threshold: Decimal) -> bool:
    """`lt`/`lte` = por debajo del umbral; `gt`/`gte` = por encima. Otro operador: False."""
    if operator == "lt":
        return price < threshold
    if operator == "lte":
        return price <= threshold
    if operator == "gt":
        return price > threshold
    if operator == "gte":
        return price >= threshold
    return False


# ======================================================================
# P&L y drawdown de un agente
# ======================================================================

@dataclass(frozen=True)
class BotPnlSnapshot:
    """P&L de un agente en un instante, en la moneda de cotización."""
    invested: Decimal      # base de los porcentajes
    total_pnl: Decimal     # realizado + parcial abierto + no realizado
    peak_pnl: Decimal      # máximo del P&L acumulado (≥ 0)

    @property
    def pnl_pct(self) -> Decimal | None:
        """−5.5 = −5,5 % del capital invertido; None sin operaciones."""
        return self.total_pnl / self.invested * _HUNDRED if self.invested > _ZERO else None

    @property
    def drawdown(self) -> Decimal:
        return max(_ZERO, self.peak_pnl - self.total_pnl)

    @property
    def drawdown_pct(self) -> Decimal | None:
        return self.drawdown / self.invested * _HUNDRED if self.invested > _ZERO else None


def bot_pnl_snapshot(perf: Performance, last_price: Decimal | None) -> BotPnlSnapshot:
    """Snapshot desde las métricas de M8 y el último cierre (None = sin precio)."""
    unrealized = _ZERO
    if perf.open_qty > _ZERO and last_price is not None:
        unrealized = (last_price - perf.open_avg_price) * perf.open_qty

    total = perf.realized_pnl + perf.open_realized_pnl + unrealized
    peak = max([_ZERO, *(value for _, value in perf.equity_curve)])
    invested = max([
        _ZERO,
        perf.open_qty * perf.open_avg_price,
        *(trade.cost for trade in perf.closed_trades),
    ])
    return BotPnlSnapshot(invested=invested, total_pnl=total, peak_pnl=peak)


def daily_pnl_pct(now: BotPnlSnapshot, day_start: BotPnlSnapshot) -> Decimal | None:
    """P&L ganado o perdido desde el inicio del día, sobre el capital invertido de ahora."""
    if now.invested <= _ZERO:
        return None
    return (now.total_pnl - day_start.total_pnl) / now.invested * _HUNDRED


def pnl_condition_met(pnl_pct: Decimal | None, threshold: Decimal) -> bool:
    """Umbral negativo: avisa al bajar hasta él (pérdida). Cero o positivo: al llegar a él."""
    if pnl_pct is None:
        return False
    if threshold < _ZERO:
        return pnl_pct <= threshold
    return pnl_pct >= threshold


def drawdown_condition_met(drawdown_pct: Decimal | None, threshold: Decimal) -> bool:
    """Avisa cuando la caída desde el máximo llega al umbral (positivo, en %)."""
    if drawdown_pct is None or threshold <= _ZERO:
        return False
    return drawdown_pct >= threshold


# ======================================================================
# Antispam
# ======================================================================

def in_cooldown(last_fired_at: datetime | None, now: datetime, repeat_minutes: int) -> bool:
    """
    True si la regla ya avisó hace menos de `repeat_minutes`.

    Mientras la condición siga cumpliéndose, el aviso se repite como
    máximo una vez por ventana (no en cada ciclo). `repeat_minutes <= 0`
    desactiva el antispam.
    """
    if last_fired_at is None or repeat_minutes <= 0:
        return False
    elapsed = ensure_aware_utc(now) - ensure_aware_utc(last_fired_at)
    return elapsed < timedelta(minutes=repeat_minutes)
