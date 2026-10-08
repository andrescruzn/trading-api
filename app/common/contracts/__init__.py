# -*- coding: utf-8 -*-

# ======================================================================
# app/common/contracts/__init__.py
#
# Barrel exports para contratos de aplicación.
# ======================================================================

from .service_result import ServiceResult, ServiceError
from .transactional_repository import TransactionalRepository

__all__ = ["ServiceResult", "ServiceError", "TransactionalRepository"]