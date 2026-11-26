# -*- coding: utf-8 -*-

from __future__ import annotations

from app.common.contracts import ServiceResult
from app.modules.agent.domain.model_run_entity import ModelRun
from app.modules.agent.domain.model_run_repository import ModelRunRepository


class ListModelRunsService:
    """Lista todas las ejecuciones de entrenamiento de un modelo."""

    def __init__(self, repo: ModelRunRepository):
        self._repo = repo

    def list(self, model_id: int) -> ServiceResult[list[ModelRun]]:
        runs = self._repo.list_by_model(model_id)
        return ServiceResult.ok(data=runs)
