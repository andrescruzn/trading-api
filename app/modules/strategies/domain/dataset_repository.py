# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/strategies/domain/dataset_repository.py
#
# Interfaz del repositorio de datasets (contrato de dominio).
# ======================================================================

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.modules.strategies.domain.dataset_entity import Dataset


class DatasetRepository(ABC):

    @abstractmethod
    def get_by_id(self, dataset_id: int) -> Optional[Dataset]:
        ...

    @abstractmethod
    def list_all(self) -> list[Dataset]:
        ...

    @abstractmethod
    def create(self, dataset: Dataset) -> Dataset:
        ...
