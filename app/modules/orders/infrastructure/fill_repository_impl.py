# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/infrastructure/fill_repository_impl.py
#
# Implementación SQLAlchemy del repositorio de fills.
# ======================================================================

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app.modules.orders.domain.fill_entity import Fill
from app.modules.orders.domain.fill_repository import FillRepository
from app.modules.orders.infrastructure.fill_model import FillModel
from app.modules.orders.infrastructure.order_model import OrderModel


class SqlAlchemyFillRepository(FillRepository):
    """Repositorio concreto de fills usando SQLAlchemy."""

    def __init__(self, session: Session):
        self._session = session

    # ------------------------------------------------------------------
    # Mappers ORM ↔ Dominio
    # ------------------------------------------------------------------

    @staticmethod
    def _to_domain(model: FillModel) -> Fill:
        return Fill(
            id=model.id,
            order_id=model.order_id,
            exchange_trade_id=model.exchange_trade_id,
            qty=Decimal(str(model.qty)),
            price=Decimal(str(model.price)),
            fee=Decimal(str(model.fee)),
            fee_asset=model.fee_asset,
            ts=model.ts,
            created_at=model.created_at,
        )

    @staticmethod
    def _apply_domain_to_model(fill: Fill, model: FillModel) -> FillModel:
        model.order_id          = fill.order_id
        model.exchange_trade_id = fill.exchange_trade_id
        model.qty               = fill.qty
        model.price             = fill.price
        model.fee               = fill.fee
        model.fee_asset         = fill.fee_asset
        model.ts                = fill.ts
        return model

    # ------------------------------------------------------------------
    # Contrato del repositorio
    # ------------------------------------------------------------------

    def list_by_order(self, order_id: int) -> list[Fill]:
        models = (
            self._session.query(FillModel)
            .filter(FillModel.order_id == order_id)
            .order_by(FillModel.ts.asc())
            .all()
        )
        return [self._to_domain(m) for m in models]

    def list_by_bot(self, bot_id: int, limit: int = 200) -> list[Fill]:
        """
        Lista fills de un bot haciendo JOIN con orders.
        Los fills no tienen bot_id directamente — se llega via order.bot_id.
        """
        models = (
            self._session.query(FillModel)
            .join(OrderModel, FillModel.order_id == OrderModel.id)
            .filter(OrderModel.bot_id == bot_id)
            .order_by(FillModel.ts.desc())
            .limit(limit)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def create(self, fill: Fill) -> Fill:
        model = FillModel()
        self._apply_domain_to_model(fill, model)
        self._session.add(model)
        self._session.flush()
        self._session.refresh(model)
        return self._to_domain(model)
