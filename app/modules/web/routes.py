# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/web/routes.py
#
# PROPÓSITO:
# - Servir páginas HTML (Jinja2) para la interfaz web.
#
# RUTAS:
# - GET /          → Redirect a /login
# - GET /login     → Página de login (password + OTP)
# - GET /dashboard → Dashboard (requiere cookie válida)
# - GET /profile   → Cambio de contraseña (requiere cookie válida)
#
# SEGURIDAD:
# - Las rutas protegidas verifican la cookie JWT.
# - Si no hay cookie válida → redirect a /login.
# - No lanza 401 (es una página, no una API) → redirige silenciosamente.
# ======================================================================

from __future__ import annotations

import time

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.common.config import settings
from app.common.security.jwt.jwt_utils import decode_access_token, JwtCodecError

templates = Jinja2Templates(directory="app/templates")

web_router = APIRouter(tags=["Web"])

# Versión de assets estáticos — cambia en cada reinicio del servidor.
# Fuerza al navegador a descargar JS/CSS frescos tras cada deploy.
templates.env.globals["sv"] = str(int(time.time()))


# ======================================================================
# Helper: verificar cookie sin lanzar excepción
# ======================================================================

def _get_identity_from_cookie(request: Request) -> dict | None:
    """
    Intenta extraer la identidad desde la cookie JWT.
    Retorna el payload si es válido, None si no hay cookie o es inválida.
    No hace validación DB (es para redireccionar, no para autorizar).
    """
    token = request.cookies.get(settings.AUTH_COOKIE_NAME)
    if not token:
        return None
    try:
        payload = decode_access_token(
            token=token,
            secret_key=settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
        sub = payload.get("sub", {})
        return sub if isinstance(sub, dict) and sub.get("user_id") else None
    except (JwtCodecError, Exception):
        return None


# ======================================================================
# GET / → redirect a /login o /dashboard
# ======================================================================

@web_router.get("/", include_in_schema=False)
def root(request: Request):
    identity = _get_identity_from_cookie(request)
    if identity:
        return RedirectResponse(url="/dashboard", status_code=302)
    return RedirectResponse(url="/login", status_code=302)


# ======================================================================
# GET /login
# ======================================================================

@web_router.get("/login", response_class=HTMLResponse, include_in_schema=False)
def login_page(request: Request):
    """
    Página de login.
    Si el usuario ya tiene cookie válida → redirect al dashboard.
    """
    identity = _get_identity_from_cookie(request)
    if identity:
        return RedirectResponse(url="/dashboard", status_code=302)

    return templates.TemplateResponse(
        request, "login.html",
        {"app_env": settings.APP_ENV},
    )


# ======================================================================
# GET /dashboard
# ======================================================================

@web_router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
def dashboard_page(request: Request):
    """
    Dashboard principal.
    Si no hay cookie válida → redirect a /login.
    """
    identity = _get_identity_from_cookie(request)
    if not identity:
        return RedirectResponse(url="/login", status_code=302)

    return templates.TemplateResponse(request, "dashboard.html")


# ======================================================================
# GET /profile
# ======================================================================

@web_router.get("/profile", response_class=HTMLResponse, include_in_schema=False)
def profile_page(request: Request):
    """
    Página de perfil (cambio de contraseña).
    Si no hay cookie válida → redirect a /login.
    """
    identity = _get_identity_from_cookie(request)
    if not identity:
        return RedirectResponse(url="/login", status_code=302)

    return templates.TemplateResponse(request, "profile.html")


# ======================================================================
# GET /market/symbols
# ======================================================================

@web_router.get("/market/symbols", response_class=HTMLResponse, include_in_schema=False)
def market_symbols_page(request: Request):
    """Lista de símbolos activos. Cualquier usuario autenticado."""
    identity = _get_identity_from_cookie(request)
    if not identity:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse(request, "market/symbols.html")


# ======================================================================
# GET /market/candles
# ======================================================================

@web_router.get("/market/candles", response_class=HTMLResponse, include_in_schema=False)
def market_candles_page(request: Request):
    """Consulta de velas OHLCV. Cualquier usuario autenticado."""
    identity = _get_identity_from_cookie(request)
    if not identity:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse(request, "market/candles.html")


# ======================================================================
# GET /admin/exchanges   (solo admin — redirige si no es admin)
# ======================================================================

@web_router.get("/admin/exchanges", response_class=HTMLResponse, include_in_schema=False)
def admin_exchanges_page(request: Request):
    """Gestión de exchanges. Redirige a /dashboard si no es admin."""
    identity = _get_identity_from_cookie(request)
    if not identity:
        return RedirectResponse(url="/login", status_code=302)
    if int(identity.get("role_id", 0)) != int(settings.AUTH_ADMIN_ROLE_ID):
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse(request, "admin/exchanges.html")


# ======================================================================
# GET /admin/symbols
# ======================================================================

@web_router.get("/admin/symbols", response_class=HTMLResponse, include_in_schema=False)
def admin_symbols_page(request: Request):
    """Gestión de símbolos. Solo admin."""
    identity = _get_identity_from_cookie(request)
    if not identity:
        return RedirectResponse(url="/login", status_code=302)
    if int(identity.get("role_id", 0)) != int(settings.AUTH_ADMIN_ROLE_ID):
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse(request, "admin/symbols.html")


# ======================================================================
# GET /admin/timeframes
# ======================================================================

@web_router.get("/admin/timeframes", response_class=HTMLResponse, include_in_schema=False)
def admin_timeframes_page(request: Request):
    """Gestión de timeframes. Solo admin."""
    identity = _get_identity_from_cookie(request)
    if not identity:
        return RedirectResponse(url="/login", status_code=302)
    if int(identity.get("role_id", 0)) != int(settings.AUTH_ADMIN_ROLE_ID):
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse(request, "admin/timeframes.html")


# ======================================================================
# GET /admin/candles/ingest
# ======================================================================

@web_router.get("/admin/candles/ingest", response_class=HTMLResponse, include_in_schema=False)
def admin_candles_ingest_page(request: Request):
    """Ingestión de velas. Solo admin."""
    identity = _get_identity_from_cookie(request)
    if not identity:
        return RedirectResponse(url="/login", status_code=302)
    if int(identity.get("role_id", 0)) != int(settings.AUTH_ADMIN_ROLE_ID):
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse(request, "admin/candles_ingest.html")


# ======================================================================
# GET /features  (M3 — Feature Engineering)
# ======================================================================

@web_router.get("/features", response_class=HTMLResponse, include_in_schema=False)
def features_page(request: Request):
    """Consulta de indicadores técnicos calculados. Cualquier usuario autenticado."""
    identity = _get_identity_from_cookie(request)
    if not identity:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse(request, "features/index.html")


# ======================================================================
# GET /admin/feature-sets
# ======================================================================

@web_router.get("/admin/feature-sets", response_class=HTMLResponse, include_in_schema=False)
def admin_feature_sets_page(request: Request):
    """Gestión de feature sets y cálculo de indicadores. Solo admin."""
    identity = _get_identity_from_cookie(request)
    if not identity:
        return RedirectResponse(url="/login", status_code=302)
    if int(identity.get("role_id", 0)) != int(settings.AUTH_ADMIN_ROLE_ID):
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse(request, "admin/feature_sets.html")


# ======================================================================
# Módulo 4 — Accounts & Portfolio
# ======================================================================

@web_router.get("/portfolio", response_class=HTMLResponse, include_in_schema=False)
def accounts_page(request: Request):
    """Panel de cuentas de trading del usuario."""
    identity = _get_identity_from_cookie(request)
    if not identity:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse(request, "accounts/index.html")


@web_router.get("/admin/accounts", response_class=HTMLResponse, include_in_schema=False)
def admin_accounts_page(request: Request):
    """Vista admin de todas las cuentas del sistema."""
    identity = _get_identity_from_cookie(request)
    if not identity:
        return RedirectResponse(url="/login", status_code=302)
    if int(identity.get("role_id", 0)) != int(settings.AUTH_ADMIN_ROLE_ID):
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse(request, "admin/accounts.html")


# ======================================================================
# Módulo 5 — Strategies
# ======================================================================

@web_router.get("/strategies", response_class=HTMLResponse, include_in_schema=False)
def strategies_page(request: Request):
    """Lista de estrategias de trading (todos los usuarios autenticados)."""
    identity = _get_identity_from_cookie(request)
    if not identity:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse(request, "strategies/index.html")


@web_router.get("/admin/strategies", response_class=HTMLResponse, include_in_schema=False)
def admin_strategies_page(request: Request):
    """Editor de estrategias (solo administradores)."""
    identity = _get_identity_from_cookie(request)
    if not identity:
        return RedirectResponse(url="/login", status_code=302)
    if int(identity.get("role_id", 0)) != int(settings.AUTH_ADMIN_ROLE_ID):
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse(request, "admin/strategies.html")


# ======================================================================
# Módulo 6 — Agent AI
# ======================================================================

@web_router.get("/agent", response_class=HTMLResponse, include_in_schema=False)
def agent_analyze_page(request: Request):
    """Página del Agente AI — Prompt Maestro (todos los usuarios autenticados)."""
    identity = _get_identity_from_cookie(request)
    if not identity:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse(request, "agent/analyze.html")


# ======================================================================
# Módulo 7 — Bots & Signals
# ======================================================================

@web_router.get("/bots", response_class=HTMLResponse, include_in_schema=False)
def bots_page(request: Request):
    """Panel de bots del usuario — lista bots y sus signals recientes."""
    identity = _get_identity_from_cookie(request)
    if not identity:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse(request, "bots/index.html")


@web_router.get("/admin/bots", response_class=HTMLResponse, include_in_schema=False)
def admin_bots_page(request: Request):
    """Vista admin — todos los bots del sistema."""
    identity = _get_identity_from_cookie(request)
    if not identity:
        return RedirectResponse(url="/login", status_code=302)
    if int(identity.get("role_id", 0)) != int(settings.AUTH_ADMIN_ROLE_ID):
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse(request, "admin/bots.html")
