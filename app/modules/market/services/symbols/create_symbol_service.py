# -*- coding: utf-8 -*-

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.common.contracts import ServiceResult
from app.modules.market.domain.exchange_repository import ExchangeRepository
from app.modules.market.domain.symbol_entity import Symbol
from app.modules.market.domain.symbol_repository import SymbolRepository


class CreateSymbolService:
    """Crea un símbolo nuevo asociado a un exchange existente."""

    def __init__(
        self,
        symbol_repo: SymbolRepository,
        exchange_repo: ExchangeRepository,
        session: Session,
    ):
        self._symbol_repo = symbol_repo
        self._exchange_repo = exchange_repo
        self._session = session

    def create(
        self,
        exchange_id: int,
        symbol: str,
        asset_class: str,
        base_asset: Optional[str] = None,
        quote_asset: Optional[str] = None,
        tick_size: Optional[Decimal] = None,
        lot_size: Optional[Decimal] = None,
    ) -> ServiceResult[Symbol]:
        # Validar que el exchange existe
        exchange = self._exchange_repo.get_by_id(exchange_id)
        if exchange is None:
            return ServiceResult.fail(code="EXCHANGE_NOT_FOUND", http_status=404)

        # Validar asset_class
        dummy = Symbol(id=0, exchange_id=exchange_id, symbol=symbol, asset_class=asset_class)
        if not dummy.is_valid_asset_class():
            return ServiceResult.fail(code="SYMBOL_INVALID_ASSET_CLASS", http_status=422)

        # Verificar unicidad (exchange_id, symbol)
        existing = self._symbol_repo.get_by_exchange_and_symbol(exchange_id, symbol)
        if existing is not None:
            return ServiceResult.fail(code="SYMBOL_ALREADY_EXISTS", http_status=409)

        new_symbol = Symbol(
            id=0,
            exchange_id=exchange_id,
            symbol=symbol,
            asset_class=asset_class,
            base_asset=base_asset,
            quote_asset=quote_asset,
            tick_size=tick_size,
            lot_size=lot_size,
            is_active=True,
        )
        created = self._symbol_repo.create(new_symbol)
        self._session.commit()

        return ServiceResult.ok(data=created)
