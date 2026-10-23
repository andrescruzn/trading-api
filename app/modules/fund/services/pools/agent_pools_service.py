# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/services/pools/agent_pools_service.py
#
# CASOS DE USO (staff; abrir, solo super admin):
# - open(bot_id)    → abrir un agente al fondo (crea su pool).
# - eligible()      → agentes que se pueden abrir: sobre la billetera de la
#                     plataforma, con par en la moneda del fondo y sin pool.
# - list()          → pools con su agente, capital estimado, cola y
#                     participantes.
# - detail(pool_id) → lo anterior + participantes (unidades, costo, valor),
#                     asignaciones en cola y liquidaciones.
#
# REGLAS AL ABRIR:
# - El agente debe operar sobre la billetera de la plataforma: es el dinero
#   de todos.
# - Su par debe cotizar en la moneda del fondo (USDT): el pool lleva la
#   cuenta en esa moneda.
# - Lo que el agente operó antes de abrirse (pruebas) no cuenta: el pool
#   arranca desde su último fill.
# ======================================================================

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from app.common.contracts import ServiceResult
from app.modules.accounts.domain.platform_wallet_repository import PlatformWalletRepository
from app.modules.bots.domain.bot_repository import BotRepository
from app.modules.fund.domain.agent_pool_entity import (
    AgentPool,
    AgentSettlement,
    AllocationOrder,
)
from app.modules.fund.domain.fund_repositories import (
    AgentPoolRepository,
    AgentSettlementRepository,
    AllocationOrderRepository,
    UnitLotRepository,
)
from app.modules.fund.services.pools.agent_capital_service import AgentCapitalService
from app.modules.fund.services.pools.agent_info import AgentInfo, AgentInfoReader
from app.modules.market.domain.symbol_repository import SymbolRepository
from app.modules.orders.domain.fill_repository import FillRepository

_ZERO = Decimal("0")


@dataclass(frozen=True)
class PoolOverview:
    pool: AgentPool
    agent: AgentInfo | None
    # Capital del agente hoy (equity liquidada + resultado desde entonces, a costo)
    estimated_capital: Decimal
    queued_total: Decimal
    participants: int
    last_settled_at: datetime | None


@dataclass(frozen=True)
class ParticipantPosition:
    user_id: int
    units: Decimal
    cost: Decimal
    value: Decimal
    share: Decimal
    first_acquired_at: datetime | None


@dataclass(frozen=True)
class PoolDetail:
    overview: PoolOverview
    participants: list[ParticipantPosition] = field(default_factory=list)
    queued: list[AllocationOrder] = field(default_factory=list)
    settlements: list[AgentSettlement] = field(default_factory=list)


