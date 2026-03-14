# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/strategies/infrastructure/strategy_repository_impl.py
#
# Implementación SQLAlchemy del repositorio de estrategias.
# ======================================================================

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.modules.strategies.domain.strategy_entity import Strategy
from app.modules.strategies.domain.strategy_repository import StrategyRepository
from app.modules.strategies.infrastructure.strategy_model import StrategyModel


class SqlAlchemyStrategyRepository(StrategyRepository):
    """Repositorio concreto de estrategias usando SQLAlchemy."""

    def __init__(self, session: Session):
        self._session = session

    # ------------------------------------------------------------------
    # Mapper
    # ------------------------------------------------------------------

    @staticmethod
    def _to_domain(model: StrategyModel) -> Strategy:
        return Strategy(
            id=model.id,
            name=model.name,
            version=model.version,
            description=model.description,
            parameters=model.parameters or {},
            created_at=model.created_at,
        )

    @staticmethod
    def _apply_domain_to_model(strategy: Strategy, model: StrategyModel) -> StrategyModel:
        model.name = strategy.name
        model.version = strategy.version
        model.description = strategy.description
        model.parameters = strategy.parameters
        return model

    # ------------------------------------------------------------------
    # Contract
    # ------------------------------------------------------------------

    def get_by_id(self, strategy_id: int) -> Optional[Strategy]:
        model: Optional[StrategyModel] = self._session.get(StrategyModel, strategy_id)
        return None if model is None else self._to_domain(model)

    def get_by_name_version(self, name: str, version: str) -> Optional[Strategy]:
        model = (
            self._session.query(StrategyModel)
            .filter(StrategyModel.name == name, StrategyModel.version == version)
            .first()
        )
        return None if model is None else self._to_domain(model)

    def list_all(self) -> list[Strategy]:
        models = (
            self._session.query(StrategyModel)
            .order_by(StrategyModel.created_at.desc())
            .all()
        )
        return [self._to_domain(m) for m in models]

    def create(self, strategy: Strategy) -> Strategy:
        model = StrategyModel()
        self._apply_domain_to_model(strategy, model)
        self._session.add(model)
        self._session.flush()
        self._session.refresh(model)
        return self._to_domain(model)

    def update(self, strategy: Strategy) -> Strategy:
        model: Optional[StrategyModel] = self._session.get(StrategyModel, strategy.id)
        if model is None:
            raise ValueError(f"Strategy not found for update: id={strategy.id}")
        self._apply_domain_to_model(strategy, model)
        self._session.flush()
        self._session.refresh(model)
        return self._to_domain(model)
