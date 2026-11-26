# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/services/pools/redemption_service.py
#
# CASOS DE USO:
# - request(...)   → "saca X USDT (o todo) de este agente". Lo pide la propia
#                    persona (decisión del usuario: cada participante decide
#                    cuándo sacar dinero) o un super admin por ella.
# - cancel(...)    → sacarla de la cola (la persona o un super admin).
# - mine(user_id)  → mis salidas en cola y lo que ya salió, con la comisión
#                    tramo por tramo.
#
# REGLAS:
# - Se aplica en la próxima liquidación del agente, al NAV de ese momento.
# - Sale solo lo que cumple la permanencia mínima; si no alcanza, sale lo
#   que cumple y se informa lo pendiente (decisión del usuario).
# - Una sola salida en cola por persona y agente (para no pisarse).
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from app.common.contracts import ServiceResult
from app.common.utils import utc_now
from app.modules.fund.domain.agent_pool_entity import RedemptionRequest, SettlementRedemption
from app.modules.fund.domain.fund_repositories import AgentPoolRepository, UnitLotRepository
from app.modules.fund.domain.payout_repositories import (
    RedemptionRequestRepository,
    SettlementRedemptionRepository,
)
from app.modules.fund.services.pools.agent_info import AgentInfo, AgentInfoReader


@dataclass(frozen=True)
class MyRedemptions:
    queued: list[RedemptionRequest] = field(default_factory=list)
    history: list[RedemptionRequest] = field(default_factory=list)
    lines: list[SettlementRedemption] = field(default_factory=list)
    # pool_id → agente: la persona puede haber salido del todo y ya no verlo
    # en sus participaciones
    agents: dict[int, AgentInfo | None] = field(default_factory=dict)


class RedemptionService:

    def __init__(
        self,
        *,
        repo: RedemptionRequestRepository,
        line_repo: SettlementRedemptionRepository,
        pool_repo: AgentPoolRepository,
        lot_repo: UnitLotRepository,
        agents: AgentInfoReader,
    ):
        self._repo = repo
        self._line_repo = line_repo
        self._pool_repo = pool_repo
        self._lot_repo = lot_repo
        self._agents = agents

    def request(
        self,
        *,
        pool_id: int,
        user_id: int,
        amount: Decimal | None,
        requester_user_id: int,
    ) -> ServiceResult[RedemptionRequest]:
        if self._pool_repo.get_by_id(int(pool_id)) is None:
            return ServiceResult.fail(code="FUND_POOL_NOT_FOUND", http_status=404)
        if amount is not None and amount <= 0:
            return ServiceResult.fail(code="FUND_REDEMPTION_INVALID_AMOUNT", http_status=422)
        has_units = any(
            lot.pool_id == int(pool_id) for lot in self._lot_repo.list_by_user(int(user_id))
        )
        if not has_units:
            return ServiceResult.fail(code="FUND_REDEMPTION_NO_UNITS", http_status=409)
        if any(
            r.pool_id == int(pool_id) and r.user_id == int(user_id)
            for r in self._repo.list_queued(int(pool_id))
        ):
            return ServiceResult.fail(code="FUND_REDEMPTION_ALREADY_QUEUED", http_status=409)

        try:
            created = self._repo.create(
                RedemptionRequest(
                    id=0,
                    pool_id=int(pool_id),
                    user_id=int(user_id),
                    amount=amount,
                    created_by_user_id=int(requester_user_id),
                )
            )
            self._repo.commit()
        except Exception:
            self._repo.rollback()
            raise
        return ServiceResult.ok(created)

    def cancel(
        self, request_id: int, *, requester_user_id: int, is_manager: bool
    ) -> ServiceResult[RedemptionRequest]:
        request = self._repo.get_by_id(int(request_id))
        if request is None or (not is_manager and not request.belongs_to(requester_user_id)):
            return ServiceResult.fail(code="FUND_REDEMPTION_NOT_FOUND", http_status=404)
        request.status = "canceled"
        request.note = "Anulada antes de la liquidación."
        request.resolved_at = utc_now()
        try:
            if not self._repo.update_if_status(request, ["queued"]):
                self._repo.rollback()
                return ServiceResult.fail(code="FUND_REDEMPTION_NOT_QUEUED", http_status=409)
            self._repo.commit()
        except Exception:
            self._repo.rollback()
            raise
        return ServiceResult.ok(request)

    def mine(self, user_id: int) -> ServiceResult[MyRedemptions]:
        requests = self._repo.list_by_user(int(user_id))
        lines = self._line_repo.list_by_user(int(user_id))
        agents: dict[int, AgentInfo | None] = {}
        for pool_id in {r.pool_id for r in requests} | {line.pool_id for line in lines}:
            pool = self._pool_repo.get_by_id(pool_id)
            agents[pool_id] = self._agents.info_by_id(pool.bot_id) if pool else None
        return ServiceResult.ok(
            MyRedemptions(
                queued=[r for r in requests if r.status == "queued"],
                history=[r for r in requests if r.status != "queued"],
                lines=lines,
                agents=agents,
            )
        )
