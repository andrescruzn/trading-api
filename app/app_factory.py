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
from fastapi.staticfiles import StaticFiles

from app.common.audit import AuditMiddleware
from app.common.audit.audit_repository import AuditRepository
from app.common.config import settings
from app.common.errors import register_error_handlers
from app.common.logging import configure_logging, LoggingMiddleware
from app.common.security.security_headers import SecurityHeadersMiddleware
from app.extensions.db.session import engine
from app.modules.health import health_router
from app.modules.market.rest import (
    exchanges_router,
    symbols_router,
    timeframes_router,
    candles_router,
)
from app.modules.features.rest import feature_sets_router, candle_features_router
from app.modules.accounts.rest import accounts_router, balances_router
from app.modules.strategies.rest import strategies_router, datasets_router
from app.modules.agent.rest import agent_router, models_router, model_runs_router
from app.modules.users.rest import auth_router
from app.modules.web import web_router


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
    # Static files (CSS, JS)
    # ------------------------------------------------------------------
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

    # ------------------------------------------------------------------
    # Middlewares (orden importa: se ejecutan en orden inverso)
    # ------------------------------------------------------------------

    # Security headers (CSP, HSTS, X-Frame-Options, etc.)
    app.add_middleware(SecurityHeadersMiddleware)

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

    # Audit Middleware (HTTP audit dinámico por año — más externo = duración real)
    audit_repo = AuditRepository(engine=engine)
    app.add_middleware(AuditMiddleware, repository=audit_repo)

    # ------------------------------------------------------------------
    # Routers
    # ------------------------------------------------------------------
    app.include_router(health_router)
    app.include_router(auth_router)

    # Market Data
    app.include_router(exchanges_router)
    app.include_router(symbols_router)
    app.include_router(timeframes_router)
    app.include_router(candles_router)

    # Feature Engineering
    app.include_router(feature_sets_router)
    app.include_router(candle_features_router)

    # Accounts & Portfolio
    app.include_router(accounts_router)
    app.include_router(balances_router)

    # Strategies
    app.include_router(strategies_router)
    app.include_router(datasets_router)

    # Agent (AI Agent + ML Models + Model Runs)
    app.include_router(agent_router)
    app.include_router(models_router)
    app.include_router(model_runs_router)

    app.include_router(web_router)      # Páginas HTML (siempre al final)

    # ------------------------------------------------------------------
    # Handlers globales (AuthException/JwtCodecError -> envelope)
    # ------------------------------------------------------------------
    register_error_handlers(app)

    return app
