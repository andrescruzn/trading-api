# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/market/infrastructure/timeframe_repository_impl.py
#
# Implementación SQLAlchemy del repositorio de timeframes.
# ======================================================================

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.modules.market.domain.timeframe_entity import Timeframe
from app.modules.market.domain.timeframe_repository import TimeframeRepository
from app.modules.market.infrastructure.timeframe_model import TimeframeModel


class SqlAlchemyTimeframeRepository(TimeframeRepository):
    """Repositorio concreto de timeframes usando SQLAlchemy."""

    def __init__(self, session: Session):
        self._session = session

    # ==================================================================
    # Mappers
    # ==================================================================

    @staticmethod
    def _to_domain(model: TimeframeModel) -> Timeframe:
        return Timeframe(
            id=model.id,
            code=model.code,
            seconds=model.seconds,
        )

    # ==================================================================
    # Contract
    # ==================================================================

    def get_by_id(self, timeframe_id: int) -> Optional[Timeframe]:
        model: Optional[TimeframeModel] = self._session.get(TimeframeModel, timeframe_id)
        return None if model is None else self._to_domain(model)

    def get_by_code(self, code: str) -> Optional[Timeframe]:
        model: Optional[TimeframeModel] = (
            self._session.query(TimeframeModel)
            .filter(TimeframeModel.code == code)
            .one_or_none()
        )
        return None if model is None else self._to_domain(model)

    def list_all(self) -> list[Timeframe]:
        models = (
            self._session.query(TimeframeModel)
            .order_by(TimeframeModel.seconds)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def create(self, timeframe: Timeframe) -> Timeframe:
        model = TimeframeModel()
        model.code = timeframe.code
        model.seconds = timeframe.seconds
        self._session.add(model)
        self._session.flush()
        self._session.refresh(model)
        return self._to_domain(model)
