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
# - Si hay salidas: debe existir tabla de comisión y, si alguna paga
#   comisión, un reparto entre propietarios.
#
# QUÉ HACE (plan_settlement, dominio puro):
# 1. equity = equity anterior + flujo de caja de los fills nuevos; NAV.
# 2. Salidas (F5): lotes FIFO que cumplen la permanencia; por cada una,
#    asiento `redemption` (+valor al disponible), `fee` (−comisión) y
#    `commission` (+parte de cada propietario); la línea con la comisión
#    tramo por tramo queda para la persona.
# 3. Entradas (F4): asiento `allocation`, lote de unidades al NAV.
# 4. Guarda la liquidación y el pool (UPDATE condicional: si otra
#    liquidación ganó, no se aplica nada).
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal

from app.common.contracts import ServiceResult
from app.common.utils import utc_now
from app.modules.bots.domain.bot_repository import BotRepository
from app.modules.fund.domain.agent_pool_entity import (
    AgentPool,
    AgentSettlement,
    CommissionCredit,
    SettlementRedemption,
    UnitLot,
)
from app.modules.fund.domain.commission import CommissionShareVersion, FeeSchedule
from app.modules.fund.domain.fund_repositories import (
    AgentPoolRepository,
    AgentSettlementRepository,
    AllocationOrderRepository,
    FundSettingsRepository,
    LedgerRepository,
    UnitLotRepository,
)
from app.modules.fund.domain.ledger_entry_entity import LedgerEntry
from app.modules.fund.domain.payout_repositories import (
    CommissionCreditRepository,
    CommissionShareRepository,
    FeeScheduleRepository,
    RedemptionRequestRepository,
    SettlementRedemptionRepository,
)
from app.modules.fund.domain.settlement import (
    CashFlow,
    PlannedRedemption,
    SettlementPlan,
    plan_settlement,
)
from app.modules.fund.services.pools.agent_capital_service import AgentCapitalService
from app.modules.orders.domain.order_repository import OrderCriteria, OrderRepository

