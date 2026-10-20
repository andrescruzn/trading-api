# app/modules/users/domain/__init__.py
# -*- coding: utf-8 -*-

# ======================================================================
# Barrel exports del paquete users.domain
# ======================================================================

from .audit_event import (
    AUDIT_EVENT_TYPES,
    AUDIT_KINDS,
    AUDIT_LOGIN_EVENT_TYPES,
    AUDIT_READ_METHODS,
    AuditEvent,
    AuditEventFilters,
)
from .audit_event_repository import AuditEventRepository
from .user_entity import User
from .user_repository import UserRepository

__all__ = [
    "AUDIT_EVENT_TYPES",
    "AUDIT_KINDS",
    "AUDIT_LOGIN_EVENT_TYPES",
    "AUDIT_READ_METHODS",
    "AuditEvent",
    "AuditEventFilters",
    "AuditEventRepository",
    "User",
    "UserRepository",
]
