# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/infrastructure/signal_subscription_repository_impl.py
#
# Implementación SQLAlchemy del repositorio de suscripciones a señales.
# Las escrituras hacen flush; el commit lo pide el servicio.
# ======================================================================

from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.extensions.db.sqlalchemy_repository import SqlAlchemyRepository
from app.modules.bots.domain.signal_subscription_entity import SignalSubscription
from app.modules.bots.domain.signal_subscription_repository import (
    SignalSubscriptionRepository,
)
from app.modules.bots.infrastructure.signal_subscription_model import SignalSubscriptionModel


class SqlAlchemySignalSubscriptionRepository(SqlAlchemyRepository, SignalSubscriptionRepository):
    """Repositorio concreto de suscripciones usando SQLAlchemy."""

    def __init__(self, session: Session):
        super().__init__(session)

    @staticmethod
    def _to_domain(model: SignalSubscriptionModel) -> SignalSubscription:
        return SignalSubscription(
            id=model.id,
            bot_id=model.bot_id,
            user_id=model.user_id,
            created_at=model.created_at,
        )

    def list_by_bot(self, bot_id: int) -> list[SignalSubscription]:
        models = (
            self._session.query(SignalSubscriptionModel)
            .filter(SignalSubscriptionModel.bot_id == bot_id)
            .order_by(SignalSubscriptionModel.id)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def list_bot_ids_by_user(self, user_id: int) -> list[int]:
        rows = (
            self._session.query(SignalSubscriptionModel.bot_id)
            .filter(SignalSubscriptionModel.user_id == user_id)
            .all()
        )
        return [row[0] for row in rows]

    def count_by_bot_ids(self, bot_ids: list[int]) -> dict[int, int]:
        if not bot_ids:
            return {}
        rows = (
            self._session.query(
                SignalSubscriptionModel.bot_id,
                func.count(SignalSubscriptionModel.id),
            )
            .filter(SignalSubscriptionModel.bot_id.in_(bot_ids))
            .group_by(SignalSubscriptionModel.bot_id)
            .all()
        )
        return {bot_id: int(total) for bot_id, total in rows}

    def exists(self, bot_id: int, user_id: int) -> bool:
        return (
            self._session.query(SignalSubscriptionModel.id)
            .filter(
                SignalSubscriptionModel.bot_id == bot_id,
                SignalSubscriptionModel.user_id == user_id,
            )
            .first()
            is not None
        )

    def create(self, subscription: SignalSubscription) -> SignalSubscription:
        model = SignalSubscriptionModel(
            bot_id=subscription.bot_id,
            user_id=subscription.user_id,
        )
        self._session.add(model)
        try:
            self._session.flush()
        except IntegrityError:
            # Doble clic: otra petición creó la misma suscripción (UNIQUE
            # bot_id + user_id). Se devuelve la existente en vez de un 500.
            self._session.rollback()
            existing = (
                self._session.query(SignalSubscriptionModel)
                .filter(
                    SignalSubscriptionModel.bot_id == subscription.bot_id,
                    SignalSubscriptionModel.user_id == subscription.user_id,
                )
                .one()
            )
            return self._to_domain(existing)
        self._session.refresh(model)
        return self._to_domain(model)

    def delete(self, bot_id: int, user_id: int) -> bool:
        deleted = (
            self._session.query(SignalSubscriptionModel)
            .filter(
                SignalSubscriptionModel.bot_id == bot_id,
                SignalSubscriptionModel.user_id == user_id,
            )
            .delete(synchronize_session=False)
        )
        self._session.flush()
        return deleted > 0
