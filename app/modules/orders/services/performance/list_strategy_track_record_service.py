# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/services/performance/list_strategy_track_record_service.py
#
# CASO DE USO:
# - Track record por estrategia (cualquier usuario con sesión): cómo le
#   ha ido a cada estrategia sumando las operaciones cerradas de TODOS
#   los agentes que la usan, separado por paper / live.
#
# REGLAS:
# - Anónimo: sin usuarios, cuentas ni montos. Se agregan RETORNOS (%)
#   por operación, que no dependen del tamaño de cada cuenta.
# - Profit factor sobre retornos: suma de % ganados / suma de % perdidos.
# - Drawdown sobre la curva de retornos sumados en orden de cierre.
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from app.common.contracts import ServiceResult
from app.modules.bots.domain.bot_repository import BotRepository
from app.modules.orders.domain.fill_repository import FillRepository
from app.modules.orders.domain.performance import ClosedTrade, compute_performance
from app.modules.strategies.domain.strategy_repository import StrategyRepository

_ZERO = Decimal("0")


@dataclass
class StrategyTrackRecord:
    strategy_id: int
    strategy_name: str
    mode: str
    agents: int = 0
    trades: int = 0
    wins: int = 0
    total_return_pct: Decimal = _ZERO
    gross_profit_pct: Decimal = _ZERO
    gross_loss_pct: Decimal = _ZERO
    max_drawdown_pct: Decimal = _ZERO
    best_trade_pct: Decimal | None = None
    worst_trade_pct: Decimal | None = None
    curve: list[tuple] = field(default_factory=list)

    @property
    def win_rate(self) -> Decimal | None:
        return Decimal(self.wins) / Decimal(self.trades) if self.trades else None

    @property
    def avg_return_pct(self) -> Decimal | None:
        return self.total_return_pct / Decimal(self.trades) if self.trades else None

    @property
    def profit_factor(self) -> Decimal | None:
        return self.gross_profit_pct / self.gross_loss_pct if self.gross_loss_pct > _ZERO else None


class ListStrategyTrackRecordService:
    """Historial agregado y anónimo por estrategia y modo."""

    def __init__(
        self,
        fill_repo: FillRepository,
        bot_repo: BotRepository,
        strategy_repo: StrategyRepository,
    ):
        self._fill_repo = fill_repo
        self._bot_repo = bot_repo
        self._strategy_repo = strategy_repo

    def list(self, mode: str | None = None) -> ServiceResult[list[StrategyTrackRecord]]:
        bots = [b for b in self._bot_repo.list_all() if mode is None or b.mode == mode]
        fills_by_bot = self._fill_repo.list_trade_fills_by_bots([b.id for b in bots])
        names = {s.id: f"{s.name} v{s.version}" for s in self._strategy_repo.list_all()}

        trades_by_key: dict[tuple[int, str], list[ClosedTrade]] = {}
        agents_by_key: dict[tuple[int, str], int] = {}
        for bot in bots:
            key = (bot.strategy_id, bot.mode)
            agents_by_key[key] = agents_by_key.get(key, 0) + 1
            closed = compute_performance(fills_by_bot.get(bot.id, [])).closed_trades
            trades_by_key.setdefault(key, []).extend(closed)

        records = [
            self._aggregate(strategy_id, bot_mode, names, agents_by_key[(strategy_id, bot_mode)], trades)
            for (strategy_id, bot_mode), trades in trades_by_key.items()
        ]
        records.sort(key=lambda r: (-r.trades, r.strategy_name))
        return ServiceResult.ok(records)

    @staticmethod
    def _aggregate(
        strategy_id: int,
        mode: str,
        names: dict[int, str],
        agents: int,
        trades: list[ClosedTrade],
    ) -> StrategyTrackRecord:
        record = StrategyTrackRecord(
            strategy_id=strategy_id,
            strategy_name=names.get(strategy_id, f"Estrategia #{strategy_id}"),
            mode=mode,
            agents=agents,
        )
        cumulative = _ZERO
        peak = _ZERO
        ordered = sorted(trades, key=lambda t: (t.closed_at is None, t.closed_at))
        for trade in ordered:
            ret = trade.return_pct
            if ret is None:
                continue
            record.trades += 1
            record.total_return_pct += ret
            if ret > _ZERO:
                record.wins += 1
                record.gross_profit_pct += ret
            elif ret < _ZERO:
                record.gross_loss_pct += -ret
            record.best_trade_pct = ret if record.best_trade_pct is None else max(record.best_trade_pct, ret)
            record.worst_trade_pct = ret if record.worst_trade_pct is None else min(record.worst_trade_pct, ret)
            cumulative += ret
            peak = max(peak, cumulative)
            record.max_drawdown_pct = max(record.max_drawdown_pct, peak - cumulative)
            record.curve.append((trade.closed_at, cumulative))
        return record
