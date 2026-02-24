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

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.common.config import settings
from app.common.security.jwt.jwt_utils import decode_access_token, JwtCodecError

templates = Jinja2Templates(directory="app/templates")

web_router = APIRouter(tags=["Web"])


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
