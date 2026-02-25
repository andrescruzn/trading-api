# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/market/infrastructure/exchange_repository_impl.py
#
# Implementación SQLAlchemy del repositorio de exchanges.
# ======================================================================

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.modules.market.domain.exchange_entity import Exchange
from app.modules.market.domain.exchange_repository import ExchangeRepository
from app.modules.market.infrastructure.exchange_model import ExchangeModel


class SqlAlchemyExchangeRepository(ExchangeRepository):
    """Repositorio concreto de exchanges usando SQLAlchemy."""

    def __init__(self, session: Session):
        self._session = session

    # ==================================================================
    # Mappers
    # ==================================================================

    @staticmethod
    def _to_domain(model: ExchangeModel) -> Exchange:
        return Exchange(
            id=model.id,
            name=model.name,
            type=model.type,
            is_active=bool(model.is_active),
            created_at=model.created_at,
        )

    @staticmethod
    def _apply_domain_to_model(exchange: Exchange, model: ExchangeModel) -> ExchangeModel:
        model.name = exchange.name
        model.type = exchange.type
        model.is_active = exchange.is_active
        return model

    # ==================================================================
    # Contract
    # ==================================================================

    def get_by_id(self, exchange_id: int) -> Optional[Exchange]:
        model: Optional[ExchangeModel] = self._session.get(ExchangeModel, exchange_id)
        return None if model is None else self._to_domain(model)

    def get_by_name(self, name: str) -> Optional[Exchange]:
        model: Optional[ExchangeModel] = (
            self._session.query(ExchangeModel)
            .filter(ExchangeModel.name == name)
            .one_or_none()
        )
        return None if model is None else self._to_domain(model)

    def list_all(self, is_active: Optional[bool] = None) -> list[Exchange]:
        query = self._session.query(ExchangeModel)
        if is_active is not None:
            query = query.filter(ExchangeModel.is_active == is_active)
        query = query.order_by(ExchangeModel.name)
        return [self._to_domain(m) for m in query.all()]

    def create(self, exchange: Exchange) -> Exchange:
        model = ExchangeModel()
        self._apply_domain_to_model(exchange, model)
        self._session.add(model)
        self._session.flush()
        self._session.refresh(model)
        return self._to_domain(model)

    def update(self, exchange: Exchange) -> Exchange:
        model: Optional[ExchangeModel] = self._session.get(ExchangeModel, exchange.id)
        if model is None:
            raise ValueError(f"Exchange not found for update: id={exchange.id}")
        self._apply_domain_to_model(exchange, model)
        self._session.flush()
        self._session.refresh(model)
        return self._to_domain(model)
