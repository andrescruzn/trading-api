# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/infrastructure/signal_repository_impl.py
#
# Implementación SQLAlchemy del repositorio de signals.
# ======================================================================

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.modules.bots.domain.signal_entity import Signal
from app.modules.bots.domain.signal_repository import SignalRepository
from app.modules.bots.infrastructure.signal_model import SignalModel


class SqlAlchemySignalRepository(SignalRepository):
    """Repositorio concreto de signals usando SQLAlchemy."""

    def __init__(self, session: Session):
        self._session = session

    # ------------------------------------------------------------------
    # Mapper: ORM model → entidad de dominio
    # ------------------------------------------------------------------

    @staticmethod
    def _to_domain(model: SignalModel) -> Signal:
        return Signal(
            id=model.id,
            bot_id=model.bot_id,
            ts=model.ts,
            action=model.action,
            approved=bool(model.approved),
            reasons=model.reasons or {},
            confidence=Decimal(str(model.confidence)) if model.confidence is not None else None,
            entry_price=Decimal(str(model.entry_price)) if model.entry_price is not None else None,
            stop_loss=Decimal(str(model.stop_loss)) if model.stop_loss is not None else None,
            take_profit=Decimal(str(model.take_profit)) if model.take_profit is not None else None,
            position_size=Decimal(str(model.position_size)) if model.position_size is not None else None,
            rr_ratio=Decimal(str(model.rr_ratio)) if model.rr_ratio is not None else None,
            model_version=model.model_version,
            features_hash=model.features_hash,
            created_at=model.created_at,
        )

    @staticmethod
    def _apply_domain_to_model(signal: Signal, model: SignalModel) -> SignalModel:
        model.bot_id        = signal.bot_id
        model.ts            = signal.ts
        model.action        = signal.action
        model.approved      = 1 if signal.approved else 0
        model.reasons       = signal.reasons
        model.confidence    = signal.confidence
        model.entry_price   = signal.entry_price
        model.stop_loss     = signal.stop_loss
        model.take_profit   = signal.take_profit
        model.position_size = signal.position_size
        model.rr_ratio      = signal.rr_ratio
        model.model_version = signal.model_version
        model.features_hash = signal.features_hash
        return model

    # ------------------------------------------------------------------
    # Contrato
    # ------------------------------------------------------------------

    def get_by_id(self, signal_id: int) -> Signal | None:
        model: SignalModel | None = self._session.get(SignalModel, signal_id)
        return None if model is None else self._to_domain(model)

    def list_by_bot(
        self,
        bot_id: int,
        action: str | None = None,
        from_ts: datetime | None = None,
        to_ts: datetime | None = None,
        limit: int = 50,
    ) -> list[Signal]:
        query = (
            self._session.query(SignalModel)
            .filter(SignalModel.bot_id == bot_id)
        )

        if action is not None:
            query = query.filter(SignalModel.action == action)
        if from_ts is not None:
            query = query.filter(SignalModel.ts >= from_ts)
        if to_ts is not None:
            query = query.filter(SignalModel.ts <= to_ts)

        # Límite máximo 500 para evitar queries costosas
        safe_limit = min(limit, 500)

        models = query.order_by(SignalModel.ts.desc()).limit(safe_limit).all()
        return [self._to_domain(m) for m in models]

    def create(self, signal: Signal) -> Signal:
        model = SignalModel()
        self._apply_domain_to_model(signal, model)
        self._session.add(model)
        self._session.flush()
        self._session.refresh(model)
        return self._to_domain(model)
