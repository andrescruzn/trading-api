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

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.common.audit import AuditMiddleware
from app.common.audit.audit_repository import AuditRepository
from app.common.config import settings
from app.common.errors import register_error_handlers
from app.common.logging import configure_logging, get_logger, LoggingMiddleware
from app.common.security.origin_guard import OriginGuardMiddleware
from app.common.security.security_headers import SecurityHeadersMiddleware
from app.extensions.db.session import engine
from app.modules.health import health_router
from app.modules.market.rest import (
    exchanges_router,
    symbols_router,
    timeframes_router,
    candles_router,
    explorer_router,
)
from app.modules.features.rest import feature_sets_router, candle_features_router
from app.modules.accounts.rest import accounts_router, balances_router
from app.modules.strategies.rest import strategies_router, datasets_router
from app.modules.agent.rest import agent_router, models_router, model_runs_router
from app.modules.bots.rest import bots_router, signals_router
from app.modules.orders.rest import (
    orders_router,
    fills_router,
    positions_router,
    signal_decisions_router,
)
from app.modules.alerts.rest import (
    alert_rules_router,
    alert_events_router,
    alerts_admin_router,
    telegram_webhook_router,
)
from app.modules.billing.rest import investors_router, managed_accounts_router, billing_periods_router
from app.modules.users.rest import auth_router, telegram_link_router, users_router

logger = get_logger(__name__)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """
    Lifespan de FastAPI: arranca el scheduler al iniciar el servidor
    y lo detiene limpiamente al apagarlo. También informa qué servicios
    LLM quedaron en el pool (sin abortar: la app funciona sin IA).
    """
    from app.modules.agent.llm import LLMClientFactory
    from app.modules.scheduler import start as start_scheduler, stop as stop_scheduler

    llm_services = LLMClientFactory.describe(settings)
    if llm_services:
        logger.info("[llm] %d servicio(s) listos: %s", len(llm_services), ", ".join(llm_services))
    else:
        logger.warning("[llm] ningún servicio LLM configurado (revisa LLM_SERVICES y sus API keys)")

    start_scheduler()
    yield
    stop_scheduler()


def create_app() -> FastAPI:
    # ------------------------------------------------------------------
    # Configurar logging
    # ------------------------------------------------------------------
    configure_logging(
        level="DEBUG" if settings.APP_ENV == "development" else "INFO",
        json_format=settings.APP_ENV != "development",
    )

    # La documentación interactiva solo en desarrollo: en producción expone
    # el mapa completo de la API sin necesidad de sesión.
    show_docs = settings.APP_ENV == "development"

    app = FastAPI(
        title=settings.API_TITLE,
        version=settings.API_VERSION,
        lifespan=_lifespan,
        docs_url="/docs" if show_docs else None,
        redoc_url="/redoc" if show_docs else None,
        openapi_url="/openapi.json" if show_docs else None,
    )

    # ------------------------------------------------------------------
    # Middlewares (orden importa: se ejecutan en orden inverso)
    # ------------------------------------------------------------------

    # CSRF: escrituras con Origin ajeno → 403 (dentro de CORS para que el
    # navegador reciba el 403 con sus cabeceras CORS)
    app.add_middleware(OriginGuardMiddleware)

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
    # Routers — API headless: todo bajo settings.API_PREFIX (/api) salvo
    # /health (lo consultan balanceadores y monitoreo en la raíz).
    # ------------------------------------------------------------------
    app.include_router(health_router)

    api_routers = (
        auth_router, telegram_link_router, users_router,
        # Market Data
        exchanges_router, symbols_router, timeframes_router, candles_router, explorer_router,
        # Feature Engineering
        feature_sets_router, candle_features_router,
        # Accounts & Portfolio
        accounts_router, balances_router,
        # Strategies
        strategies_router, datasets_router,
        # Agent (AI Agent + ML Models + Model Runs)
        agent_router, models_router, model_runs_router,
        # Bots & Signals (signals_router antes: GET /signals/pending)
        bots_router, signals_router,
        # Orders & Execution (aprobar / rechazar señales)
        orders_router, fills_router, positions_router, signal_decisions_router,
        # Alerts (+ webhook de Telegram)
        alert_rules_router, alert_events_router, alerts_admin_router, telegram_webhook_router,
        # Billing & Managed Accounts
        investors_router, managed_accounts_router, billing_periods_router,
    )
    for router in api_routers:
        app.include_router(router, prefix=settings.API_PREFIX)

    # ------------------------------------------------------------------
    # Handlers globales (todo error -> envelope {msg, errorCode, data})
    # ------------------------------------------------------------------
    register_error_handlers(app)

    return app
