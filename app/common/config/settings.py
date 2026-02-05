# -*- coding: utf-8 -*-

# ======================================================================
# app/common/config/settings.py
#
# PROPÓSITO:
# - Centralizar configuración del sistema en un único punto.
#
# DECISIÓN:
# - Settings como instancia (no class attributes) para:
#   - testear fácil
#   - evitar valores “congelados” en import time
#   - validar faltantes críticos (fail fast)
#
# JWT:
# - Token dura 1 hora por defecto (60 min).
# - Override por env: JWT_ACCESS_TOKEN_EXPIRES_MINUTES
# - Legacy: JWT_EXPIRES_H
# ======================================================================

from __future__ import annotations

import os
from datetime import timedelta

from dotenv import load_dotenv


load_dotenv()


class Settings:
    """
    Settings base del sistema.
    """

    def __init__(self) -> None:
        # --------------------------------------------------------------
        # Entorno
        # --------------------------------------------------------------
        self.APP_ENV: str = os.getenv("APP_ENV", "development").strip()

        # --------------------------------------------------------------
        # Base de datos
        # --------------------------------------------------------------
        self.DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1").strip()
        self.DB_PORT: str = os.getenv("DB_PORT", "3306").strip()
        self.DB_NAME: str = os.getenv("DB_NAME", "").strip()
        self.DB_USER: str = os.getenv("DB_USER", "").strip()
        self.DB_PASSWORD: str = os.getenv("DB_PASSWORD", "").strip()

        # --------------------------------------------------------------
        # JWT / Security
        # --------------------------------------------------------------
        self.JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "").strip()
        self.JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256").strip()

        # Fail fast fuera de development
        if self.APP_ENV != "development" and not self.JWT_SECRET_KEY:
            raise RuntimeError("JWT_SECRET_KEY is required in non-development environments")

        # Dev fallback (para que puedas correr local sin env)
        if self.APP_ENV == "development" and not self.JWT_SECRET_KEY:
            self.JWT_SECRET_KEY = "dev-only-change-me"

        # --------------------------------------------------------------
        # Expiración token (default 1 hora)
        # --------------------------------------------------------------
        jwt_minutes_raw = os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "0").strip()
        jwt_hours_legacy_raw = os.getenv("JWT_EXPIRES_H", "0").strip()

        jwt_minutes = 0
        jwt_hours_legacy = 0

        try:
            jwt_minutes = int(jwt_minutes_raw)
        except ValueError:
            jwt_minutes = 0

        try:
            jwt_hours_legacy = int(jwt_hours_legacy_raw)
        except ValueError:
            jwt_hours_legacy = 0

        if jwt_minutes > 0:
            self.JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=jwt_minutes)
        elif jwt_hours_legacy > 0:
            self.JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=jwt_hours_legacy)
        else:
            self.JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=60)  # 1 hora

        # --------------------------------------------------------------
        # CORS
        # --------------------------------------------------------------
        # SEGURIDAD:
        # - En producción, CORS_ORIGINS debe estar configurado explícitamente.
        # - En desarrollo, permite localhost por defecto.
        # - Formato: lista separada por comas (ej: "https://app.com,https://admin.app.com")
        # --------------------------------------------------------------
        cors_raw = os.getenv("CORS_ORIGINS", "").strip()

        if cors_raw:
            # Parsear lista de orígenes permitidos
            self.CORS_ORIGINS: list[str] = [
                origin.strip()
                for origin in cors_raw.split(",")
                if origin.strip()
            ]
        else:
            # Fail-fast en producción si no está configurado
            if self.APP_ENV not in ("development", "testing"):
                raise RuntimeError(
                    "CORS_ORIGINS is required in production environments. "
                    "Set it to a comma-separated list of allowed origins."
                )
            # Default seguro para desarrollo
            self.CORS_ORIGINS: list[str] = [
                "http://localhost:3000",
                "http://localhost:5173",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:5173",
                "http://127.0.0.1:8000",
            ]

        # --------------------------------------------------------------
        # OpenAPI / Docs
        # --------------------------------------------------------------
        self.API_TITLE: str = os.getenv("API_TITLE", "Trading API").strip()
        self.API_VERSION: str = os.getenv("API_VERSION", "v1").strip()

        # --------------------------------------------------------------
        # SMTP / Mailer
        # --------------------------------------------------------------
        self.SMTP_HOST: str = os.getenv("SMTP_HOST", "").strip()
        self.SMTP_PORT: int = int(os.getenv("SMTP_PORT", "465"))

        self.SMTP_USE_SSL: bool = os.getenv("SMTP_USE_SSL", "true").lower() == "true"
        self.SMTP_USE_STARTTLS: bool = os.getenv("SMTP_USE_STARTTLS", "false").lower() == "true"

        self.SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "").strip()
        self.SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "").strip()

        self.SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", self.SMTP_USERNAME).strip()
        self.SMTP_FROM_NAME: str = os.getenv("SMTP_FROM_NAME", "Trading AI").strip()


        # --------------------------------------------------------------
        # AUTH / Roles (IDs en DB)
        # --------------------------------------------------------------
        # PROPÓSITO:
        # - Centralizar IDs de roles para autorización en guards.
        # - Evita hardcodear "1" o "2" en código.
        #
        # NOTA:
        # - Estos IDs son "infra" (DB), pero se usan como configuración
        #   para reglas simples (admin accede a todo).
        # --------------------------------------------------------------
        admin_role_raw = os.getenv("AUTH_ADMIN_ROLE_ID", "1").strip()
        user_role_raw = os.getenv("AUTH_USER_ROLE_ID", "2").strip()

        self.AUTH_ADMIN_ROLE_ID: int = int(admin_role_raw) if admin_role_raw.isdigit() else 1
        self.AUTH_USER_ROLE_ID: int = int(user_role_raw) if user_role_raw.isdigit() else 2

        # --------------------------------------------------------------
        # AUTH / Cookie Settings
        # --------------------------------------------------------------
        # PROPÓSITO:
        # - Configuración de cookies HTTP-only para autenticación segura.
        # - El frontend React NO necesita acceder al token (protección XSS).
        #
        # SEGURIDAD:
        # - HttpOnly: JavaScript no puede leer la cookie.
        # - Secure: Solo se envía por HTTPS (producción).
        # - SameSite=Lax: Protección CSRF básica (cookies no se envían
        #   en requests cross-site excepto navegación top-level).
        # --------------------------------------------------------------
        self.AUTH_COOKIE_NAME: str = os.getenv("AUTH_COOKIE_NAME", "access_token").strip()

        # Secure=True en producción (HTTPS requerido)
        self.AUTH_COOKIE_SECURE: bool = self.APP_ENV not in ("development", "testing")

        # SameSite: Lax es el balance entre seguridad y usabilidad
        # - "Lax": cookie se envía en navegación top-level (links) pero NO en
        #   requests cross-site (iframes, AJAX desde otro dominio).
        # - "Strict": más seguro pero puede romper flujos de OAuth.
        # - "None": requiere Secure=True, permite cross-site (solo si es necesario).
        self.AUTH_COOKIE_SAMESITE: str = os.getenv("AUTH_COOKIE_SAMESITE", "Lax").strip()

        # Path: "/" para que la cookie se envíe en todas las rutas
        self.AUTH_COOKIE_PATH: str = os.getenv("AUTH_COOKIE_PATH", "/").strip()

        # Domain: None = dominio del servidor que emite la cookie
        # En producción puede ser ".tudominio.com" para subdominios
        cookie_domain_raw = os.getenv("AUTH_COOKIE_DOMAIN", "").strip()
        self.AUTH_COOKIE_DOMAIN: str | None = cookie_domain_raw if cookie_domain_raw else None