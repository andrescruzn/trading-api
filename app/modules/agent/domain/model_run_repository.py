# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/agent/domain/model_run_repository.py
#
# Contrato del repositorio de ejecuciones de entrenamiento.
# ======================================================================

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.modules.agent.domain.model_run_entity import ModelRun


class ModelRunRepository(ABC):

    @abstractmethod
    def get_by_id(self, run_id: int) -> Optional[ModelRun]:
        ...

    @abstractmethod
    def list_by_model(self, model_id: int) -> list[ModelRun]:
        ...

    @abstractmethod
    def create(self, run: ModelRun) -> ModelRun:
        ...

    @abstractmethod
    def update(self, run: ModelRun) -> ModelRun:
        ...
