# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/services/bots/list_bots_service.py
#
# Lista bots. Los admins ven todos; los usuarios ven solo los de sus cuentas.
# ======================================================================

from __future__ import annotations

from app.common.contracts import ServiceResult
from app.modules.accounts.domain.account_repository import AccountRepository
from app.modules.bots.domain.bot_entity import Bot
from app.modules.bots.domain.bot_repository import BotRepository


class ListBotsService:
    """
    Lista bots del sistema.

    Reglas de negocio:
    - Admin (owner_id=None): todos los bots, o los de `account_id`.
    - Usuario: solo los bots de sus cuentas; con `account_id`, solo si
      esa cuenta es suya (si no, lista vacía).
    """

    def __init__(self, repo: BotRepository, account_repo: AccountRepository):
        self._repo = repo
        self._account_repo = account_repo

    def list(
        self,
        account_id: int | None = None,
        owner_id: int | None = None,
    ) -> ServiceResult[list[Bot]]:
        if owner_id is None:
            if account_id is not None:
                return ServiceResult.ok(data=self._repo.list_by_account(account_id=account_id))
            return ServiceResult.ok(data=self._repo.list_all())

        own_ids = [a.id for a in self._account_repo.list_by_user_id(owner_id)]
        if account_id is not None:
            own_ids = [account_id] if account_id in own_ids else []
        return ServiceResult.ok(data=self._repo.list_by_account_ids(own_ids))
