# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/services/pools/settle_agent_service.py
#
# CASOS DE USO:
# - preview(pool_id) → la liquidación calculada sin escribir nada, con lo
#                      que la impide (si algo). Staff.
# - settle(pool_id)  → la liquidación real (super admin), en un solo commit.
#
# CUÁNDO SE PUEDE LIQUIDAR (si no, la equity no sería exacta):
# - El agente no está `running` (pausado o detenido).
# - Sin posiciones abiertas ni órdenes vivas (new / sent / partially_filled).
# - Con unidades en 0 el agente no debe tener resultado: dinero sin dueño.
# - La equity resultante no puede ser negativa.
#
# QUÉ HACE (plan_settlement, dominio puro):
# 1. equity = equity anterior + flujo de caja de los fills nuevos; NAV.
# 2. Aplica la cola: por cada asignación, asiento `allocation` (sale del
#    saldo de la persona), lote de unidades al NAV y la orden `applied`.
#    Sin saldo suficiente → `canceled` con motivo.
# 3. Guarda la liquidación y el pool (UPDATE condicional: si otra
#    liquidación ganó, no se aplica nada).
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from app.common.contracts import ServiceResult
from app.common.utils import utc_now
from app.modules.bots.domain.bot_repository import BotRepository
from app.modules.fund.domain.agent_pool_entity import AgentPool, AgentSettlement, UnitLot
from app.modules.fund.domain.fund_repositories import (
    AgentPoolRepository,
    AgentSettlementRepository,
    AllocationOrderRepository,
    LedgerRepository,
    UnitLotRepository,
)
from app.modules.fund.domain.ledger_entry_entity import LedgerEntry
from app.modules.fund.domain.settlement import CashFlow, SettlementPlan, plan_settlement
from app.modules.fund.services.pools.agent_capital_service import AgentCapitalService
from app.modules.orders.domain.order_repository import OrderCriteria, OrderRepository

ALLOCATION_REF_TYPE = "allocation_order"
_OPEN_ORDER_STATUSES = ("new", "sent", "partially_filled")
_ZERO = Decimal("0")

# Motivos de cancelación de una asignación (texto para el historial)
_CANCEL_NOTES = {
    "insufficient_balance": "Cancelada al liquidar: la persona ya no tenía ese saldo.",
    "invalid_nav": "Cancelada al liquidar: el agente no tenía un valor de unidad válido.",
}


@dataclass(frozen=True)
class SettlementPreview:
    pool: AgentPool
    flow: CashFlow
    plan: SettlementPlan
    # Códigos que impiden liquidar ahora (vacío = se puede)
    blockers: list[str] = field(default_factory=list)


