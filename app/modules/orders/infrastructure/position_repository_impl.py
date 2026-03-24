# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/infrastructure/position_repository_impl.py
#
# Implementación SQLAlchemy del repositorio de posiciones.
# ======================================================================

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app.modules.orders.domain.position_entity import Position
from app.modules.orders.domain.position_repository import PositionRepository
from app.modules.orders.infrastructure.position_model import PositionModel


class SqlAlchemyPositionRepository(PositionRepository):
    """Repositorio concreto de posiciones usando SQLAlchemy."""

    def __init__(self, session: Session):
        self._session = session

    # ------------------------------------------------------------------
    # Mappers ORM ↔ Dominio
    # ------------------------------------------------------------------

    @staticmethod
    def _to_domain(model: PositionModel) -> Position:
        return Position(
            id=model.id,
            bot_id=model.bot_id,
            symbol_id=model.symbol_id,
            qty=Decimal(str(model.qty)),
            avg_price=Decimal(str(model.avg_price)),
            realized_pnl=Decimal(str(model.realized_pnl)),
            updated_at=model.updated_at,
        )

    @staticmethod
    def _apply_domain_to_model(position: Position, model: PositionModel) -> PositionModel:
        model.bot_id        = position.bot_id
        model.symbol_id     = position.symbol_id
        model.qty           = position.qty
        model.avg_price     = position.avg_price
        model.realized_pnl  = position.realized_pnl
        return model

    # ------------------------------------------------------------------
    # Contrato del repositorio
    # ------------------------------------------------------------------

    def get_by_bot_and_symbol(self, bot_id: int, symbol_id: int) -> Position | None:
        model: PositionModel | None = (
            self._session.query(PositionModel)
            .filter(
                PositionModel.bot_id == bot_id,
                PositionModel.symbol_id == symbol_id,
            )
            .first()
        )
        return None if model is None else self._to_domain(model)

    def list_by_bot(self, bot_id: int) -> list[Position]:
        models = (
            self._session.query(PositionModel)
            .filter(PositionModel.bot_id == bot_id)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def list_all(self) -> list[Position]:
        models = self._session.query(PositionModel).all()
        return [self._to_domain(m) for m in models]

    def create(self, position: Position) -> Position:
        model = PositionModel()
        self._apply_domain_to_model(position, model)
        self._session.add(model)
        self._session.flush()
        self._session.refresh(model)
        return self._to_domain(model)

    def update(self, position: Position) -> Position:
        model: PositionModel | None = self._session.get(PositionModel, position.id)
        if model is None:
            raise ValueError(f"Position not found for update: id={position.id}")
        self._apply_domain_to_model(position, model)
        self._session.flush()
        self._session.refresh(model)
        return self._to_domain(model)
