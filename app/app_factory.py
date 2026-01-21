# -*- coding: utf-8 -*-

# ======================================================================
# app/app_factory.py
#
# PROPÓSITO:
# - Centralizar el bootstrap de la aplicación FastAPI.
#
# RESPONSABILIDAD:
# - Crear la instancia FastAPI.
# - Registrar routers por módulo (screaming architecture).
# - Registrar middlewares / handlers transversales (cuando existan).
#
# POR QUÉ:
# - main.py se mantiene mínimo.
# - Escala bien cuando el sistema crece.
#
# NOTA ARQUITECTÓNICA:
# - NO contiene lógica de negocio.
# - NO contiene configuración de DB.
# - NO contiene lectura de variables de entorno.
# ======================================================================

from fastapi import FastAPI

from app.common.config import settings
from app.modules.users.rest import auth_router


def create_app() -> FastAPI:
    """
    Application Factory.

    Retorna:
    - Instancia configurada de FastAPI.
    """

    # ------------------------------------------------------------------
    # Crear aplicación
    # ------------------------------------------------------------------
    app = FastAPI(
        title=settings.API_TITLE,
        version=settings.API_VERSION,
    )

    # ------------------------------------------------------------------
    # Routers (por módulo / bounded context)
    # ------------------------------------------------------------------
    app.include_router(auth_router)

    # ------------------------------------------------------------------
    # (Futuro)
    # - Middlewares
    # - Exception handlers globales
    # - Lifespan events
    # ------------------------------------------------------------------

    return app