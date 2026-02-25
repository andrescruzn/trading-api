# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/market/domain/exchange_repository.py
#
# Contrato (interfaz) del repositorio de exchanges.
# Implementado en infrastructure/exchange_repository_impl.py
# ======================================================================

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.modules.market.domain.exchange_entity import Exchange


class ExchangeRepository(ABC):

    @abstractmethod
    def get_by_id(self, exchange_id: int) -> Optional[Exchange]: ...

    @abstractmethod
    def get_by_name(self, name: str) -> Optional[Exchange]: ...

    @abstractmethod
    def list_all(self, is_active: Optional[bool] = None) -> list[Exchange]: ...

    @abstractmethod
    def create(self, exchange: Exchange) -> Exchange: ...

    @abstractmethod
    def update(self, exchange: Exchange) -> Exchange: ...
