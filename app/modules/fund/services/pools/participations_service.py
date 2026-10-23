# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/services/pools/participations_service.py
#
# CASO DE USO:
# - mine(user_id) → en qué agentes está el dinero de una persona: unidades,
#   costo, valor a la última liquidación y el estado del agente. Lo ve la
#   propia persona (también el inversor): transparencia sin mostrar la
#   billetera.
#
# NOTA:
# - "Valor" = unidades × NAV de la última liquidación (exacto). Entre
#   liquidaciones el agente puede ir ganando o perdiendo; se indica la fecha
#   de esa liquidación.
# ======================================================================

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.common.contracts import ServiceResult
from app.modules.fund.domain.fund_repositories import (
    AgentPoolRepository,
    AgentSettlementRepository,
    UnitLotRepository,
)
from app.modules.fund.services.pools.agent_info import AgentInfo, AgentInfoReader

_ZERO = Decimal("0")


@dataclass(frozen=True)
class Participation:
    pool_id: int
    agent: AgentInfo | None
    units: Decimal
    cost: Decimal
    nav: Decimal
    value: Decimal
    first_acquired_at: datetime | None
    last_settled_at: datetime | None

    @property
    def result(self) -> Decimal:
        return self.value - self.cost


class ParticipationsService:

    def __init__(
        self,
        *,
        lot_repo: UnitLotRepository,
        pool_repo: AgentPoolRepository,
        settlement_repo: AgentSettlementRepository,
        agents: AgentInfoReader,
    ):
        self._lot_repo = lot_repo
        self._pool_repo = pool_repo
        self._settlement_repo = settlement_repo
        self._agents = agents

    def mine(self, user_id: int) -> ServiceResult[list[Participation]]:
        units: dict[int, Decimal] = defaultdict(lambda: _ZERO)
        cost: dict[int, Decimal] = defaultdict(lambda: _ZERO)
        first: dict[int, datetime | None] = {}
        for lot in self._lot_repo.list_by_user(int(user_id)):
            units[lot.pool_id] += lot.units_remaining
            cost[lot.pool_id] += lot.cost_remaining
            first.setdefault(lot.pool_id, lot.acquired_at)

        participations: list[Participation] = []
        for pool_id, pool_units in units.items():
            pool = self._pool_repo.get_by_id(pool_id)
            if pool is None:
                continue
            last = self._settlement_repo.list_by_pool(pool_id, limit=1)
            participations.append(
                Participation(
                    pool_id=pool_id,
                    agent=self._agents.info_by_id(pool.bot_id),
                    units=pool_units,
                    cost=cost[pool_id],
                    nav=pool.nav,
                    value=pool_units * pool.nav,
                    first_acquired_at=first.get(pool_id),
                    last_settled_at=last[0].settled_at if last else None,
                )
            )
        return ServiceResult.ok(participations)
