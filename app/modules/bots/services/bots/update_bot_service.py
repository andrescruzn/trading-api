# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/services/bots/update_bot_service.py
#
# Actualiza la configuración de un bot (solo cuando está stopped).
# ======================================================================

from __future__ import annotations

from typing import Any

from app.common.contracts import ServiceResult
from app.modules.accounts.domain.account_repository import AccountRepository
from app.modules.bots.domain.bot_entity import Bot
from app.modules.bots.domain.bot_repository import BotRepository
from app.modules.bots.services.bots.bot_access import find_accessible_bot
from app.modules.market.domain.ccxt_exchanges import is_perpetual
from app.modules.market.domain.symbol_repository import SymbolRepository


class UpdateBotService:
    """
    Actualiza la configuración de un bot existente.

    Regla de negocio:
    - El nombre se puede cambiar en cualquier estado.
    - El resto de la configuración solo si el bot está 'stopped'.
    - No se puede cambiar la cuenta, símbolo, estrategia ni timeframe
      de un bot activo (podría dejar posiciones huérfanas).
    - Un agente sobre un perpetuo no puede pasar a live.
    """

    def __init__(
        self,
        repo: BotRepository,
        account_repo: AccountRepository,
        symbol_repo: SymbolRepository,
    ):
        self._repo = repo
        self._account_repo = account_repo
        self._symbol_repo = symbol_repo

    def update(
        self,
        bot_id: int,
        name: str | None = None,
        mode: str | None = None,
        risk_params: dict[str, Any] | None = None,
        owner_id: int | None = None,
    ) -> ServiceResult[Bot]:
        bot = find_accessible_bot(self._repo, self._account_repo, bot_id, owner_id)
        if bot is None:
            return ServiceResult.fail(code="BOT_NOT_FOUND", http_status=404)

        changes_config = mode is not None or risk_params is not None
        if changes_config and bot.status != "stopped":
            return ServiceResult.fail(code="BOT_MUST_BE_STOPPED_TO_EDIT", http_status=409)

        if name is not None:
            if not name.strip():
                return ServiceResult.fail(code="BOT_INVALID_NAME", http_status=422)
            bot.name = name.strip()

        if mode is not None:
            bot.mode = mode
            if not bot.is_valid_mode():
                return ServiceResult.fail(code="BOT_INVALID_MODE", http_status=422)
            # Mismo criterio que al crear: el modo del agente es el de su cuenta
            account = self._account_repo.get_by_id(bot.account_id) if bot.account_id else None
            if account is None or account.mode != mode:
                return ServiceResult.fail(
                    code="BOT_MODE_ACCOUNT_MISMATCH",
                    http_status=422,
                    meta={"account_mode": account.mode if account else None, "bot_mode": mode},
                )
            if mode == "live":
                symbol = self._symbol_repo.get_by_id(bot.symbol_id)
                if symbol is not None and is_perpetual(symbol.symbol):
                    return ServiceResult.fail(
                        code="BOT_PERPETUAL_LIVE_NOT_SUPPORTED", http_status=422
                    )

        if risk_params is not None:
            if not Bot.is_valid_risk_pct(risk_params.get("risk_pct")):
                return ServiceResult.fail(code="BOT_INVALID_RISK_PCT", http_status=422)
            bot.risk_params = risk_params

        updated = self._repo.update(bot)
        self._repo.commit()
        return ServiceResult.ok(data=updated)
