# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/services/pools/allocation_service.py
#
# CASOS DE USO (super admin):
# - queue(...)  → poner en cola "X USDT de esta persona a este agente".
#                 No mueve dinero: se aplica en la próxima liquidación.
# - cancel(...) → sacar una asignación de la cola.
#
# REGLAS:
# - Sale del saldo pendiente de asignar o del disponible de la persona.
# - No se puede encolar más de lo que la persona tiene en ese saldo menos
#   lo que ya tiene en cola desde él (y, del disponible, menos los retiros
#   pedidos sin pagar). Al liquidar se vuelve a comprobar
#   (pudo haber una devolución entre medio).
# ======================================================================

from __future__ import annotations

from decimal import Decimal

from app.common.contracts import ServiceResult
from app.common.utils import utc_now
from app.modules.fund.domain.agent_pool_entity import ALLOCATION_SOURCES, AllocationOrder
from app.modules.fund.domain.fund_repositories import (
    AgentPoolRepository,
    AllocationOrderRepository,
    LedgerRepository,
)
from app.modules.fund.domain.payout_repositories import WithdrawalRequestRepository
from app.modules.users.domain import UserRepository

MAX_ALLOCATION = Decimal("1000000000")


class AllocationService:

    def __init__(
        self,
        *,
        allocation_repo: AllocationOrderRepository,
        pool_repo: AgentPoolRepository,
        ledger_repo: LedgerRepository,
        user_repo: UserRepository,
        withdrawal_repo: WithdrawalRequestRepository | None = None,
    ):
        self._allocation_repo = allocation_repo
        self._pool_repo = pool_repo
        self._ledger_repo = ledger_repo
        self._user_repo = user_repo
        self._withdrawal_repo = withdrawal_repo

    def queue(
        self,
        *,
        pool_id: int,
        user_id: int,
        amount: Decimal,
        source_bucket: str,
        requester_user_id: int,
    ) -> ServiceResult[AllocationOrder]:
        if self._pool_repo.get_by_id(int(pool_id)) is None:
            return ServiceResult.fail(code="FUND_POOL_NOT_FOUND", http_status=404)
        if self._user_repo.get_by_id(int(user_id)) is None:
            return ServiceResult.fail(code="FUND_USER_NOT_FOUND", http_status=404)
        if source_bucket not in ALLOCATION_SOURCES:
            return ServiceResult.fail(code="FUND_ALLOCATION_INVALID_SOURCE", http_status=422)
        if amount <= 0 or amount > MAX_ALLOCATION:
            return ServiceResult.fail(code="FUND_ALLOCATION_INVALID_AMOUNT", http_status=422)

        free = self._ledger_repo.bucket_balance(int(user_id), source_bucket)
        already = self._allocation_repo.queued_total(int(user_id), source_bucket)
        # Del disponible también se descuenta lo pedido para retirar (F5)
        if source_bucket == "available" and self._withdrawal_repo is not None:
            already += self._withdrawal_repo.open_total(int(user_id))
        if amount > free - already:
            return ServiceResult.fail(
                code="FUND_ALLOCATION_EXCEEDS_BALANCE",
                http_status=409,
                meta={"free": str(free - already)},
            )

        try:
            order = self._allocation_repo.create(
                AllocationOrder(
                    id=0,
                    pool_id=int(pool_id),
                    user_id=int(user_id),
                    amount=amount,
                    source_bucket=source_bucket,
                    created_by_user_id=int(requester_user_id),
                )
            )
            self._allocation_repo.commit()
        except Exception:
            self._allocation_repo.rollback()
            raise
        return ServiceResult.ok(order)

    def cancel(self, order_id: int) -> ServiceResult[AllocationOrder]:
        order = self._allocation_repo.get_by_id(int(order_id))
        if order is None:
            return ServiceResult.fail(code="FUND_ALLOCATION_NOT_FOUND", http_status=404)
        if order.status != "queued":
            return ServiceResult.fail(code="FUND_ALLOCATION_NOT_QUEUED", http_status=409)

        order.status = "canceled"
        order.note = "Cancelada por un super admin."
        order.resolved_at = utc_now()
        try:
            if not self._allocation_repo.update_if_status(order, ["queued"]):
                self._allocation_repo.rollback()
                return ServiceResult.fail(code="FUND_ALLOCATION_NOT_QUEUED", http_status=409)
            self._allocation_repo.commit()
        except Exception:
            self._allocation_repo.rollback()
            raise
        return ServiceResult.ok(order)
