# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/market/domain/symbol_repository.py
#
# Contrato (interfaz) del repositorio de symbols.
# ======================================================================

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.modules.market.domain.symbol_entity import Symbol


class SymbolRepository(ABC):

    @abstractmethod
    def get_by_id(self, symbol_id: int) -> Optional[Symbol]: ...

    @abstractmethod
    def get_by_exchange_and_symbol(
        self, exchange_id: int, symbol: str
    ) -> Optional[Symbol]: ...

    @abstractmethod
    def list_all(
        self,
        exchange_id: Optional[int] = None,
        asset_class: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> list[Symbol]: ...

    @abstractmethod
    def create(self, symbol: Symbol) -> Symbol: ...

    @abstractmethod
    def update(self, symbol: Symbol) -> Symbol: ...
