# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/services/signals/list_signals_service.py
# ======================================================================

from __future__ import annotations

from datetime import datetime

from app.common.contracts import ServiceResult
from app.modules.bots.domain.signal_entity import Signal
from app.modules.bots.domain.signal_repository import SignalRepository


class ListSignalsService:
    """Lista signals de un bot con filtros opcionales."""

    def __init__(self, repo: SignalRepository):
        self._repo = repo

    def list(
        self,
        bot_id: int,
        action: str | None = None,
        from_ts: datetime | None = None,
        to_ts: datetime | None = None,
        limit: int = 50,
    ) -> ServiceResult[list[Signal]]:
        if action is not None and action not in Signal.VALID_ACTIONS:
            return ServiceResult.fail(code="SIGNAL_INVALID_ACTION_FILTER", http_status=422)

        signals = self._repo.list_by_bot(
            bot_id=bot_id,
            action=action,
            from_ts=from_ts,
            to_ts=to_ts,
            limit=min(limit, 500),
        )
        return ServiceResult.ok(data=signals)