ALLOCATION_REF_TYPE = "allocation_order"
REDEMPTION_REF_TYPE = "settlement_redemption"
COMMISSION_REF_TYPE = "commission_credit"
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
    hold_cutoff: datetime | None
    fee_schedule: FeeSchedule | None
    shares: CommissionShareVersion | None
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
        settings_repo: FundSettingsRepository,
        redemption_repo: RedemptionRequestRepository,
        line_repo: SettlementRedemptionRepository,
        credit_repo: CommissionCreditRepository,
        fee_repo: FeeScheduleRepository,
        shares_repo: CommissionShareRepository,
    ):
        self._pool_repo = pool_repo
        self._settlement_repo = settlement_repo
        self._lot_repo = lot_repo
        self._allocation_repo = allocation_repo
        self._ledger_repo = ledger_repo
        self._bot_repo = bot_repo
        self._order_repo = order_repo
        self._capital = capital
        self._settings_repo = settings_repo
        self._redemption_repo = redemption_repo
        self._line_repo = line_repo
        self._credit_repo = credit_repo
        self._fee_repo = fee_repo
        self._shares_repo = shares_repo

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
        redemptions = self._redemption_repo.list_queued(pool.id)
        schedule = self._fee_repo.current()
        shares = self._shares_repo.current()
        cutoff = utc_now() - timedelta(days=self._settings_repo.get().min_hold_days)
        plan = plan_settlement(
            pool,
            flow,
            queued,
            balances,
            redemptions=redemptions,
            lots=self._lot_repo.list_by_pool(pool.id),
            hold_cutoff=cutoff,
            fee_tiers=schedule.tiers if schedule else [],
            shares=shares.shares if shares else [],
        )

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
        if plan.redemptions and schedule is None:
            blockers.append("FUND_SETTLE_NO_FEE_SCHEDULE")
        if plan.fees_total > 0 and shares is None:
            blockers.append("FUND_SETTLE_NO_COMMISSION_SHARES")
        return ServiceResult.ok(
            SettlementPreview(pool, flow, plan, cutoff, schedule, shares, blockers)
        )

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
        by = int(requester_user_id)
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
                    created_by_user_id=by,
                    redeemed_amount=plan.redeemed_amount,
                    units_redeemed=plan.units_redeemed,
                    fees_total=plan.fees_total,
                )
            )

            # 1. Salidas
            for planned in plan.redemptions:
                if not self._apply_redemption(
                    planned, preview, settlement, agent_name=agent_name, by=by, now=now
                ):
                    self._pool_repo.rollback()
                    return ServiceResult.fail(code="FUND_SETTLE_CONFLICT", http_status=409)

            # 2. Entradas
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
                        created_by_user_id=by,
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

    def _apply_redemption(
        self,
        planned: PlannedRedemption,
        preview: SettlementPreview,
        settlement: AgentSettlement,
        *,
        agent_name: str,
        by: int,
        now: datetime,
    ) -> bool:
        """Escribe una salida (lotes, línea, asientos y comisiones). False = conflicto."""
        pool = preview.pool
        for lot_id, units in planned.consumed:
            if not self._lot_repo.consume(lot_id, units):
                return False

        order = planned.order
        order.status = "applied"
        order.settlement_id = settlement.id
        order.resolved_at = now
        if planned.pending_amount:
            order.note = (
                f"Salieron {planned.value.quantize(Decimal('0.01'))} {pool.asset}; "
                f"{planned.pending_amount.quantize(Decimal('0.01'))} aún no cumplían la permanencia mínima."
            )
        if not self._redemption_repo.update_if_status(order, ["queued"]):
            return False

        line = self._line_repo.create(
            SettlementRedemption(
                id=0,
                settlement_id=settlement.id,
                redemption_request_id=order.id,
                pool_id=pool.id,
                user_id=order.user_id,
                units=planned.units,
                value=planned.value,
                cost=planned.cost,
                gain=planned.gain,
                return_pct=planned.return_pct,
                fee=planned.fee,
                net=planned.net,
                pending_amount=planned.pending_amount,
                fee_schedule_id=preview.fee_schedule.id if preview.fee_schedule else None,
                commission_version_id=preview.shares.id if preview.shares else None,
                breakdown=[
                    {
                        "from_return": str(c.from_return),
                        "to_return": None if c.to_return is None else str(c.to_return),
                        "rate": str(c.rate),
                        "base": str(c.base),
                        "fee": str(c.fee),
                    }
                    for c in planned.breakdown
                ],
            )
        )
        self._ledger_repo.add(
            LedgerEntry(
                id=0,
                user_id=order.user_id,
                entry_type="redemption",
                bucket="available",
                amount=planned.value,
                asset=pool.asset,
                ref_type=REDEMPTION_REF_TYPE,
                ref_id=line.id,
                bot_id=pool.bot_id,
                description=f"Salida del agente «{agent_name}»",
                created_by_user_id=by,
            )
        )
        if planned.fee > 0:
            self._ledger_repo.add(
                LedgerEntry(
                    id=0,
                    user_id=order.user_id,
                    entry_type="fee",
                    bucket="available",
                    amount=-planned.fee,
                    asset=pool.asset,
                    ref_type=REDEMPTION_REF_TYPE,
                    ref_id=line.id,
                    bot_id=pool.bot_id,
                    description=f"Comisión sobre la ganancia ({(planned.return_pct * 100).quantize(Decimal('0.01'))} % de retorno)",
                    created_by_user_id=by,
                )
            )
        for owner_id, amount in planned.commissions:
            credit = self._credit_repo.create(
                CommissionCredit(id=0, settlement_redemption_id=line.id, user_id=owner_id, amount=amount)
            )
            self._ledger_repo.add(
                LedgerEntry(
                    id=0,
                    user_id=owner_id,
                    entry_type="commission",
                    bucket="available",
                    amount=amount,
                    asset=pool.asset,
                    ref_type=COMMISSION_REF_TYPE,
                    ref_id=credit.id,
                    bot_id=pool.bot_id,
                    description=f"Comisión del agente «{agent_name}»",
                    created_by_user_id=by,
                )
            )
        return True

    def _has_open_orders(self, bot_id: int) -> bool:
        return any(
            self._order_repo.count(OrderCriteria(bot_ids=[bot_id], status=status)) > 0
            for status in _OPEN_ORDER_STATUSES
        )
