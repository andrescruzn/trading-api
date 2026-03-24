# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/infrastructure/order_repository_impl.py
#
# Implementación SQLAlchemy del repositorio de órdenes.
# ======================================================================

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app.modules.orders.domain.order_entity import Order
from app.modules.orders.domain.order_repository import OrderRepository
from app.modules.orders.infrastructure.order_model import OrderModel


class SqlAlchemyOrderRepository(OrderRepository):
    """Repositorio concreto de órdenes usando SQLAlchemy."""

    def __init__(self, session: Session):
        self._session = session

    # ------------------------------------------------------------------
    # Mappers ORM ↔ Dominio
    # ------------------------------------------------------------------

    @staticmethod
    def _to_domain(model: OrderModel) -> Order:
        """
        Convierte un modelo ORM → entidad de dominio.

        Nota: los valores NUMERIC de MySQL pueden llegar como Decimal
        con precisión irregular. Convertir via str() garantiza que
        Decimal("0.5") no sea Decimal("0.500000000000") con artefactos.
        """
        return Order(
            id=model.id,
            bot_id=model.bot_id,
            signal_id=model.signal_id,
            exchange_order_id=model.exchange_order_id,
            side=model.side,
            type=model.type,
            status=model.status,
            qty=Decimal(str(model.qty)),
            price=Decimal(str(model.price)) if model.price is not None else None,
            stop_price=Decimal(str(model.stop_price)) if model.stop_price is not None else None,
            time_in_force=model.time_in_force,
            meta=model.meta or {},
            ts=model.ts,
            created_at=model.created_at,
        )

    @staticmethod
    def _apply_domain_to_model(order: Order, model: OrderModel) -> OrderModel:
        """Aplica los campos de la entidad de dominio al modelo ORM."""
        model.bot_id            = order.bot_id
        model.signal_id         = order.signal_id
        model.exchange_order_id = order.exchange_order_id
        model.side              = order.side
        model.type              = order.type
        model.status            = order.status
        model.qty               = order.qty
        model.price             = order.price
        model.stop_price        = order.stop_price
        model.time_in_force     = order.time_in_force
        model.meta              = order.meta
        model.ts                = order.ts
        return model

    # ------------------------------------------------------------------
    # Contrato del repositorio
    # ------------------------------------------------------------------

    def get_by_id(self, order_id: int) -> Order | None:
        model: OrderModel | None = self._session.get(OrderModel, order_id)
        return None if model is None else self._to_domain(model)

    def list_by_bot(self, bot_id: int, limit: int = 100) -> list[Order]:
        models = (
            self._session.query(OrderModel)
            .filter(OrderModel.bot_id == bot_id)
            .order_by(OrderModel.ts.desc())
            .limit(limit)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def list_all(self, limit: int = 200) -> list[Order]:
        models = (
            self._session.query(OrderModel)
            .order_by(OrderModel.ts.desc())
            .limit(limit)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def create(self, order: Order) -> Order:
        model = OrderModel()
        self._apply_domain_to_model(order, model)
        self._session.add(model)
        self._session.flush()         # genera el ID auto-increment
        self._session.refresh(model)  # recarga ts y created_at del servidor
        return self._to_domain(model)

    def update(self, order: Order) -> Order:
        model: OrderModel | None = self._session.get(OrderModel, order.id)
        if model is None:
            raise ValueError(f"Order not found for update: id={order.id}")
        self._apply_domain_to_model(order, model)
        self._session.flush()
        self._session.refresh(model)
        return self._to_domain(model)
