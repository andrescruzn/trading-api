# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/strategies/domain/strategy_repository.py
#
# Interfaz del repositorio de estrategias (contrato de dominio).
# ======================================================================

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.modules.strategies.domain.strategy_entity import Strategy


class StrategyRepository(ABC):

    @abstractmethod
    def get_by_id(self, strategy_id: int) -> Optional[Strategy]:
        ...

    @abstractmethod
    def get_by_name_version(self, name: str, version: str) -> Optional[Strategy]:
        ...

    @abstractmethod
    def list_all(self) -> list[Strategy]:
        ...

    @abstractmethod
    def create(self, strategy: Strategy) -> Strategy:
        ...

    @abstractmethod
    def update(self, strategy: Strategy) -> Strategy:
        ...
