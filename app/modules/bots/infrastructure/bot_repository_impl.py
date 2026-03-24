# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/infrastructure/bot_repository_impl.py
#
# Implementación SQLAlchemy del repositorio de bots.
# ======================================================================

from __future__ import annotations

from sqlalchemy.orm import Session

from app.modules.bots.domain.bot_entity import Bot
from app.modules.bots.domain.bot_repository import BotRepository
from app.modules.bots.infrastructure.bot_model import BotModel


class SqlAlchemyBotRepository(BotRepository):
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
        )

    @staticmethod
    def _apply_domain_to_model(bot: Bot, model: BotModel) -> BotModel:
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

    def list_all(self) -> list[Bot]:
        models = (
            self._session.query(BotModel)
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
