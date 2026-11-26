# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/providers/audit_provider.py
#
# PROPÓSITO:
# - Factory de los servicios de lectura de la auditoría HTTP (solo admin).
#
# POR QUÉ EN USERS (M1):
# - La auditoría es parte de la seguridad de M1 (redacción, middleware,
#   script de purga ya documentados en specs/M01-AUTH.md) y la página vive
#   junto a Usuarios en Configuración. La escritura sigue en app/common/audit.
# ======================================================================

from __future__ import annotations

from sqlalchemy.orm import Session

from app.modules.users.infrastructure.audit_event_repository_impl import (
    SqlAlchemyAuditEventRepository,
)
from app.modules.users.services.audit import ListAuditEventsService


class AuditServiceFactory:
    """Crea los servicios de auditoría con el repositorio de lectura."""

    def __init__(self, session: Session):
        self._repo = SqlAlchemyAuditEventRepository(session)

    def list_audit_events(self) -> ListAuditEventsService:
        """Listado paginado de eventos de auditoría."""
        return ListAuditEventsService(repo=self._repo)
