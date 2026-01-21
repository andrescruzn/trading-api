# ======================================================================
# app/common/security/jwt/jwt_settings.py
# -*- coding: utf-8 -*-
#
# PROPÓSITO (Screaming Architecture):
# - Este archivo define la configuración de JWT como un Value Object.
#
# POR QUÉ:
# - Centralizar settings evita duplicación (DRY) y reduce errores por
#   configuraciones inconsistentes en diferentes módulos.
# - La configuración debe ser inmutable para evitar mutaciones accidentales
#   en runtime (seguridad + predictibilidad).
#
# PATRÓN APLICADO:
# - Value Object (inmutable): JwtSettings
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
import os


# ======================================================================
# 1) Value Object: JwtSettings (inmutable)
# ======================================================================
@dataclass(frozen=True)
class JwtSettings:
    """
    Value Object inmutable de configuración JWT.

    NOTAS DE DISEÑO:
    - frozen=True evita que un desarrollador cambie valores críticos
      (ej. secret_key, ttl) luego de instanciado. Esto es útil en seguridad.
    - Este objeto NO contiene lógica de negocio, solo datos de configuración.
    """

    # ------------------------------------------------------------------
    # secret_key:
    # - Clave usada para firmar tokens (HS256).
    # - Debe ser larga, aleatoria y provenir de variables de entorno.
    # ------------------------------------------------------------------
    secret_key: str

    # ------------------------------------------------------------------
    # algorithm:
    # - Algoritmo permitido para firma/verificación.
    # - Fijarlo reduce riesgos como "alg confusion" (token declarando otro alg).
    # ------------------------------------------------------------------
    algorithm: str = "HS256"

    # ------------------------------------------------------------------
    # access_token_ttl_seconds:
    # - TTL de access token en segundos.
    # - Por defecto 1 hora (3600).
    # ------------------------------------------------------------------
    access_token_ttl_seconds: int = 60 * 60


# ======================================================================
# 2) Loader: load_jwt_settings
# ======================================================================
def load_jwt_settings() -> JwtSettings:
    """
    Carga configuración JWT desde variables de entorno.

    VARIABLES ESPERADAS:
    - JWT_SECRET_KEY (obligatoria)
    - JWT_ACCESS_TTL_SECONDS (opcional, default 3600)

    POR QUÉ AQUÍ:
    - Mantener la carga de env en un único punto evita duplicación
      y facilita testear (puedes mockear env o inyectar settings).
    """

    # ------------------------------------------------------------------
    # 1) Leer secret desde env
    # ------------------------------------------------------------------
    secret = os.getenv("JWT_SECRET_KEY", "").strip()
    if not secret:
        # --------------------------------------------------------------
        # Decisión: fallar temprano si falta el secreto.
        # - En seguridad, un secreto vacío debe romper el arranque.
        # --------------------------------------------------------------
        raise RuntimeError("JWT_SECRET_KEY is required")

    # ------------------------------------------------------------------
    # 2) Leer TTL desde env (default 3600)
    # ------------------------------------------------------------------
    ttl_raw = os.getenv("JWT_ACCESS_TTL_SECONDS", "3600").strip()

    # ------------------------------------------------------------------
    # 3) Construir y retornar el Value Object (inmutable)
    # ------------------------------------------------------------------
    return JwtSettings(
        secret_key=secret,
        access_token_ttl_seconds=int(ttl_raw),
    )