# -*- coding: utf-8 -*-

# ======================================================================
# app/common/config/settings.py
#
# PROPÓSITO:
# - Centralizar configuración del sistema.
#
# ALCANCE ACTUAL:
# - Variables de entorno desde .env (local) o del sistema (prod).
# - Sin AWS, sin Secrets Manager (por ahora).
#
# NOTA ARQUITECTÓNICA:
# - `dotenv` SOLO se usa aquí.
# - El resto del sistema SOLO consume `settings`.
# ======================================================================

import os
from datetime import timedelta

from dotenv import load_dotenv


# ----------------------------------------------------------------------
# Cargar variables del archivo .env (solo en local)
# ----------------------------------------------------------------------
# En producción, si no existe .env, no pasa nada.
# load_dotenv simplemente no carga nada.
load_dotenv()


class Settings:
    """
    Settings base del sistema.
    No depende de FastAPI ni de ningún framework.
    """

    # ------------------------------------------------------------------
    # Entorno
    # ------------------------------------------------------------------
    APP_ENV: str = os.getenv("APP_ENV", "development")

    # ------------------------------------------------------------------
    # Base de datos
    # ------------------------------------------------------------------
    DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT: str = os.getenv("DB_PORT", "3306")
    DB_NAME: str = os.getenv("DB_NAME", "")
    DB_USER: str = os.getenv("DB_USER", "")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")

    # ------------------------------------------------------------------
    # JWT / Security
    # ------------------------------------------------------------------
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-me")
    JWT_ACCESS_TOKEN_EXPIRES: timedelta = timedelta(
        hours=int(os.getenv("JWT_EXPIRES_H", "24"))
    )

    # ------------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------------
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "*")

    # ------------------------------------------------------------------
    # OpenAPI / Docs
    # ------------------------------------------------------------------
    API_TITLE: str = os.getenv("API_TITLE", "Trading API")
    API_VERSION: str = os.getenv("API_VERSION", "v1")