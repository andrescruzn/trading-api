# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/agent/infrastructure/market_recommendation_repository_impl.py
#
# Implementación SQLAlchemy del repositorio de recomendaciones de mercados.
# ======================================================================

from __future__ import annotations

from sqlalchemy.orm import Session

from app.common.utils import ensure_aware_utc
from app.extensions.db.sqlalchemy_repository import SqlAlchemyRepository
from app.modules.agent.domain.market_recommendation_entity import (
    MarketRecommendation,
    RecommendationItem,
)
from app.modules.agent.domain.market_recommendation_repository import (
    MarketRecommendationRepository,
)
from app.modules.agent.infrastructure.market_recommendation_model import MarketRecommendationORM


class SqlAlchemyMarketRecommendationRepository(SqlAlchemyRepository, MarketRecommendationRepository):
    """Repositorio concreto de recomendaciones de mercados usando SQLAlchemy."""

    def __init__(self, session: Session):
        self._session = session

    # ------------------------------------------------------------------
    # Mapper: ORM → Domain
    # ------------------------------------------------------------------

    @staticmethod
    def _to_domain(orm: MarketRecommendationORM) -> MarketRecommendation:
        return MarketRecommendation(
            id=orm.id,
            created_by_user_id=orm.created_by_user_id,
            asset_class=orm.asset_class,
            summary=orm.summary,
            items=[RecommendationItem.from_dict(item) for item in (orm.items or [])],
            market_snapshot=orm.market_snapshot or {},
            llm_provider=orm.llm_provider,
            llm_model=orm.llm_model,
            llm_latency_ms=orm.llm_latency_ms,
            created_at=ensure_aware_utc(orm.created_at) if orm.created_at else None,
        )

    # ------------------------------------------------------------------
    # Contract
    # ------------------------------------------------------------------

    def create(self, recommendation: MarketRecommendation) -> MarketRecommendation:
        orm = MarketRecommendationORM(
            created_by_user_id=recommendation.created_by_user_id,
            asset_class=recommendation.asset_class,
            summary=recommendation.summary,
            items=[item.to_dict() for item in recommendation.items],
            market_snapshot=recommendation.market_snapshot,
            llm_provider=recommendation.llm_provider,
            llm_model=recommendation.llm_model,
            llm_latency_ms=recommendation.llm_latency_ms,
        )
        self._session.add(orm)
        self._session.flush()
        self._session.refresh(orm)
        return self._to_domain(orm)

    def get_latest(self) -> MarketRecommendation | None:
        orm = (
            self._session.query(MarketRecommendationORM)
            .order_by(MarketRecommendationORM.created_at.desc(), MarketRecommendationORM.id.desc())
            .first()
        )
        return None if orm is None else self._to_domain(orm)
