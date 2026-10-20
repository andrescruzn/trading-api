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


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


class Settings:
    """
    Settings base del sistema.
    """

    def __init__(self) -> None:
        # --------------------------------------------------------------
        # Entorno
        # --------------------------------------------------------------
        # Por defecto "production": si se olvida APP_ENV en un servidor, la app
        # exige secretos reales (fail fast) en vez de arrancar con los de desarrollo.
        self.APP_ENV: str = os.getenv("APP_ENV", "production").strip()

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
            # (5193 = Vite del frontend, que llama a la API directo con CORS)
            self.CORS_ORIGINS: list[str] = [
                "http://localhost:5193",
                "http://127.0.0.1:5193",
                "http://localhost:5173",
                "http://127.0.0.1:5173",
            ]

        # --------------------------------------------------------------
        # OpenAPI / Docs
        # --------------------------------------------------------------
        self.API_TITLE: str = os.getenv("API_TITLE", "Trading App").strip()
        self.API_VERSION: str = os.getenv("API_VERSION", "v1").strip()

        # Prefijo común de todas las rutas REST (la API es headless: el
        # frontend React vive aparte y consume /api/*). /health queda en raíz.
        self.API_PREFIX: str = os.getenv("API_PREFIX", "/api").strip().rstrip("/")

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
        self.SMTP_FROM_NAME: str = os.getenv("SMTP_FROM_NAME", "Trading App").strip()


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
        # Defaults = IDs reales de la tabla `roles`: 1 user, 2 admin, 3 investor.
        admin_role_raw = os.getenv("AUTH_ADMIN_ROLE_ID", "2").strip()
        user_role_raw = os.getenv("AUTH_USER_ROLE_ID", "1").strip()

        self.AUTH_ADMIN_ROLE_ID: int = int(admin_role_raw) if admin_role_raw.isdigit() else 2
        self.AUTH_USER_ROLE_ID: int = int(user_role_raw) if user_role_raw.isdigit() else 1

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

        # Claves anteriores (separadas por comas) que solo se usan para
        # DESCIFRAR mientras se rota la clave: la nueva va en
        # CREDENTIALS_SECRET_KEY y la vieja aquí hasta re-cifrar las cuentas.
        self.CREDENTIALS_PREVIOUS_KEYS: list[str] = [
            key.strip()
            for key in os.getenv("CREDENTIALS_PREVIOUS_KEYS", "").split(",")
            if key.strip()
        ]

        if self.APP_ENV not in ("development", "testing") and not self.CREDENTIALS_SECRET_KEY:
            raise RuntimeError(
                "CREDENTIALS_SECRET_KEY is required in non-development environments"
            )

        # --------------------------------------------------------------
        # OTP
        # --------------------------------------------------------------
        # OTP_HMAC_SECRET: secreto propio para hashear los OTP. Vacío → usa
        #   JWT_SECRET_KEY (compatibilidad); conviene separarlos para que
        #   filtrar uno no comprometa el otro.
        # DEV_RETURN_OTP: devuelve el OTP en la respuesta del login para
        #   probar sin correo. Solo tiene efecto con APP_ENV=development.
        # OTP_MAX_FAILED_ATTEMPTS: intentos fallidos antes de invalidar el código.
        # --------------------------------------------------------------
        self.OTP_HMAC_SECRET: str = (
            os.getenv("OTP_HMAC_SECRET", "").strip() or self.JWT_SECRET_KEY
        )
        self.DEV_RETURN_OTP: bool = (
            self.APP_ENV == "development"
            and os.getenv("DEV_RETURN_OTP", "true").lower() == "true"
        )
        self.OTP_MAX_FAILED_ATTEMPTS: int = _env_int("OTP_MAX_FAILED_ATTEMPTS", 5)

        # --------------------------------------------------------------
        # Proxies de confianza
        # --------------------------------------------------------------
        # Solo si la API corre detrás de un proxy propio (Nginx, Caddy) se
        # confía en X-Forwarded-For para la IP del cliente; si no, cualquiera
        # podría falsearla y saltarse el rate limit.
        # --------------------------------------------------------------
        self.TRUST_PROXY_HEADERS: bool = (
            os.getenv("TRUST_PROXY_HEADERS", "false").lower() == "true"
        )

        # --------------------------------------------------------------
        # LLM — Pool de servicios de Inteligencia Artificial
        # --------------------------------------------------------------
        # LLM_SERVICES: servicios en el orden de rotación (round-robin).
        #   Cada análisis usa el siguiente servicio del turno; si falla,
        #   se prueba el siguiente (failover) en la misma petición.
        #   Los servicios sin API key se omiten.
        #
        # Servicios disponibles (catálogo en app/modules/agent/llm/llm_services.py):
        #   groq       → Groq (SDK `groq`)
        #   gemini     → Google AI Studio (SDK `google-genai`)
        #   ollama     → Ollama Cloud (SDK `ollama`); va de último
        #                porque su capa gratuita es la más limitada.
        # --------------------------------------------------------------
        llm_services_raw = os.getenv("LLM_SERVICES", "groq,gemini,ollama")
        self.LLM_SERVICES: list[str] = [
            name.strip().lower()
            for name in llm_services_raw.split(",")
            if name.strip()
        ]

        self.GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "").strip()
        self.GROQ_MODEL: str = (
            os.getenv("GROQ_MODEL", "").strip() or "moonshotai/kimi-k2-instruct-0905"
        )

        self.GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
        self.GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "").strip() or "gemini-3.5-flash-lite"

        # Ollama Cloud: el modelo va con el nombre de https://ollama.com/api/tags
        # (sin el sufijo :cloud, que solo usa la app/CLI local).
        self.OLLAMA_API_KEY: str = os.getenv("OLLAMA_API_KEY", "").strip()
        self.OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "").strip() or "nemotron-3-ultra"

        # Tiempo máximo por llamada; al vencer se pasa al siguiente servicio.
        # 60 s porque nemotron-3-ultra (550B, con razonamiento) puede pasar de 30 s.
        try:
            self.LLM_TIMEOUT_SECONDS: float = float(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
        except ValueError:
            self.LLM_TIMEOUT_SECONDS = 60.0

        # Temperatura: 0.0 (más determinístico) — 1.0 (más creativo)
        # 0.1 es el valor recomendado para análisis financiero reproducible.
        try:
            self.LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.1"))
        except ValueError:
            self.LLM_TEMPERATURE = 0.1

        # Máximo de tokens en la respuesta del LLM. 4096 porque en los modelos
        # con razonamiento (Gemini 3) los tokens de "thinking" cuentan aquí;
        # con 1024 el JSON puede llegar vacío o cortado.
        try:
            self.LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "4096"))
        except ValueError:
            self.LLM_MAX_TOKENS = 4096

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

        # AGENT_MAX_ENTRY_ATR_DISTANCE: el entry que propone el LLM no puede
        #   alejarse del último cierre más de N × ATR (evita precios inventados).
        # AGENT_ANALYSES_PER_MINUTE: análisis por usuario y minuto (cada uno
        #   cuesta una llamada al LLM).
        self.AGENT_MAX_ENTRY_ATR_DISTANCE: float = _env_float("AGENT_MAX_ENTRY_ATR_DISTANCE", 1.0)
        self.AGENT_ANALYSES_PER_MINUTE: int = _env_int("AGENT_ANALYSES_PER_MINUTE", 6)

        # --------------------------------------------------------------
        # Trading — Salvaguardas de ejecución (M8)
        # --------------------------------------------------------------
        # TRADING_ENABLED: kill switch global. false → no sale ninguna orden.
        # TRADING_LIVE_ENABLED: false → solo se ejecutan órdenes paper.
        # ORDER_MAX_NOTIONAL: valor máximo (qty × precio) de una orden, en la
        #   moneda de cotización. 0 = sin tope global (el bot puede fijar
        #   el suyo en risk_params.max_notional).
        # --------------------------------------------------------------
        self.TRADING_ENABLED: bool = os.getenv("TRADING_ENABLED", "true").lower() == "true"
        self.TRADING_LIVE_ENABLED: bool = (
            os.getenv("TRADING_LIVE_ENABLED", "false").lower() == "true"
        )
        self.ORDER_MAX_NOTIONAL: float = _env_float("ORDER_MAX_NOTIONAL", 10000.0)
        # ORDER_REQUESTS_PER_MINUTE: crear, cancelar o aprobar órdenes por
        #   usuario y minuto (cada una puede llegar al exchange).
        self.ORDER_REQUESTS_PER_MINUTE: int = _env_int("ORDER_REQUESTS_PER_MINUTE", 20)

        # ORDER_NATIVE_STOP_LOSS: en live, al abrir una posición desde una señal
        #   se deja el stop loss como orden en el exchange (protege aunque la
        #   API esté caída). Si el exchange no lo soporta, vigila el scheduler.
        # LIVE_USE_SANDBOX: usa la testnet del exchange (claves de testnet)
        #   para probar el circuito live sin dinero real.
        self.ORDER_NATIVE_STOP_LOSS: bool = (
            os.getenv("ORDER_NATIVE_STOP_LOSS", "true").lower() == "true"
        )
        self.LIVE_USE_SANDBOX: bool = os.getenv("LIVE_USE_SANDBOX", "false").lower() == "true"

        # --------------------------------------------------------------
        # Modo de ejecución de los agentes (manual / approval / auto)
        # --------------------------------------------------------------
        # TRADING_LIVE_AUTO_ENABLED: permite agentes `auto` en live (órdenes
        #   reales sin aprobación humana). false por defecto.
        # SIGNAL_APPROVAL_TTL_MINUTES: minutos para aprobar una señal si el
        #   agente no fija los suyos (approval_ttl_minutes).
        # SIGNALS_AUTO_MIN_TIMEFRAME_SECONDS: timeframe mínimo para señales
        #   automáticas (por debajo, el coste de IA se dispara). 900 = 15m.
        # AGENT_MAX_AUTO_ANALYSES_PER_DAY: análisis automáticos por usuario y día.
        # --------------------------------------------------------------
        self.TRADING_LIVE_AUTO_ENABLED: bool = (
            os.getenv("TRADING_LIVE_AUTO_ENABLED", "false").lower() == "true"
        )
        self.SIGNAL_APPROVAL_TTL_MINUTES: int = _env_int("SIGNAL_APPROVAL_TTL_MINUTES", 60)
        self.SIGNALS_AUTO_MIN_TIMEFRAME_SECONDS: int = _env_int(
            "SIGNALS_AUTO_MIN_TIMEFRAME_SECONDS", 900
        )
        self.AGENT_MAX_AUTO_ANALYSES_PER_DAY: int = _env_int("AGENT_MAX_AUTO_ANALYSES_PER_DAY", 96)

        # --------------------------------------------------------------
        # Alerts — Canales de notificación
        # --------------------------------------------------------------
        self.TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        self.TELEGRAM_DEFAULT_CHAT_ID: str = os.getenv("TELEGRAM_DEFAULT_CHAT_ID", "").strip()

        # Telegram por usuario (vincular chat + aprobar señales con botones)
        # TELEGRAM_BOT_USERNAME: @usuario del bot, sin @ (para el enlace t.me/...).
        # TELEGRAM_UPDATES_MODE: cómo llegan las respuestas de Telegram:
        #   off      → no se procesan (solo se envían avisos)
        #   polling  → el scheduler consulta getUpdates (desarrollo, sin URL pública)
        #   webhook  → Telegram llama POST /api/telegram/webhook (producción)
        # TELEGRAM_WEBHOOK_SECRET: secret_token registrado con setWebhook; el
        #   webhook rechaza toda petición sin esa cabecera.
        self.TELEGRAM_BOT_USERNAME: str = (
            os.getenv("TELEGRAM_BOT_USERNAME", "").strip().lstrip("@")
        )
        self.TELEGRAM_UPDATES_MODE: str = (
            os.getenv("TELEGRAM_UPDATES_MODE", "off").strip().lower()
        )
        self.TELEGRAM_WEBHOOK_SECRET: str = os.getenv("TELEGRAM_WEBHOOK_SECRET", "").strip()

        # URL del frontend (enlaces en Telegram y correos)
        self.FRONTEND_URL: str = (
            os.getenv("FRONTEND_URL", "http://localhost:5193").strip().rstrip("/")
        )
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