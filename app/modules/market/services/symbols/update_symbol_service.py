# -*- coding: utf-8 -*-

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.common.contracts import ServiceResult
from app.modules.market.domain.symbol_entity import Symbol
from app.modules.market.domain.symbol_repository import SymbolRepository


class UpdateSymbolService:
    """Actualiza un símbolo existente (campos opcionales)."""

    def __init__(self, repo: SymbolRepository, session: Session):
        self._repo = repo
        self._session = session

    def update(
        self,
        symbol_id: int,
        asset_class: Optional[str] = None,
        base_asset: Optional[str] = None,
        quote_asset: Optional[str] = None,
        tick_size: Optional[Decimal] = None,
        lot_size: Optional[Decimal] = None,
        is_active: Optional[bool] = None,
    ) -> ServiceResult[Symbol]:
        symbol = self._repo.get_by_id(symbol_id)
        if symbol is None:
            return ServiceResult.fail(code="SYMBOL_NOT_FOUND", http_status=404)

        if asset_class is not None:
            dummy = Symbol(id=0, exchange_id=symbol.exchange_id, symbol=symbol.symbol, asset_class=asset_class)
            if not dummy.is_valid_asset_class():
                return ServiceResult.fail(code="SYMBOL_INVALID_ASSET_CLASS", http_status=422)
            symbol.asset_class = asset_class

        if base_asset is not None:
            symbol.base_asset = base_asset
        if quote_asset is not None:
            symbol.quote_asset = quote_asset
        if tick_size is not None:
            symbol.tick_size = tick_size
        if lot_size is not None:
            symbol.lot_size = lot_size
        if is_active is not None:
            symbol.is_active = is_active

        updated = self._repo.update(symbol)
        self._session.commit()

        return ServiceResult.ok(data=updated)
