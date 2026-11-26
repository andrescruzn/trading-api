# -*- coding: utf-8 -*-

# ======================================================================
# app/common/service_result.py
#
# PROPÓSITO:
# - Contrato estándar entre Services y REST.
#
# DECISIÓN (según tus preferencias):
# - El Service NO retorna mensajes de UI.
# - El Service retorna un error "crudo" (code/http_status/meta).
# - La capa REST decide el msg final (presentación).
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Generic, Optional, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class ServiceError:
    """
    Error crudo (sin UI).

    - code: razón estable (string) para mapear en REST a un mensaje.
    - http_status: sugerencia para la capa REST (no es HTTP en sí).
    - meta: datos crudos adicionales (debug/control), no presentación.
    """
    code: str
    http_status: int = 400
    meta: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class ServiceResult(Generic[T]):
    """
    Resultado estándar de un Service.
    """
    success: bool
    data: Optional[T] = None
    error: Optional[ServiceError] = None

    @staticmethod
    def ok(data: T) -> "ServiceResult[T]":
        return ServiceResult(success=True, data=data, error=None)

    @staticmethod
    def fail(
        *,
        code: str,
        http_status: int = 400,
        meta: Optional[Dict[str, Any]] = None,
    ) -> "ServiceResult[T]":
        return ServiceResult(
            success=False,
            data=None,
            error=ServiceError(code=code, http_status=http_status, meta=meta),
        )