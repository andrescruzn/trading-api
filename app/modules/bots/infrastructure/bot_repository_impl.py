# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/infrastructure/bot_repository_impl.py
#
# Implementación SQLAlchemy del repositorio de bots.
# ======================================================================

from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Query, Session

from app.modules.bots.domain.bot_entity import Bot
from app.modules.bots.domain.bot_repository import BotCriteria, BotRepository
from app.modules.bots.infrastructure.bot_model import BotModel
from app.extensions.db.sqlalchemy_repository import SqlAlchemyRepository


class SqlAlchemyBotRepository(SqlAlchemyRepository, BotRepository):
    """Repositorio concreto de bots usando SQLAlchemy."""

    def __init__(self, session: Session):
        self._session = session

    # ------------------------------------------------------------------
    # Mapper: ORM model → entidad de dominio
    # ------------------------------------------------------------------

    @staticmethod
    def _to_domain(model: BotModel) -> Bot:
        return Bot(
            id=model.id,
            name=model.name,
            strategy_id=model.strategy_id,
            symbol_id=model.symbol_id,
            timeframe_id=model.timeframe_id,
            account_id=model.account_id,
            feature_set_id=model.feature_set_id,
            mode=model.mode,
            status=model.status,
            risk_params=model.risk_params or {},
            started_at=model.started_at,
            stopped_at=model.stopped_at,
            created_at=model.created_at,
            execution_mode=model.execution_mode or "manual",
            approval_ttl_minutes=model.approval_ttl_minutes,
            share_signals=bool(model.share_signals),
        )

    @staticmethod
    def _apply_domain_to_model(bot: Bot, model: BotModel) -> BotModel:
        model.name         = bot.name
        model.strategy_id  = bot.strategy_id
        model.symbol_id    = bot.symbol_id
        model.timeframe_id = bot.timeframe_id
        model.account_id   = bot.account_id
        model.feature_set_id = bot.feature_set_id
        model.mode         = bot.mode
        model.status       = bot.status
        model.risk_params  = bot.risk_params
        model.started_at   = bot.started_at
        model.stopped_at   = bot.stopped_at
        model.execution_mode = bot.execution_mode
        model.approval_ttl_minutes = bot.approval_ttl_minutes
        model.share_signals = bool(bot.share_signals)
        return model

    # ------------------------------------------------------------------
    # Contrato
    # ------------------------------------------------------------------

    def get_by_id(self, bot_id: int) -> Bot | None:
        model: BotModel | None = self._session.get(BotModel, bot_id)
        return None if model is None else self._to_domain(model)

    def list_by_account(self, account_id: int) -> list[Bot]:
        models = (
            self._session.query(BotModel)
            .filter(BotModel.account_id == account_id)
            .order_by(BotModel.created_at.desc())
            .all()
        )
        return [self._to_domain(m) for m in models]

    def list_by_account_ids(self, account_ids: list[int]) -> list[Bot]:
        if not account_ids:
            return []
        models = (
            self._session.query(BotModel)
            .filter(BotModel.account_id.in_(account_ids))
            .order_by(BotModel.created_at.desc())
            .all()
        )
        return [self._to_domain(m) for m in models]

    def list_all(self) -> list[Bot]:
        models = (
            self._session.query(BotModel)
            .order_by(BotModel.created_at.desc())
            .all()
        )
        return [self._to_domain(m) for m in models]

    @staticmethod
    def _apply_criteria(query: Query, criteria: BotCriteria) -> Query:
        if criteria.account_ids is not None:
            query = query.filter(BotModel.account_id.in_(criteria.account_ids))
        if criteria.status is not None:
            query = query.filter(BotModel.status == criteria.status)
        if criteria.mode is not None:
            query = query.filter(BotModel.mode == criteria.mode)
        return query

    def search(
        self, criteria: BotCriteria, offset: int = 0, limit: int | None = None
    ) -> list[Bot]:
        # `account_ids=[]` = sin cuentas: sin consulta (IN () no es SQL válido)
        if criteria.account_ids is not None and not criteria.account_ids:
            return []
        query = self._apply_criteria(self._session.query(BotModel), criteria).order_by(
            BotModel.created_at.desc(), BotModel.id.desc()
        )
        if offset > 0:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)
        return [self._to_domain(m) for m in query.all()]

    def count(self, criteria: BotCriteria) -> int:
        if criteria.account_ids is not None and not criteria.account_ids:
            return 0
        query = self._apply_criteria(self._session.query(func.count(BotModel.id)), criteria)
        return int(query.scalar() or 0)

    def list_by_statuses(self, statuses: list[str]) -> list[Bot]:
        models = (
            self._session.query(BotModel)
            .filter(BotModel.status.in_(statuses))
            .all()
        )
        return [self._to_domain(m) for m in models]

    def list_shared(self) -> list[Bot]:
        models = (
            self._session.query(BotModel)
            .filter(BotModel.share_signals.is_(True))
            .order_by(BotModel.created_at.desc())
            .all()
        )
        return [self._to_domain(m) for m in models]

    def create(self, bot: Bot) -> Bot:
        model = BotModel()
        self._apply_domain_to_model(bot, model)
        self._session.add(model)
        self._session.flush()
        self._session.refresh(model)
        return self._to_domain(model)

    def update(self, bot: Bot) -> Bot:
        model: BotModel | None = self._session.get(BotModel, bot.id)
        if model is None:
            raise ValueError(f"Bot not found for update: id={bot.id}")
        self._apply_domain_to_model(bot, model)
        self._session.flush()
        self._session.refresh(model)
        return self._to_domain(model)
