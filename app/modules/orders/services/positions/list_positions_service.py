# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/services/positions/list_positions_service.py
#
# Lista posiciones abiertas de un bot o del sistema completo (admin).
# ======================================================================

from __future__ import annotations

from app.common.contracts import ServiceResult
from app.modules.accounts.domain.account_repository import AccountRepository
from app.modules.bots.domain.bot_repository import BotRepository
from app.modules.bots.services.bots.bot_access import find_accessible_bot
from app.modules.orders.domain.position_entity import Position
from app.modules.orders.domain.position_repository import PositionRepository


class ListPositionsService:
    """
    Lista posiciones del sistema.

    Reglas de negocio:
    - Admin (owner_id=None, bot_id=None): todas las posiciones del sistema.
    - Usuario normal: requiere bot_id, y el bot debe ser suyo (BOT_NOT_FOUND si no).
    """

    def __init__(
        self,
        repo: PositionRepository,
        bot_repo: BotRepository,
        account_repo: AccountRepository,
    ):
        self._repo = repo
        self._bot_repo = bot_repo
        self._account_repo = account_repo

    def list(
        self,
        bot_id: int | None = None,
        owner_id: int | None = None,
    ) -> ServiceResult[list[Position]]:
        if bot_id is None:
            if owner_id is not None:
                return ServiceResult.fail(code="POSITIONS_MISSING_BOT", http_status=400)
            return ServiceResult.ok(data=self._repo.list_all())

        if find_accessible_bot(self._bot_repo, self._account_repo, bot_id, owner_id) is None:
            return ServiceResult.fail(code="BOT_NOT_FOUND", http_status=404)

        return ServiceResult.ok(data=self._repo.list_by_bot(bot_id=bot_id))
