# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/bots/services/bots/list_bots_service.py
#
# Lista bots. Los admins ven todos; los usuarios ven solo los de sus cuentas.
#
# Dos formas, con los mismos filtros y la misma regla de propiedad:
# - list():      lista simple (todos los que cumplen). Catálogo de nombres que
#                usan muchas pantallas.
# - list_page(): una página + el total ("Todos los agentes" del admin).
# ======================================================================

from __future__ import annotations

from app.common.contracts import Page, PageRequest, ServiceResult
from app.modules.accounts.domain.account_repository import AccountRepository
from app.modules.bots.domain.bot_entity import Bot
from app.modules.bots.domain.bot_repository import BotCriteria, BotRepository
from app.modules.bots.services.bots.demo_capital import attach_demo_capital


class ListBotsService:
    """
    Lista bots del sistema.

    Reglas de negocio:
    - Admin (owner_id=None): todos los bots, o los de `account_id`, o los de
      las cuentas del dueño `user_id`.
    - Usuario: solo los bots de sus cuentas; con `account_id`, solo si
      esa cuenta es suya (si no, lista vacía). `user_id` se ignora.
    - Filtros opcionales por estado y modo (paper/live). Un valor fuera del
      catálogo de la entidad → BOTS_INVALID_FILTER (422).
    - Orden estable: el más reciente primero (created_at desc, id desc).
    """

    def __init__(self, repo: BotRepository, account_repo: AccountRepository):
        self._repo = repo
        self._account_repo = account_repo

    def list(
        self,
        account_id: int | None = None,
        owner_id: int | None = None,
        status: str | None = None,
        mode: str | None = None,
        user_id: int | None = None,
    ) -> ServiceResult[list[Bot]]:
        criteria = self._build_criteria(account_id, owner_id, status, mode, user_id)
        if not criteria.success:
            return ServiceResult.fail(
                code=criteria.error.code, http_status=criteria.error.http_status
            )
        return ServiceResult.ok(
            data=attach_demo_capital(self._repo.search(criteria.data), self._account_repo)
        )

    def list_page(
        self,
        page: PageRequest,
        account_id: int | None = None,
        owner_id: int | None = None,
        status: str | None = None,
        mode: str | None = None,
        user_id: int | None = None,
    ) -> ServiceResult[Page[Bot]]:
        criteria = self._build_criteria(account_id, owner_id, status, mode, user_id)
        if not criteria.success:
            return ServiceResult.fail(
                code=criteria.error.code, http_status=criteria.error.http_status
            )
        total = self._repo.count(criteria.data)
        items = (
            self._repo.search(criteria.data, offset=page.offset, limit=page.limit)
            if total > page.offset
            else []
        )
        attach_demo_capital(items, self._account_repo)
        return ServiceResult.ok(
            data=Page(items=items, total=total, page=page.page, page_size=page.page_size)
        )

    # ------------------------------------------------------------------
    # Filtros + propiedad (comunes a las dos formas)
    # ------------------------------------------------------------------

    def _build_criteria(
        self,
        account_id: int | None,
        owner_id: int | None,
        status: str | None,
        mode: str | None,
        user_id: int | None,
    ) -> ServiceResult[BotCriteria]:
        if (status is not None and status not in Bot.VALID_STATUSES) or (
            mode is not None and mode not in Bot.VALID_MODES
        ):
            return ServiceResult.fail(code="BOTS_INVALID_FILTER", http_status=422)

        account_ids: list[int] | None
        if owner_id is not None:
            account_ids = [a.id for a in self._account_repo.list_by_user_id(owner_id)]
        elif user_id is not None:
            # Filtro "Dueño" del admin: el dueño de un bot es el de su cuenta
            account_ids = [a.id for a in self._account_repo.list_by_user_id(user_id)]
        else:
            account_ids = None

        if account_id is not None:
            if account_ids is None:
                account_ids = [account_id]
            else:
                account_ids = [account_id] if account_id in account_ids else []

        return ServiceResult.ok(
            data=BotCriteria(account_ids=account_ids, status=status, mode=mode)
        )
