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
                "http://localhost:4321",
                "http://localhost:5173",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:4321",
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

        investor_role_raw = os.getenv("AUTH_INVESTOR_ROLE_ID", "3").strip()
        self.AUTH_INVESTOR_ROLE_ID: int = int(investor_role_raw) if investor_role_raw.isdigit() else 3

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

        # --------------------------------------------------------------
        # Credentials Cipher
        # --------------------------------------------------------------
        # PROPÓSITO:
        # - Clave Fernet (base64 de 32 bytes) para cifrar credenciales
        #   de API (api_key + api_secret) de cuentas de exchange.
        #
        # GENERAR UNA CLAVE:
        #   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
        #
        # SEGURIDAD:
        # - En producción DEBE estar configurada en el .env.
        # - En desarrollo se usa una clave fija de fallback (insegura).
        # --------------------------------------------------------------
        self.CREDENTIALS_SECRET_KEY: str | None = (
            os.getenv("CREDENTIALS_SECRET_KEY", "").strip() or None
        )

        # --------------------------------------------------------------
        # LLM — Proveedor de Inteligencia Artificial
        # --------------------------------------------------------------
        # Providers soportados:
        #   openai    → api.openai.com (GPT-4o, GPT-5, etc.)
        #   anthropic → api.anthropic.com (Claude Opus, Sonnet, etc.)
        #   gemini    → generativelanguage.googleapis.com (Gemini 2.5 Pro, etc.)
        #   xai       → api.x.ai (Grok 4, etc.)
        #   deepseek  → api.deepseek.com (DeepSeek R1, etc.)
        #   ollama    → localhost:11434 (modelos locales)
        #
        # NOTA: gemini, xai, deepseek y ollama usan la librería openai
        #       con una base_url distinta (API compatible OpenAI).
        # --------------------------------------------------------------
        self.LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai").strip().lower()
        self.LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o").strip()
        self.LLM_API_KEY: str = os.getenv("LLM_API_KEY", "").strip()

        # Base URL personalizada (None = usa la URL por defecto del provider)
        llm_base_url_raw = os.getenv("LLM_BASE_URL", "").strip()
        self.LLM_BASE_URL: str | None = llm_base_url_raw or None

        # Temperatura: 0.0 (más determinístico) — 1.0 (más creativo)
        # 0.1 es el valor recomendado para análisis financiero reproducible.
        try:
            self.LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.1"))
        except ValueError:
            self.LLM_TEMPERATURE = 0.1

        # Máximo de tokens en la respuesta del LLM
        try:
            self.LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "1024"))
        except ValueError:
            self.LLM_MAX_TOKENS = 1024

        # --------------------------------------------------------------
        # Agent — Configuración del Agente de Trading
        # --------------------------------------------------------------
        # AGENT_MIN_RR_RATIO: mínimo ratio Recompensa/Riesgo para aprobar.
        #   Valor 2.0 = ganancia proyectada >= 2× el riesgo asumido.
        # AGENT_MASTER_PROMPT: prompt del sistema que instruye al LLM.
        #   Si está vacío, se usa el prompt maestro por defecto.
        # --------------------------------------------------------------
        try:
            self.AGENT_MIN_RR_RATIO: float = float(os.getenv("AGENT_MIN_RR_RATIO", "2.0"))
        except ValueError:
            self.AGENT_MIN_RR_RATIO = 2.0

        agent_prompt_raw = os.getenv("AGENT_MASTER_PROMPT", "").strip()
        self.AGENT_MASTER_PROMPT: str = agent_prompt_raw or ""

        # --------------------------------------------------------------
        # Alerts — Canales de notificación
        # --------------------------------------------------------------
        self.TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        self.TELEGRAM_DEFAULT_CHAT_ID: str = os.getenv("TELEGRAM_DEFAULT_CHAT_ID", "").strip()
        self.DESKTOP_NOTIFICATIONS_ENABLED: bool = (
            os.getenv("DESKTOP_NOTIFICATIONS_ENABLED", "false").lower() == "true"
        )

        # --------------------------------------------------------------
        # Scheduler — Actualización automática de velas y features
        # --------------------------------------------------------------
        # SCHEDULER_ENABLED: false para deshabilitar (tests, entorno manual).
        # SCHEDULER_INTERVAL_SECONDS: cada cuántos segundos corre el ciclo.
        #   Default 60 s — revisa cada minuto qué pares necesitan vela nueva.
        # SCHEDULER_RETENTION_CANDLES: cuántas velas mantener por par.
        #   Default 500 — suficiente para EMA200 (~20 días en 1h).
        # --------------------------------------------------------------
        self.SCHEDULER_ENABLED: bool = (
            os.getenv("SCHEDULER_ENABLED", "true").lower() == "true"
        )

        try:
            self.SCHEDULER_INTERVAL_SECONDS: int = int(
                os.getenv("SCHEDULER_INTERVAL_SECONDS", "60")
            )
        except ValueError:
            self.SCHEDULER_INTERVAL_SECONDS = 60

        try:
            self.SCHEDULER_RETENTION_CANDLES: int = int(
                os.getenv("SCHEDULER_RETENTION_CANDLES", "500")
            )
        except ValueError:
            self.SCHEDULER_RETENTION_CANDLES = 500