class AgentPoolsService:

    def __init__(
        self,
        *,
        pool_repo: AgentPoolRepository,
        lot_repo: UnitLotRepository,
        allocation_repo: AllocationOrderRepository,
        settlement_repo: AgentSettlementRepository,
        wallet_repo: PlatformWalletRepository,
        bot_repo: BotRepository,
        symbol_repo: SymbolRepository,
        fill_repo: FillRepository,
        capital: AgentCapitalService,
    ):
        self._pool_repo = pool_repo
        self._lot_repo = lot_repo
        self._allocation_repo = allocation_repo
        self._settlement_repo = settlement_repo
        self._wallet_repo = wallet_repo
        self._bot_repo = bot_repo
        self._symbol_repo = symbol_repo
        self._fill_repo = fill_repo
        self._capital = capital
        self._agents = AgentInfoReader(bot_repo, symbol_repo)

    # ------------------------------------------------------------------
    # Abrir un agente al fondo
    # ------------------------------------------------------------------

    def eligible(self) -> ServiceResult[list[AgentInfo]]:
        wallet = self._wallet_repo.get()
        if wallet is None:
            return ServiceResult.ok([])
        with_pool = {p.bot_id for p in self._pool_repo.list_all()}
        agents: list[AgentInfo] = []
        for bot in self._bot_repo.list_by_account(wallet.account_id):
            if bot.id in with_pool:
                continue
            symbol = self._symbol_repo.get_by_id(bot.symbol_id)
            if symbol is not None and (symbol.quote_asset or "").upper() == wallet.base_asset.upper():
                agents.append(self._agents.info(bot))
        return ServiceResult.ok(agents)

    def open(self, bot_id: int, requester_user_id: int) -> ServiceResult[AgentPool]:
        bot = self._bot_repo.get_by_id(int(bot_id))
        if bot is None:
            return ServiceResult.fail(code="FUND_BOT_NOT_FOUND", http_status=404)
        wallet = self._wallet_repo.get()
        if wallet is None:
            return ServiceResult.fail(code="FUND_WALLET_NOT_CONFIGURED", http_status=409)
        if bot.account_id != wallet.account_id:
            return ServiceResult.fail(code="FUND_BOT_NOT_ON_WALLET", http_status=422)
        symbol = self._symbol_repo.get_by_id(bot.symbol_id)
        if symbol is None or (symbol.quote_asset or "").upper() != wallet.base_asset.upper():
            return ServiceResult.fail(code="FUND_BOT_WRONG_QUOTE", http_status=422)
        if self._pool_repo.get_by_bot(bot.id) is not None:
            return ServiceResult.fail(code="FUND_POOL_EXISTS", http_status=409)

        try:
            pool = self._pool_repo.create(
                AgentPool(
                    id=0,
                    bot_id=bot.id,
                    asset=wallet.base_asset.upper(),
                    last_fill_id=self._fill_repo.max_id_by_bot(bot.id),
                    created_by_user_id=int(requester_user_id),
                )
            )
            self._pool_repo.commit()
        except Exception:
            self._pool_repo.rollback()
            raise
        return ServiceResult.ok(pool)

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------

    def list(self) -> ServiceResult[list[PoolOverview]]:
        queued = self._allocation_repo.list_queued()
        return ServiceResult.ok(
            [self._overview(pool, queued) for pool in self._pool_repo.list_all()]
        )

    def detail(self, pool_id: int) -> ServiceResult[PoolDetail]:
        pool = self._pool_repo.get_by_id(int(pool_id))
        if pool is None:
            return ServiceResult.fail(code="FUND_POOL_NOT_FOUND", http_status=404)
        queued = self._allocation_repo.list_queued(pool.id)
        return ServiceResult.ok(
            PoolDetail(
                overview=self._overview(pool, queued),
                participants=self._participants(pool),
                queued=queued,
                settlements=self._settlement_repo.list_by_pool(pool.id),
            )
        )

    def _overview(self, pool: AgentPool, queued: list[AllocationOrder]) -> PoolOverview:
        bot = self._bot_repo.get_by_id(pool.bot_id)
        fund = self._capital.capital_for(bot) if bot else None
        lots = self._lot_repo.list_by_pool(pool.id)
        settlements = self._settlement_repo.list_by_pool(pool.id, limit=1)
        return PoolOverview(
            pool=pool,
            agent=self._agents.info(bot) if bot else None,
            estimated_capital=fund.capital if fund else pool.equity,
            queued_total=sum((o.amount for o in queued if o.pool_id == pool.id), _ZERO),
            participants=len({lot.user_id for lot in lots}),
            last_settled_at=settlements[0].settled_at if settlements else None,
        )

    def _participants(self, pool: AgentPool) -> list[ParticipantPosition]:
        units: dict[int, Decimal] = defaultdict(lambda: _ZERO)
        cost: dict[int, Decimal] = defaultdict(lambda: _ZERO)
        first: dict[int, datetime | None] = {}
        for lot in self._lot_repo.list_by_pool(pool.id):
            units[lot.user_id] += lot.units_remaining
            cost[lot.user_id] += lot.cost_remaining
            first.setdefault(lot.user_id, lot.acquired_at)
        nav = pool.nav
        return sorted(
            (
                ParticipantPosition(
                    user_id=user_id,
                    units=units[user_id],
                    cost=cost[user_id],
                    value=units[user_id] * nav,
                    share=(units[user_id] / pool.units) if pool.units > 0 else _ZERO,
                    first_acquired_at=first.get(user_id),
                )
                for user_id in units
            ),
            key=lambda p: p.units,
            reverse=True,
        )
