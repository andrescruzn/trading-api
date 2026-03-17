# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/agent/infrastructure/ml_model_repository_impl.py
#
# Implementación SQLAlchemy del repositorio de modelos ML.
# ======================================================================

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.modules.agent.domain.ml_model_entity import MLModel
from app.modules.agent.domain.ml_model_repository import MLModelRepository
from app.modules.agent.infrastructure.ml_model_model import MLModelORM


class SqlAlchemyMLModelRepository(MLModelRepository):
    """Repositorio concreto de modelos ML usando SQLAlchemy."""

    def __init__(self, session: Session):
        self._session = session

    # ------------------------------------------------------------------
    # Mapper: ORM → Domain
    # ------------------------------------------------------------------

    @staticmethod
    def _to_domain(orm: MLModelORM) -> MLModel:
        return MLModel(
            id=orm.id,
            name=orm.name,
            version=orm.version,
            model_type=orm.model_type,
            feature_set_id=orm.feature_set_id,
            artifact_uri=orm.artifact_uri,
            status=orm.status,
            meta=orm.meta or {},
            created_at=orm.created_at,
        )

    @staticmethod
    def _apply_to_orm(model: MLModel, orm: MLModelORM) -> MLModelORM:
        orm.name = model.name
        orm.version = model.version
        orm.model_type = model.model_type
        orm.feature_set_id = model.feature_set_id
        orm.artifact_uri = model.artifact_uri
        orm.status = model.status
        orm.meta = model.meta
        return orm

    # ------------------------------------------------------------------
    # Contract
    # ------------------------------------------------------------------

    def get_by_id(self, model_id: int) -> Optional[MLModel]:
        orm = self._session.get(MLModelORM, model_id)
        return None if orm is None else self._to_domain(orm)

    def get_by_name_version(self, name: str, version: str) -> Optional[MLModel]:
        orm = (
            self._session.query(MLModelORM)
            .filter(MLModelORM.name == name, MLModelORM.version == version)
            .first()
        )
        return None if orm is None else self._to_domain(orm)

    def list_all(self, status: Optional[str] = None) -> list[MLModel]:
        q = self._session.query(MLModelORM)
        if status:
            q = q.filter(MLModelORM.status == status)
        orms = q.order_by(MLModelORM.created_at.desc()).all()
        return [self._to_domain(o) for o in orms]

    def create(self, model: MLModel) -> MLModel:
        orm = MLModelORM()
        self._apply_to_orm(model, orm)
        self._session.add(orm)
        self._session.flush()
        self._session.refresh(orm)
        return self._to_domain(orm)

    def update(self, model: MLModel) -> MLModel:
        orm: Optional[MLModelORM] = self._session.get(MLModelORM, model.id)
        if orm is None:
            raise ValueError(f"MLModel not found for update: id={model.id}")
        self._apply_to_orm(model, orm)
        self._session.flush()
        self._session.refresh(orm)
        return self._to_domain(orm)
