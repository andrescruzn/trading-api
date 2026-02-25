# -*- coding: utf-8 -*-

from __future__ import annotations

from sqlalchemy.orm import Session

from app.common.contracts import ServiceResult
from app.modules.market.domain.timeframe_entity import Timeframe
from app.modules.market.domain.timeframe_repository import TimeframeRepository


class CreateTimeframeService:
    """Crea un nuevo timeframe verificando unicidad del código."""

    def __init__(self, repo: TimeframeRepository, session: Session):
        self._repo = repo
        self._session = session

    def create(self, code: str, seconds: int) -> ServiceResult[Timeframe]:
        if seconds <= 0:
            return ServiceResult.fail(code="TIMEFRAME_INVALID_SECONDS", http_status=422)

        existing = self._repo.get_by_code(code)
        if existing is not None:
            return ServiceResult.fail(code="TIMEFRAME_CODE_EXISTS", http_status=409)

        new_tf = Timeframe(id=0, code=code, seconds=seconds)
        created = self._repo.create(new_tf)
        self._session.commit()

        return ServiceResult.ok(data=created)
