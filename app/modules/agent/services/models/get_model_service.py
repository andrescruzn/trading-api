# -*- coding: utf-8 -*-

from __future__ import annotations

from app.common.contracts import ServiceResult
from app.modules.agent.domain.ml_model_entity import MLModel
from app.modules.agent.domain.ml_model_repository import MLModelRepository


class GetModelService:
    """Obtiene un modelo ML por ID."""

    def __init__(self, repo: MLModelRepository):
        self._repo = repo

    def get(self, model_id: int) -> ServiceResult[MLModel]:
        model = self._repo.get_by_id(model_id)
        if model is None:
            return ServiceResult.fail(code="MODEL_NOT_FOUND", http_status=404)
        return ServiceResult.ok(data=model)
