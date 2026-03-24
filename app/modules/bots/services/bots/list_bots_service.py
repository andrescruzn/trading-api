# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/services/bots/list_bots_service.py
#
# Lista bots. Los admins ven todos; los usuarios ven solo los de sus cuentas.
# ======================================================================

from __future__ import annotations

from app.common.contracts import ServiceResult
from app.modules.bots.domain.bot_entity import Bot
from app.modules.bots.domain.bot_repository import BotRepository


class ListBotsService:
    """
    Lista bots del sistema.

    Reglas de negocio:
    - Admin (account_id=None): retorna todos los bots del sistema.
    - Usuario normal: retorna solo los bots asociados a su cuenta.
    """

    def __init__(self, repo: BotRepository):
        self._repo = repo

    def list(self, account_id: int | None = None) -> ServiceResult[list[Bot]]:
        if account_id is not None:
            bots = self._repo.list_by_account(account_id=account_id)
        else:
            bots = self._repo.list_all()

        return ServiceResult.ok(data=bots)
