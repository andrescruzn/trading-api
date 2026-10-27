# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/infrastructure/bot_history_repository_impl.py
#
# Implementación SQLAlchemy del historial de los agentes sobre `audit_logs`
# (modelo en app/common/audit/audit_log_model.py).
#
# NOTAS:
# - Solo lee y escribe filas con `bot_id`; `audit_logs` no tiene otros
#   usos hoy.
# - El nombre de quien actuó sale de un LEFT JOIN a `users` (NULL = sistema).
# - Índice usado: (bot_id, ts).
# ======================================================================

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.audit.audit_log_model import AuditLogModel
from app.common.contracts import Page, PageRequest
from app.common.utils import ensure_aware_utc, utc_now
from app.extensions.db.sqlalchemy_repository import SqlAlchemyRepository
from app.modules.bots.domain.bot_history import BotHistoryEntry
from app.modules.bots.domain.bot_history_repository import BotHistoryRepository
from app.modules.users.infrastructure.user_model import UserModel


class SqlAlchemyBotHistoryRepository(SqlAlchemyRepository, BotHistoryRepository):
    """Historial de los agentes en `audit_logs`."""

    def __init__(self, session: Session):
        super().__init__(session)

    def record(
        self,
        *,
        bot_id: int,
        event_type: str,
        data: dict[str, Any],
        user_id: int | None = None,
    ) -> None:
        self._session.add(
            AuditLogModel(
                bot_id=int(bot_id),
                user_id=int(user_id) if user_id is not None else None,
                event_type=event_type,
                ts=utc_now(),
                # Decimal y fechas → texto: la columna es JSON
                data=json.loads(json.dumps(data, default=str)),
            )
        )
        self._session.flush()

    def list_by_bot(self, bot_id: int, page: PageRequest) -> Page[BotHistoryEntry]:
        total = int(
            self._session.execute(
                select(func.count())
                .select_from(AuditLogModel)
                .where(AuditLogModel.bot_id == bot_id)
            ).scalar()
            or 0
        )
        if total == 0 or page.offset >= total:
            return Page(items=[], total=total, page=page.page, page_size=page.page_size)

        rows = self._session.execute(
            select(AuditLogModel, UserModel.full_name, UserModel.email)
            .outerjoin(UserModel, UserModel.id == AuditLogModel.user_id)
            .where(AuditLogModel.bot_id == bot_id)
            .order_by(AuditLogModel.ts.desc(), AuditLogModel.id.desc())
            .offset(page.offset)
            .limit(page.limit)
        ).all()

        items = [
            BotHistoryEntry(
                id=int(model.id),
                bot_id=int(model.bot_id),
                event_type=str(model.event_type),
                ts=ensure_aware_utc(model.ts),
                data=model.data if isinstance(model.data, dict) else {},
                user_id=int(model.user_id) if model.user_id is not None else None,
                user_name=(full_name or email) if model.user_id is not None else None,
            )
            for model, full_name, email in rows
        ]
        return Page(items=items, total=total, page=page.page, page_size=page.page_size)
