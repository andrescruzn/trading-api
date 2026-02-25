# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/market/domain/timeframe_repository.py
#
# Contrato (interfaz) del repositorio de timeframes.
# ======================================================================

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.modules.market.domain.timeframe_entity import Timeframe


class TimeframeRepository(ABC):

    @abstractmethod
    def get_by_id(self, timeframe_id: int) -> Optional[Timeframe]: ...

    @abstractmethod
    def get_by_code(self, code: str) -> Optional[Timeframe]: ...

    @abstractmethod
    def list_all(self) -> list[Timeframe]: ...

    @abstractmethod
    def create(self, timeframe: Timeframe) -> Timeframe: ...
