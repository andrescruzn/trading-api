# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/infrastructure/signal_repository_impl.py
#
# Implementación SQLAlchemy del repositorio de signals.
# ======================================================================

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Query, Session

from app.modules.bots.domain.signal_entity import Signal
from app.modules.bots.domain.signal_repository import SignalRepository
from app.modules.bots.infrastructure.signal_model import SignalModel
from app.extensions.db.sqlalchemy_repository import SqlAlchemyRepository


class SqlAlchemySignalRepository(SqlAlchemyRepository, SignalRepository):
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
            llm_provider=model.llm_provider,
            llm_model=model.llm_model,
            llm_latency_ms=model.llm_latency_ms,
            created_at=model.created_at,
            decision_status=model.decision_status or "not_required",
            expires_at=model.expires_at,
            decided_at=model.decided_at,
            decided_by_user_id=model.decided_by_user_id,
            decision_channel=model.decision_channel,
            decision_reason=model.decision_reason,
            candle_ts=model.candle_ts,
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
        model.features_hash  = signal.features_hash
        model.llm_provider   = signal.llm_provider
        model.llm_model      = signal.llm_model
        model.llm_latency_ms = signal.llm_latency_ms
        model.decision_status = signal.decision_status
        model.expires_at = signal.expires_at
        model.decided_at = signal.decided_at
        model.decided_by_user_id = signal.decided_by_user_id
        model.decision_channel = signal.decision_channel
        model.decision_reason = signal.decision_reason
        model.candle_ts = signal.candle_ts
        return model

    # ------------------------------------------------------------------
    # Contrato
    # ------------------------------------------------------------------

    def get_by_id(self, signal_id: int) -> Signal | None:
        model: SignalModel | None = self._session.get(SignalModel, signal_id)
        return None if model is None else self._to_domain(model)

    @staticmethod
    def _bot_signals_query(
        query: Query,
        bot_id: int,
        action: str | None,
        from_ts: datetime | None,
        to_ts: datetime | None,
    ) -> Query:
        query = query.filter(SignalModel.bot_id == bot_id)
        if action is not None:
            query = query.filter(SignalModel.action == action)
        if from_ts is not None:
            query = query.filter(SignalModel.ts >= from_ts)
        if to_ts is not None:
            query = query.filter(SignalModel.ts <= to_ts)
        return query

    def list_by_bot(
        self,
        bot_id: int,
        action: str | None = None,
        from_ts: datetime | None = None,
        to_ts: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Signal]:
        query = self._bot_signals_query(
            self._session.query(SignalModel), bot_id, action, from_ts, to_ts
        )

        # Límite máximo 500 para evitar queries costosas
        safe_limit = min(limit, 500)

        # id desc desempata señales del mismo instante: orden estable entre páginas
        query = query.order_by(SignalModel.ts.desc(), SignalModel.id.desc())
        if offset > 0:
            query = query.offset(offset)
        models = query.limit(safe_limit).all()
        return [self._to_domain(m) for m in models]

    def count_by_bot(
        self,
        bot_id: int,
        action: str | None = None,
        from_ts: datetime | None = None,
        to_ts: datetime | None = None,
    ) -> int:
        query = self._bot_signals_query(
            self._session.query(func.count(SignalModel.id)), bot_id, action, from_ts, to_ts
        )
        return int(query.scalar() or 0)

    def exists_for_candle(self, bot_id: int, candle_ts: datetime) -> bool:
        return (
            self._session.query(SignalModel.id)
            .filter(SignalModel.bot_id == bot_id, SignalModel.candle_ts == candle_ts)
            .first()
            is not None
        )

    def count_created_since(self, bot_ids: list[int], since: datetime) -> int:
        if not bot_ids:
            return 0
        return (
            self._session.query(func.count(SignalModel.id))
            .filter(SignalModel.bot_id.in_(bot_ids), SignalModel.created_at >= since)
            .scalar()
            or 0
        )

    def list_by_decision_status(
        self,
        decision_status: str,
        bot_ids: list[int] | None = None,
        limit: int = 100,
    ) -> list[Signal]:
        query = self._session.query(SignalModel).filter(
            SignalModel.decision_status == decision_status
        )
        if bot_ids is not None:
            if not bot_ids:
                return []
            query = query.filter(SignalModel.bot_id.in_(bot_ids))
        models = query.order_by(SignalModel.ts.desc()).limit(min(limit, 500)).all()
        return [self._to_domain(m) for m in models]

    def transition_decision(
        self,
        signal_id: int,
        from_statuses: tuple[str, ...],
        to_status: str,
        **fields: Any,
    ) -> bool:
        # UPDATE condicional: si dos personas (o la app y Telegram) deciden a
        # la vez, solo una fila cambia y solo esa decisión gana.
        values = {"decision_status": to_status, **fields}
        updated = (
            self._session.query(SignalModel)
            .filter(
                SignalModel.id == signal_id,
                SignalModel.decision_status.in_(from_statuses),
            )
            .update(values, synchronize_session=False)
        )
        return updated == 1

    def expire_pending(self, now: datetime) -> list[int]:
        ids = [
            row.id
            for row in self._session.query(SignalModel.id).filter(
                SignalModel.decision_status == "pending",
                SignalModel.expires_at.isnot(None),
                SignalModel.expires_at <= now,
            )
        ]
        if ids:
            (
                self._session.query(SignalModel)
                .filter(SignalModel.id.in_(ids), SignalModel.decision_status == "pending")
                .update({"decision_status": "expired"}, synchronize_session=False)
            )
        return ids

    def create(self, signal: Signal) -> Signal:
        model = SignalModel()
        self._apply_domain_to_model(signal, model)
        self._session.add(model)
        self._session.flush()
        self._session.refresh(model)
        return self._to_domain(model)
