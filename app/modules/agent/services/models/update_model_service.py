# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from app.common.contracts import ServiceResult
from app.modules.agent.domain.ml_model_entity import MLModel
from app.modules.agent.domain.ml_model_repository import MLModelRepository


class UpdateModelService:
    """
    Actualiza un modelo ML existente.
    Permite cambiar status (active → deprecated → archived),
    artifact_uri y meta.
    """

    def __init__(self, repo: MLModelRepository, session: Session):
        self._repo = repo
        self._session = session

    def update(
        self,
        model_id: int,
        status: Optional[str] = None,
        artifact_uri: Optional[str] = None,
        meta: Optional[dict[str, Any]] = None,
    ) -> ServiceResult[MLModel]:
        model = self._repo.get_by_id(model_id)
        if model is None:
            return ServiceResult.fail(code="MODEL_NOT_FOUND", http_status=404)

        if status is not None:
            if status not in MLModel.VALID_STATUSES:
                return ServiceResult.fail(code="MODEL_INVALID_STATUS", http_status=422)
            model.status = status

        if artifact_uri is not None:
            model.artifact_uri = artifact_uri

        if meta is not None:
            model.meta = meta

        updated = self._repo.update(model)
        self._session.commit()
        return ServiceResult.ok(data=updated)
