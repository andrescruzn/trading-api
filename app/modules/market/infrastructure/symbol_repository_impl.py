# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/market/infrastructure/symbol_repository_impl.py
#
# Implementación SQLAlchemy del repositorio de symbols.
# ======================================================================

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.modules.market.domain.symbol_entity import Symbol
from app.modules.market.domain.symbol_repository import SymbolRepository
from app.modules.market.infrastructure.symbol_model import SymbolModel


class SqlAlchemySymbolRepository(SymbolRepository):
    """Repositorio concreto de symbols usando SQLAlchemy."""

    def __init__(self, session: Session):
        self._session = session

    # ==================================================================
    # Mappers
    # ==================================================================

    @staticmethod
    def _to_domain(model: SymbolModel) -> Symbol:
        return Symbol(
            id=model.id,
            exchange_id=model.exchange_id,
            symbol=model.symbol,
            asset_class=model.asset_class,
            base_asset=model.base_asset,
            quote_asset=model.quote_asset,
            tick_size=Decimal(str(model.tick_size)) if model.tick_size is not None else None,
            lot_size=Decimal(str(model.lot_size)) if model.lot_size is not None else None,
            is_active=bool(model.is_active),
            created_at=model.created_at,
        )

    @staticmethod
    def _apply_domain_to_model(symbol: Symbol, model: SymbolModel) -> SymbolModel:
        model.exchange_id = symbol.exchange_id
        model.symbol = symbol.symbol
        model.asset_class = symbol.asset_class
        model.base_asset = symbol.base_asset
        model.quote_asset = symbol.quote_asset
        model.tick_size = symbol.tick_size
        model.lot_size = symbol.lot_size
        model.is_active = symbol.is_active
        return model

    # ==================================================================
    # Contract
    # ==================================================================

    def get_by_id(self, symbol_id: int) -> Optional[Symbol]:
        model: Optional[SymbolModel] = self._session.get(SymbolModel, symbol_id)
        return None if model is None else self._to_domain(model)

    def get_by_exchange_and_symbol(
        self, exchange_id: int, symbol: str
    ) -> Optional[Symbol]:
        model: Optional[SymbolModel] = (
            self._session.query(SymbolModel)
            .filter(
                SymbolModel.exchange_id == exchange_id,
                SymbolModel.symbol == symbol,
            )
            .one_or_none()
        )
        return None if model is None else self._to_domain(model)

    def list_all(
        self,
        exchange_id: Optional[int] = None,
        asset_class: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> list[Symbol]:
        query = self._session.query(SymbolModel)
        if exchange_id is not None:
            query = query.filter(SymbolModel.exchange_id == exchange_id)
        if asset_class is not None:
            query = query.filter(SymbolModel.asset_class == asset_class)
        if is_active is not None:
            query = query.filter(SymbolModel.is_active == is_active)
        query = query.order_by(SymbolModel.symbol)
        return [self._to_domain(m) for m in query.all()]

    def create(self, symbol: Symbol) -> Symbol:
        model = SymbolModel()
        self._apply_domain_to_model(symbol, model)
        self._session.add(model)
        self._session.flush()
        self._session.refresh(model)
        return self._to_domain(model)

    def update(self, symbol: Symbol) -> Symbol:
        model: Optional[SymbolModel] = self._session.get(SymbolModel, symbol.id)
        if model is None:
            raise ValueError(f"Symbol not found for update: id={symbol.id}")
        self._apply_domain_to_model(symbol, model)
        self._session.flush()
        self._session.refresh(model)
        return self._to_domain(model)
