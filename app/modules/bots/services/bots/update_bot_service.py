# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/services/bots/update_bot_service.py
#
# Actualiza la configuración de un bot (solo cuando está stopped).
# ======================================================================

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.common.contracts import ServiceResult
from app.modules.bots.domain.bot_entity import Bot
from app.modules.bots.domain.bot_repository import BotRepository


class UpdateBotService:
    """
    Actualiza la configuración de un bot existente.

    Regla de negocio:
    - Solo se puede editar un bot si está en estado 'stopped'.
    - No se puede cambiar la cuenta, símbolo, estrategia ni timeframe
      de un bot activo (podría dejar posiciones huérfanas).
    """

    def __init__(self, repo: BotRepository, session: Session):
        self._repo = repo
        self._session = session

    def update(
        self,
        bot_id: int,
        mode: str | None = None,
        risk_params: dict[str, Any] | None = None,
    ) -> ServiceResult[Bot]:
        bot = self._repo.get_by_id(bot_id)
        if bot is None:
            return ServiceResult.fail(code="BOT_NOT_FOUND", http_status=404)

        if bot.status != "stopped":
            return ServiceResult.fail(code="BOT_MUST_BE_STOPPED_TO_EDIT", http_status=409)

        if mode is not None:
            bot.mode = mode
            if not bot.is_valid_mode():
                return ServiceResult.fail(code="BOT_INVALID_MODE", http_status=422)

        if risk_params is not None:
            risk_pct = risk_params.get("risk_pct")
            if risk_pct is None or not (0 < float(risk_pct) <= 1):
                return ServiceResult.fail(code="BOT_INVALID_RISK_PCT", http_status=422)
            bot.risk_params = risk_params

        updated = self._repo.update(bot)
        self._session.commit()
        return ServiceResult.ok(data=updated)
