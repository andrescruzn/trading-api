# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.common.contracts import ServiceResult
from app.modules.market.domain.exchange_entity import Exchange
from app.modules.market.domain.exchange_repository import ExchangeRepository


class UpdateExchangeService:
    """Actualiza nombre, tipo y estado activo de un exchange."""

    def __init__(self, repo: ExchangeRepository, session: Session):
        self._repo = repo
        self._session = session

    def update(
        self,
        exchange_id: int,
        name: Optional[str] = None,
        type: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> ServiceResult[Exchange]:
        exchange = self._repo.get_by_id(exchange_id)
        if exchange is None:
            return ServiceResult.fail(code="EXCHANGE_NOT_FOUND", http_status=404)

        # Aplicar cambios solo si se enviaron
        if name is not None:
            # Verificar que el nuevo nombre no exista en otro registro
            existing = self._repo.get_by_name(name)
            if existing is not None and existing.id != exchange_id:
                return ServiceResult.fail(code="EXCHANGE_NAME_EXISTS", http_status=409)
            exchange.name = name

        if type is not None:
            dummy = Exchange(id=0, name="", type=type)
            if not dummy.is_valid_type():
                return ServiceResult.fail(code="EXCHANGE_INVALID_TYPE", http_status=422)
            exchange.type = type

        if is_active is not None:
            exchange.is_active = is_active

        updated = self._repo.update(exchange)
        self._session.commit()

        return ServiceResult.ok(data=updated)
