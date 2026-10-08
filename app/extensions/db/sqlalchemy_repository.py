# -*- coding: utf-8 -*-

# ======================================================================
# app/extensions/db/sqlalchemy_repository.py
#
# PROPÓSITO:
# - Base de todas las implementaciones SqlAlchemy<X>Repository.
# - Único lugar del código que llama a `session.commit()` / `rollback()`.
#
# USO:
#     class SqlAlchemyStrategyRepository(SqlAlchemyRepository, StrategyRepository):
#         def __init__(self, session: Session):
#             super().__init__(session)
# ======================================================================

from __future__ import annotations

from sqlalchemy.orm import Session


class SqlAlchemyRepository:
    """Implementa TransactionalRepository sobre una sesión SQLAlchemy."""

    def __init__(self, session: Session):
        self._session = session

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()
