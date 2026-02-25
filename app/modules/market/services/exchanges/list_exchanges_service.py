# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Optional

from app.common.contracts import ServiceResult
from app.modules.market.domain.exchange_entity import Exchange
from app.modules.market.domain.exchange_repository import ExchangeRepository


class ListExchangesService:
    """Lista exchanges con filtro opcional por estado activo."""

    def __init__(self, repo: ExchangeRepository):
        self._repo = repo

    def list(self, is_active: Optional[bool] = None) -> ServiceResult[list[Exchange]]:
        exchanges = self._repo.list_all(is_active=is_active)
        return ServiceResult.ok(data=exchanges)
