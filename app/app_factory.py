# -*- coding: utf-8 -*-

# ======================================================================
# app/app_factory.py
#
# PROPÓSITO:
# - Factory para crear la aplicación FastAPI.
# - Centraliza configuración de middlewares, routers y handlers.
# ======================================================================

# 1) Registro de modelos ORM (necesario para FKs)
import app.extensions.db.models_registry  # noqa: F401

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.common.config import settings
from app.common.errors import register_error_handlers
from app.common.logging import configure_logging, LoggingMiddleware
from app.modules.health import health_router
from app.modules.users.rest import auth_router


def create_app() -> FastAPI:
    # ------------------------------------------------------------------
    # Configurar logging
    # ------------------------------------------------------------------
    configure_logging(
        level="DEBUG" if settings.APP_ENV == "development" else "INFO",
        json_format=settings.APP_ENV != "development",
    )

    app = FastAPI(title=settings.API_TITLE, version=settings.API_VERSION)

    # ------------------------------------------------------------------
    # Middlewares (orden importa: se ejecutan en orden inverso)
    # ------------------------------------------------------------------

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept", "X-Request-ID"],
    )

    # Logging Middleware (request_id, duración, logs)
    app.add_middleware(LoggingMiddleware)

    # ------------------------------------------------------------------
    # Routers
    # ------------------------------------------------------------------
    app.include_router(health_router)
    app.include_router(auth_router)

    # ------------------------------------------------------------------
    # Handlers globales (AuthException/JwtCodecError -> envelope)
    # ------------------------------------------------------------------
    register_error_handlers(app)

    return app