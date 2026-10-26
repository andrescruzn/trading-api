# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/services/bots/update_bot_service.py
#
# Actualiza la configuración de un bot. Nombre, modo de ejecución y
# compartir señales en cualquier estado; riesgo solo con el bot stopped.
# Real (live) o demo (paper) no se cambia: se decide al crear el agente.
# ======================================================================

from __future__ import annotations

from typing import Any

from app.common.contracts import ServiceResult
from app.modules.accounts.domain.account_repository import AccountRepository
from app.modules.bots.domain.bot_entity import Bot
from app.modules.bots.domain.bot_repository import BotRepository
from app.modules.bots.services.bots.bot_access import find_accessible_bot
from app.modules.bots.services.bots.execution_mode_rules import check_execution_mode
from app.modules.market.domain.timeframe_repository import TimeframeRepository


class UpdateBotService:
    """
    Actualiza la configuración de un bot existente.

    Regla de negocio:
    - El nombre, el modo de ejecución y `share_signals` se pueden cambiar
      en cualquier estado.
    - El resto de la configuración solo si el bot está 'stopped'.
    - Nunca se cambia el modo (real o demo), la cuenta, el símbolo, la
      estrategia ni el timeframe: un demo no se vuelve real ni al revés, y
      cambiar el resto podría dejar posiciones huérfanas.
    """

    def __init__(
        self,
        repo: BotRepository,
        account_repo: AccountRepository,
        timeframe_repo: TimeframeRepository,
    ):
        self._repo = repo
        self._account_repo = account_repo
        self._timeframe_repo = timeframe_repo

    def update(
        self,
        bot_id: int,
        name: str | None = None,
        risk_params: dict[str, Any] | None = None,
        owner_id: int | None = None,
        execution_mode: str | None = None,
        approval_ttl_minutes: int | None = None,
        clear_approval_ttl: bool = False,
        share_signals: bool | None = None,
    ) -> ServiceResult[Bot]:
        bot = find_accessible_bot(self._repo, self._account_repo, bot_id, owner_id)
        if bot is None:
            return ServiceResult.fail(code="BOT_NOT_FOUND", http_status=404)

        if risk_params is not None and bot.status != "stopped":
            return ServiceResult.fail(code="BOT_MUST_BE_STOPPED_TO_EDIT", http_status=409)

        if name is not None:
            if not name.strip():
                return ServiceResult.fail(code="BOT_INVALID_NAME", http_status=422)
            bot.name = name.strip()

        if risk_params is not None:
            if not Bot.is_valid_risk_pct(risk_params.get("risk_pct")):
                return ServiceResult.fail(code="BOT_INVALID_RISK_PCT", http_status=422)
            bot.risk_params = risk_params

        # El modo de ejecución se cambia en cualquier estado: pasar de auto a
        # approval (o manual) es un freno que no debe esperar a detener el agente
        if execution_mode is not None:
            bot.execution_mode = execution_mode
        if approval_ttl_minutes is not None or clear_approval_ttl:
            bot.approval_ttl_minutes = approval_ttl_minutes

        # Compartir señales no toca la operación del agente: cualquier estado.
        # Al apagarlo las suscripciones se conservan, pero el aviso deja de
        # salir (el hook mira share_signals) y el agente sale del listado.
        if share_signals is not None:
            bot.share_signals = share_signals

        timeframe = self._timeframe_repo.get_by_id(bot.timeframe_id)
        execution_check = check_execution_mode(bot, timeframe.seconds if timeframe else None)
        if not execution_check.success:
            return execution_check

        updated = self._repo.update(bot)
        self._repo.commit()
        return ServiceResult.ok(data=updated)
