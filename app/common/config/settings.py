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
        self.CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "*").strip()

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