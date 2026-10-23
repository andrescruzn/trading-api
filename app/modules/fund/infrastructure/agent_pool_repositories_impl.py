# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/infrastructure/agent_pool_repositories_impl.py
#
# Implementaciones SQLAlchemy del capital de los agentes (F4): pools,
# liquidaciones, lotes de unidades y asignaciones en cola.
# ======================================================================

from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.common.utils import ensure_aware_utc
from app.extensions.db.sqlalchemy_repository import SqlAlchemyRepository
from app.modules.fund.domain.agent_pool_entity import (
    AgentPool,
    AgentSettlement,
    AllocationOrder,
    UnitLot,
)
from app.modules.fund.domain.fund_repositories import (
    AgentPoolRepository,
    AgentSettlementRepository,
    AllocationOrderRepository,
    UnitLotRepository,
)
from app.modules.fund.infrastructure.agent_pool_models import (
    AgentPoolModel,
    AgentSettlementModel,
    AllocationOrderModel,
    UnitLotModel,
)

_ZERO = Decimal("0")


def _decimal(value: Any) -> Decimal:
    return Decimal(str(value)) if value is not None else _ZERO


# ======================================================================
# Pools
# ======================================================================

class SqlAlchemyAgentPoolRepository(SqlAlchemyRepository, AgentPoolRepository):

    def __init__(self, session: Session):
        self._session = session

    @staticmethod
    def _to_domain(m: AgentPoolModel) -> AgentPool:
        return AgentPool(
            id=m.id,
            bot_id=m.bot_id,
            asset=m.asset,
            equity=_decimal(m.equity),
            units=_decimal(m.units),
            last_fill_id=int(m.last_fill_id or 0),
            last_settlement_id=m.last_settlement_id,
            created_by_user_id=m.created_by_user_id,
            created_at=ensure_aware_utc(m.created_at),
            updated_at=ensure_aware_utc(m.updated_at),
        )

    def get_by_id(self, pool_id: int) -> AgentPool | None:
        m = self._session.get(AgentPoolModel, pool_id)
        return None if m is None else self._to_domain(m)

    def get_by_bot(self, bot_id: int) -> AgentPool | None:
        m = self._session.query(AgentPoolModel).filter(AgentPoolModel.bot_id == bot_id).first()
        return None if m is None else self._to_domain(m)

    def list_all(self) -> list[AgentPool]:
        return [
            self._to_domain(m)
            for m in self._session.query(AgentPoolModel).order_by(AgentPoolModel.id).all()
        ]

    def create(self, pool: AgentPool) -> AgentPool:
        m = AgentPoolModel(
            bot_id=pool.bot_id,
            asset=pool.asset,
            equity=pool.equity,
            units=pool.units,
            last_fill_id=pool.last_fill_id,
            created_by_user_id=pool.created_by_user_id,
        )
        self._session.add(m)
        self._session.flush()
        self._session.refresh(m)
        return self._to_domain(m)

    def update_settled(self, pool: AgentPool, expected_last_fill_id: int) -> bool:
        updated = (
            self._session.query(AgentPoolModel)
            .filter(
                AgentPoolModel.id == pool.id,
                AgentPoolModel.last_fill_id == expected_last_fill_id,
                # Sin fills nuevos el last_fill_id no cambia: la liquidación
                # anterior también debe ser la esperada
                (
                    AgentPoolModel.last_settlement_id.is_(None)
                    if pool.previous_settlement_id is None
                    else AgentPoolModel.last_settlement_id == pool.previous_settlement_id
                ),
            )
            .update(
                {
                    "equity": pool.equity,
                    "units": pool.units,
                    "last_fill_id": pool.last_fill_id,
                    "last_settlement_id": pool.last_settlement_id,
                },
                synchronize_session=False,
            )
        )
        self._session.flush()
        return updated == 1


# ======================================================================
# Liquidaciones
# ======================================================================

class SqlAlchemyAgentSettlementRepository(SqlAlchemyRepository, AgentSettlementRepository):

    def __init__(self, session: Session):
        self._session = session

    @staticmethod
    def _to_domain(m: AgentSettlementModel) -> AgentSettlement:
        return AgentSettlement(
            id=m.id,
            pool_id=m.pool_id,
            bot_id=m.bot_id,
            previous_equity=_decimal(m.previous_equity),
            trading_result=_decimal(m.trading_result),
            equity_before=_decimal(m.equity_before),
            units_before=_decimal(m.units_before),
            nav=_decimal(m.nav),
            allocated_amount=_decimal(m.allocated_amount),
            units_issued=_decimal(m.units_issued),
            equity_after=_decimal(m.equity_after),
            units_after=_decimal(m.units_after),
            last_fill_id=int(m.last_fill_id),
            fills_count=int(m.fills_count or 0),
            unvalued_fees=dict(m.unvalued_fees or {}),
            note=m.note,
            created_by_user_id=m.created_by_user_id,
            settled_at=ensure_aware_utc(m.settled_at),
            redeemed_amount=_decimal(m.redeemed_amount),
            units_redeemed=_decimal(m.units_redeemed),
            fees_total=_decimal(m.fees_total),
        )

    def create(self, s: AgentSettlement) -> AgentSettlement:
        m = AgentSettlementModel(
            pool_id=s.pool_id,
            bot_id=s.bot_id,
            previous_equity=s.previous_equity,
            trading_result=s.trading_result,
            equity_before=s.equity_before,
            units_before=s.units_before,
            nav=s.nav,
            allocated_amount=s.allocated_amount,
            units_issued=s.units_issued,
            equity_after=s.equity_after,
            units_after=s.units_after,
            last_fill_id=s.last_fill_id,
            fills_count=s.fills_count,
            unvalued_fees=dict(s.unvalued_fees),
            note=s.note,
            created_by_user_id=s.created_by_user_id,
            redeemed_amount=s.redeemed_amount,
            units_redeemed=s.units_redeemed,
            fees_total=s.fees_total,
        )
        self._session.add(m)
        self._session.flush()
        self._session.refresh(m)
        return self._to_domain(m)

    def list_by_pool(self, pool_id: int, limit: int = 50) -> list[AgentSettlement]:
        models = (
            self._session.query(AgentSettlementModel)
            .filter(AgentSettlementModel.pool_id == pool_id)
            .order_by(AgentSettlementModel.settled_at.desc(), AgentSettlementModel.id.desc())
            .limit(limit)
            .all()
        )
        return [self._to_domain(m) for m in models]