class SettleAgentService:

    def __init__(
        self,
        *,
        pool_repo: AgentPoolRepository,
        settlement_repo: AgentSettlementRepository,
        lot_repo: UnitLotRepository,
        allocation_repo: AllocationOrderRepository,
        ledger_repo: LedgerRepository,
        bot_repo: BotRepository,
        order_repo: OrderRepository,
        capital: AgentCapitalService,
    ):
        self._pool_repo = pool_repo
        self._settlement_repo = settlement_repo
        self._lot_repo = lot_repo
        self._allocation_repo = allocation_repo
        self._ledger_repo = ledger_repo
        self._bot_repo = bot_repo
        self._order_repo = order_repo
        self._capital = capital

    # ------------------------------------------------------------------
    # Vista previa
    # ------------------------------------------------------------------

    def preview(self, pool_id: int) -> ServiceResult[SettlementPreview]:
        pool = self._pool_repo.get_by_id(int(pool_id))
        if pool is None:
            return ServiceResult.fail(code="FUND_POOL_NOT_FOUND", http_status=404)
        bot = self._bot_repo.get_by_id(pool.bot_id)
        if bot is None:
            return ServiceResult.fail(code="FUND_BOT_NOT_FOUND", http_status=404)

        flow = self._capital.flow_since_settlement(pool, bot)
        queued = self._allocation_repo.list_queued(pool.id)
        balances = {
            (o.user_id, o.source_bucket): self._ledger_repo.bucket_balance(o.user_id, o.source_bucket)
            for o in queued
        }
        plan = plan_settlement(pool, flow, queued, balances)

        blockers: list[str] = []
        if bot.status == "running":
            blockers.append("FUND_SETTLE_BOT_RUNNING")
        if self._capital.open_cost(bot.id) > 0:
            blockers.append("FUND_SETTLE_OPEN_POSITIONS")
        if self._has_open_orders(bot.id):
            blockers.append("FUND_SETTLE_OPEN_ORDERS")
        if pool.units <= 0 and plan.equity_before != 0:
            blockers.append("FUND_SETTLE_ORPHAN_EQUITY")
        if plan.equity_before < 0:
            blockers.append("FUND_SETTLE_NEGATIVE_EQUITY")
        return ServiceResult.ok(SettlementPreview(pool, flow, plan, blockers))

    # ------------------------------------------------------------------
    # Liquidación
    # ------------------------------------------------------------------

    def settle(
        self, pool_id: int, *, requester_user_id: int, note: str | None = None
    ) -> ServiceResult[AgentSettlement]:
        result = self.preview(pool_id)
        if not result.success:
            return result
        preview = result.data
        if preview.blockers:
            return ServiceResult.fail(code=preview.blockers[0], http_status=409)

        pool, flow, plan = preview.pool, preview.flow, preview.plan
        expected_last_fill_id = pool.last_fill_id
        bot = self._bot_repo.get_by_id(pool.bot_id)
        agent_name = bot.name if bot else f"#{pool.bot_id}"
        now = utc_now()
        try:
            settlement = self._settlement_repo.create(
                AgentSettlement(
                    id=0,
                    pool_id=pool.id,
                    bot_id=pool.bot_id,
                    previous_equity=plan.previous_equity,
                    trading_result=plan.trading_result,
                    equity_before=plan.equity_before,
                    units_before=plan.units_before,
                    nav=plan.nav,
                    allocated_amount=plan.allocated_amount,
                    units_issued=plan.units_issued,
                    equity_after=plan.equity_after,
                    units_after=plan.units_after,
                    last_fill_id=flow.last_fill_id,
                    fills_count=flow.fills_count,
                    unvalued_fees={k: str(v) for k, v in flow.unvalued_fees.items()},
                    note=(note or "").strip()[:500] or None,
                    created_by_user_id=int(requester_user_id),
                )
            )

            for planned in plan.allocations:
                order = planned.order
                order.status = "applied"
                order.settlement_id = settlement.id
                order.resolved_at = now
                if not self._allocation_repo.update_if_status(order, ["queued"]):
                    self._pool_repo.rollback()
                    return ServiceResult.fail(code="FUND_SETTLE_CONFLICT", http_status=409)
                self._ledger_repo.add(
                    LedgerEntry(
                        id=0,
                        user_id=order.user_id,
                        entry_type="allocation",
                        bucket=order.source_bucket,
                        amount=-order.amount,
                        asset=pool.asset,
                        ref_type=ALLOCATION_REF_TYPE,
                        ref_id=order.id,
                        bot_id=pool.bot_id,
                        description=f"Asignado al agente «{agent_name}»",
                        created_by_user_id=int(requester_user_id),
                    )
                )
                self._lot_repo.create(
                    UnitLot(
                        id=0,
                        pool_id=pool.id,
                        user_id=order.user_id,
                        units=planned.units,
                        units_remaining=planned.units,
                        cost=order.amount,
                        nav_at_entry=plan.nav,
                        settlement_id=settlement.id,
                        acquired_at=now,
                    )
                )

            for canceled in plan.canceled:
                order = canceled.order
                order.status = "canceled"
                order.note = _CANCEL_NOTES.get(canceled.reason, canceled.reason)
                order.settlement_id = settlement.id
                order.resolved_at = now
                self._allocation_repo.update_if_status(order, ["queued"])

            pool.apply_settlement(
                settlement_id=settlement.id,
                equity=plan.equity_after,
                units=plan.units_after,
                last_fill_id=flow.last_fill_id,
            )
            if not self._pool_repo.update_settled(pool, expected_last_fill_id):
                self._pool_repo.rollback()
                return ServiceResult.fail(code="FUND_SETTLE_CONFLICT", http_status=409)
            self._pool_repo.commit()
        except Exception:
            self._pool_repo.rollback()
            raise
        return ServiceResult.ok(settlement)

    def _has_open_orders(self, bot_id: int) -> bool:
        return any(
            self._order_repo.count(OrderCriteria(bot_ids=[bot_id], status=status)) > 0
            for status in _OPEN_ORDER_STATUSES
        )
