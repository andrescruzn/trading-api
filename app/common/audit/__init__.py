# -*- coding: utf-8 -*-

# ======================================================================
# app/common/audit/__init__.py
#
# PROPÓSITO:
# - Barrel export del paquete de auditoría HTTP dinámica.
# ======================================================================

from app.common.audit.audit_middleware import AuditMiddleware

__all__ = ["AuditMiddleware"]
