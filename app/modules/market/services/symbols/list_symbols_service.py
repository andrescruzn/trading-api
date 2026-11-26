# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Optional

from app.common.contracts import ServiceResult
from app.modules.market.domain.symbol_entity import Symbol
from app.modules.market.domain.symbol_repository import SymbolRepository


class ListSymbolsService:
    """Lista símbolos con filtros opcionales."""

    def __init__(self, repo: SymbolRepository):
        self._repo = repo

    def list(
        self,
        exchange_id: Optional[int] = None,
        asset_class: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> ServiceResult[list[Symbol]]:
        symbols = self._repo.list_all(
            exchange_id=exchange_id,
            asset_class=asset_class,
            is_active=is_active,
        )
        return ServiceResult.ok(data=symbols)
