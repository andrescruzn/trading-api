# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Optional

from app.common.contracts import ServiceResult
from app.modules.agent.domain.ml_model_entity import MLModel
from app.modules.agent.domain.ml_model_repository import MLModelRepository


class ListModelsService:
    """Lista modelos ML registrados. Filtra por status si se especifica."""

    def __init__(self, repo: MLModelRepository):
        self._repo = repo

    def list(self, status: Optional[str] = None) -> ServiceResult[list[MLModel]]:
        models = self._repo.list_all(status=status)
        return ServiceResult.ok(data=models)
