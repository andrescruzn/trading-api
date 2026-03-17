# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/agent/infrastructure/model_run_repository_impl.py
#
# Implementación SQLAlchemy del repositorio de ejecuciones de entrenamiento.
# ======================================================================

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.modules.agent.domain.model_run_entity import ModelRun
from app.modules.agent.domain.model_run_repository import ModelRunRepository
from app.modules.agent.infrastructure.model_run_model import ModelRunORM


class SqlAlchemyModelRunRepository(ModelRunRepository):
    """Repositorio concreto de ejecuciones de entrenamiento usando SQLAlchemy."""

    def __init__(self, session: Session):
        self._session = session

    # ------------------------------------------------------------------
    # Mapper: ORM → Domain
    # ------------------------------------------------------------------

    @staticmethod
    def _to_domain(orm: ModelRunORM) -> ModelRun:
        return ModelRun(
            id=orm.id,
            model_id=orm.model_id,
            dataset_id=orm.dataset_id,
            status=orm.status,
            metrics=orm.metrics or {},
            params=orm.params or {},
            logs_uri=orm.logs_uri,
            started_at=orm.started_at,
            finished_at=orm.finished_at,
        )

    @staticmethod
    def _apply_to_orm(run: ModelRun, orm: ModelRunORM) -> ModelRunORM:
        orm.model_id = run.model_id
        orm.dataset_id = run.dataset_id
        orm.started_at = run.started_at
        orm.status = run.status
        orm.metrics = run.metrics
        orm.params = run.params
        orm.logs_uri = run.logs_uri
        orm.finished_at = run.finished_at
        return orm

    # ------------------------------------------------------------------
    # Contract
    # ------------------------------------------------------------------

    def get_by_id(self, run_id: int) -> Optional[ModelRun]:
        orm = self._session.get(ModelRunORM, run_id)
        return None if orm is None else self._to_domain(orm)

    def list_by_model(self, model_id: int) -> list[ModelRun]:
        orms = (
            self._session.query(ModelRunORM)
            .filter(ModelRunORM.model_id == model_id)
            .order_by(ModelRunORM.started_at.desc())
            .all()
        )
        return [self._to_domain(o) for o in orms]

    def create(self, run: ModelRun) -> ModelRun:
        orm = ModelRunORM()
        self._apply_to_orm(run, orm)
        self._session.add(orm)
        self._session.flush()
        self._session.refresh(orm)
        return self._to_domain(orm)

    def update(self, run: ModelRun) -> ModelRun:
        orm: Optional[ModelRunORM] = self._session.get(ModelRunORM, run.id)
        if orm is None:
            raise ValueError(f"ModelRun not found for update: id={run.id}")
        self._apply_to_orm(run, orm)
        self._session.flush()
        self._session.refresh(orm)
        return self._to_domain(orm)
