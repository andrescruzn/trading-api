# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/health/rest/routes.py
#
# ENDPOINTS:
# - GET /health       → Estado básico del sistema
# - GET /health/ready → Readiness check (incluye DB)
# - GET /health/live  → Liveness check (solo aplicación)
#
# USO:
# - Kubernetes: readinessProbe y livenessProbe
# - Load balancers: health check
# - Monitoreo: verificar estado del sistema
# ======================================================================

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.common.config import settings
from app.common.http import build_success_response
from app.extensions.db import get_db


router = APIRouter(prefix="/health", tags=["Health"])


# ======================================================================
# GET /health - Estado básico
# ======================================================================

@router.get(
    "",
    status_code=status.HTTP_200_OK,
)
def health_check():
    """
    Health check básico.

    Retorna:
    - status: "ok"
    - version: versión de la API
    - environment: ambiente actual
    - timestamp: fecha/hora UTC
    """
    return build_success_response(
        data={
            "status": "ok",
            "version": settings.API_VERSION,
            "environment": settings.APP_ENV,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


# ======================================================================
# GET /health/live - Liveness check
# ======================================================================

@router.get(
    "/live",
    status_code=status.HTTP_200_OK,
)
def liveness_check():
    """
    Liveness check (Kubernetes).

    Verifica que la aplicación está corriendo.
    NO verifica dependencias externas (DB, Redis, etc.).

    Retorna:
    - status: "ok"
    """
    return build_success_response(
        data={"status": "ok"}
    )


# ======================================================================
# GET /health/ready - Readiness check
# ======================================================================

@router.get(
    "/ready",
    status_code=status.HTTP_200_OK,
)
def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness check (Kubernetes).

    Verifica que la aplicación puede recibir tráfico:
    - Conexión a base de datos

    Retorna:
    - status: "ok" o "degraded"
    - checks: estado de cada dependencia
    """
    checks: Dict[str, Any] = {}
    overall_status = "ok"

    # ------------------------------------------------------------------
    # Check: Database
    # ------------------------------------------------------------------
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = {
            "status": "ok",
            "type": "mysql",
        }
    except Exception as e:
        checks["database"] = {
            "status": "error",
            "type": "mysql",
            "error": str(e)[:100],  # Truncar por seguridad
        }
        overall_status = "degraded"

    # ------------------------------------------------------------------
    # Respuesta
    # ------------------------------------------------------------------
    response_data = {
        "status": overall_status,
        "checks": checks,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if overall_status != "ok":
        # Retornar 503 si hay problemas
        from app.common.http import send
        return send(
            msg="Service degraded",
            status_code=503,
            data=response_data,
        )

    return build_success_response(data=response_data)
