# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/services/bots/list_bot_history_service.py
#
# CASO DE USO:
# - Ver el historial de un agente (pestaña Historial del detalle): quién lo
#   creó, editó, arrancó, pausó o detuvo, y cuándo lo cambió el sistema.
#
# REGLAS:
# - Mismo acceso que el detalle del agente: el dueño o el staff; un agente
#   ajeno responde BOT_NOT_FOUND (404), igual que uno inexistente.
# - Paginado en el servidor, el más reciente primero.
# ======================================================================

from __future__ import annotations

from app.common.contracts import Page, PageRequest, ServiceResult
from app.modules.accounts.domain.account_repository import AccountRepository
from app.modules.bots.domain.bot_history import BotHistoryEntry
from app.modules.bots.domain.bot_history_repository import BotHistoryRepository
from app.modules.bots.domain.bot_repository import BotRepository
from app.modules.bots.services.bots.bot_access import find_accessible_bot


class ListBotHistoryService:
    """Lista el historial de un agente."""

    def __init__(
        self,
        repo: BotRepository,
        account_repo: AccountRepository,
        history_repo: BotHistoryRepository,
    ):
        self._repo = repo
        self._account_repo = account_repo
        self._history_repo = history_repo

    def list(
        self,
        bot_id: int,
        page: PageRequest,
        owner_id: int | None = None,
    ) -> ServiceResult[Page[BotHistoryEntry]]:
        """`owner_id=None` = sin restricción de propiedad (staff)."""
        bot = find_accessible_bot(self._repo, self._account_repo, bot_id, owner_id)
        if bot is None:
            return ServiceResult.fail(code="BOT_NOT_FOUND", http_status=404)

        return ServiceResult.ok(data=self._history_repo.list_by_bot(bot.id, page))
