# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/services/bots/create_bot_service.py
#
# Crea un nuevo bot vinculando cuenta, símbolo, estrategia y timeframe.
# ======================================================================

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.common.contracts import ServiceResult
from app.modules.bots.domain.bot_entity import Bot
from app.modules.bots.domain.bot_repository import BotRepository


class CreateBotService:
    """
    Crea un nuevo bot de trading.

    Reglas de negocio:
    - El mode debe ser 'paper' o 'live'.
    - risk_pct en risk_params debe ser > 0 y <= 1 (entre 0% y 100%).
    - El bot siempre inicia en estado 'stopped'.
    """

    def __init__(self, repo: BotRepository, session: Session):
        self._repo = repo
        self._session = session

    def create(
        self,
        strategy_id: int,
        symbol_id: int,
        timeframe_id: int,
        account_id: int,
        feature_set_id: int,
        mode: str,
        risk_params: dict[str, Any],
    ) -> ServiceResult[Bot]:
        bot = Bot(
            id=0,
            strategy_id=strategy_id,
            symbol_id=symbol_id,
            timeframe_id=timeframe_id,
            account_id=account_id,
            feature_set_id=feature_set_id,
            mode=mode,
            status="stopped",
            risk_params=risk_params,
        )

        if not bot.is_valid_mode():
            return ServiceResult.fail(code="BOT_INVALID_MODE", http_status=422)

        risk_pct = risk_params.get("risk_pct")
        if risk_pct is None or not (0 < float(risk_pct) <= 1):
            return ServiceResult.fail(code="BOT_INVALID_RISK_PCT", http_status=422)

        created = self._repo.create(bot)
        self._session.commit()
        return ServiceResult.ok(data=created)
