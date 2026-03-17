# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/agent/domain/ml_model_repository.py
#
# Contrato del repositorio de modelos ML (interfaz de dominio).
# La implementación concreta vive en infrastructure/.
# ======================================================================

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.modules.agent.domain.ml_model_entity import MLModel


class MLModelRepository(ABC):

    @abstractmethod
    def get_by_id(self, model_id: int) -> Optional[MLModel]:
        ...

    @abstractmethod
    def get_by_name_version(self, name: str, version: str) -> Optional[MLModel]:
        ...

    @abstractmethod
    def list_all(self, status: Optional[str] = None) -> list[MLModel]:
        ...

    @abstractmethod
    def create(self, model: MLModel) -> MLModel:
        ...

    @abstractmethod
    def update(self, model: MLModel) -> MLModel:
        ...
