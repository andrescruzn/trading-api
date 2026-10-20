# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/domain/audit_event_repository.py
#
# Contrato de lectura de la auditoría HTTP (tablas `http_audit_<año>`).
# Solo lectura: las escrituras las hace AuditMiddleware en un hilo aparte.
# ======================================================================

from __future__ import annotations

from abc import ABC, abstractmethod

from app.common.contracts import Page, PageRequest, TransactionalRepository
from app.modules.users.domain.audit_event import AuditEvent, AuditEventFilters


class AuditEventRepository(TransactionalRepository, ABC):
    """Lectura paginada de eventos de auditoría."""

    @abstractmethod
    def list_events(
        self,
        filters: AuditEventFilters,
        years: list[int],
        page: PageRequest,
    ) -> Page[AuditEvent]:
        """
        Eventos de los años dados que cumplen los filtros, del más reciente al
        más antiguo (una página y el total). Años sin tabla se ignoran.
        """
        raise NotImplementedError