# ======================================================================
# Lotes de unidades
# ======================================================================

class SqlAlchemyUnitLotRepository(SqlAlchemyRepository, UnitLotRepository):

    def __init__(self, session: Session):
        self._session = session

    @staticmethod
    def _to_domain(m: UnitLotModel) -> UnitLot:
        return UnitLot(
            id=m.id,
            pool_id=m.pool_id,
            user_id=m.user_id,
            units=_decimal(m.units),
            units_remaining=_decimal(m.units_remaining),
            cost=_decimal(m.cost),
            nav_at_entry=_decimal(m.nav_at_entry),
            settlement_id=m.settlement_id,
            acquired_at=ensure_aware_utc(m.acquired_at),
        )

    def create(self, lot: UnitLot) -> UnitLot:
        m = UnitLotModel(
            pool_id=lot.pool_id,
            user_id=lot.user_id,
            units=lot.units,
            units_remaining=lot.units_remaining,
            cost=lot.cost,
            nav_at_entry=lot.nav_at_entry,
            settlement_id=lot.settlement_id,
        )
        if lot.acquired_at is not None:
            m.acquired_at = lot.acquired_at
        self._session.add(m)
        self._session.flush()
        self._session.refresh(m)
        return self._to_domain(m)

    def _live(self):
        return self._session.query(UnitLotModel).filter(UnitLotModel.units_remaining > 0)

    def list_by_pool(self, pool_id: int) -> list[UnitLot]:
        models = (
            self._live()
            .filter(UnitLotModel.pool_id == pool_id)
            .order_by(UnitLotModel.acquired_at, UnitLotModel.id)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def list_by_user(self, user_id: int) -> list[UnitLot]:
        models = (
            self._live()
            .filter(UnitLotModel.user_id == user_id)
            .order_by(UnitLotModel.acquired_at, UnitLotModel.id)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def consume(self, lot_id: int, units: Decimal) -> bool:
        updated = (
            self._session.query(UnitLotModel)
            .filter(UnitLotModel.id == lot_id, UnitLotModel.units_remaining >= units)
            .update(
                {"units_remaining": UnitLotModel.units_remaining - units},
                synchronize_session=False,
            )
        )
        self._session.flush()
        return updated == 1


# ======================================================================
# Asignaciones en cola
# ======================================================================

class SqlAlchemyAllocationOrderRepository(SqlAlchemyRepository, AllocationOrderRepository):

    def __init__(self, session: Session):
        self._session = session

    @staticmethod
    def _to_domain(m: AllocationOrderModel) -> AllocationOrder:
        return AllocationOrder(
            id=m.id,
            pool_id=m.pool_id,
            user_id=m.user_id,
            amount=_decimal(m.amount),
            source_bucket=m.source_bucket,
            status=m.status,
            note=m.note,
            settlement_id=m.settlement_id,
            created_by_user_id=m.created_by_user_id,
            created_at=ensure_aware_utc(m.created_at),
            resolved_at=ensure_aware_utc(m.resolved_at),
        )

    def create(self, order: AllocationOrder) -> AllocationOrder:
        m = AllocationOrderModel(
            pool_id=order.pool_id,
            user_id=order.user_id,
            amount=order.amount,
            source_bucket=order.source_bucket,
            status=order.status,
            created_by_user_id=order.created_by_user_id,
        )
        self._session.add(m)
        self._session.flush()
        self._session.refresh(m)
        return self._to_domain(m)

    def get_by_id(self, order_id: int) -> AllocationOrder | None:
        m = self._session.get(AllocationOrderModel, order_id)
        return None if m is None else self._to_domain(m)

    def list_queued(self, pool_id: int | None = None) -> list[AllocationOrder]:
        query = self._session.query(AllocationOrderModel).filter(
            AllocationOrderModel.status == "queued"
        )
        if pool_id is not None:
            query = query.filter(AllocationOrderModel.pool_id == pool_id)
        return [self._to_domain(m) for m in query.order_by(AllocationOrderModel.id).all()]

    def queued_total(self, user_id: int, bucket: str) -> Decimal:
        value = (
            self._session.query(func.coalesce(func.sum(AllocationOrderModel.amount), 0))
            .filter(
                AllocationOrderModel.user_id == user_id,
                AllocationOrderModel.source_bucket == bucket,
                AllocationOrderModel.status == "queued",
            )
            .scalar()
        )
        return _decimal(value)

    def update_if_status(self, order: AllocationOrder, expected: list[str]) -> bool:
        updated = (
            self._session.query(AllocationOrderModel)
            .filter(AllocationOrderModel.id == order.id, AllocationOrderModel.status.in_(expected))
            .update(
                {
                    "status": order.status,
                    "note": order.note,
                    "settlement_id": order.settlement_id,
                    "resolved_at": order.resolved_at,
                },
                synchronize_session=False,
            )
        )
        self._session.flush()
        return updated == 1
