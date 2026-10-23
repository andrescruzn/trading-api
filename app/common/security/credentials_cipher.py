# -*- coding: utf-8 -*-

# ======================================================================
# app/common/security/credentials_cipher.py
#
# PROPÓSITO:
# - Cifrar/descifrar credenciales de API (api_key + api_secret) con
#   cifrado simétrico Fernet (AES-128-CBC + HMAC-SHA256).
#
# DECISIÓN:
# - Las credenciales se cifran juntas como JSON antes de persistir.
# - La clave Fernet se lee de CREDENTIALS_SECRET_KEY en settings.
# - Rotación con MultiFernet: se cifra siempre con la clave actual y se
#   descifra con la actual o con cualquiera de CREDENTIALS_PREVIOUS_KEYS.
#   `rotate(token)` re-cifra un token viejo con la clave actual.
# - La clave fija de ejemplo solo se usa con APP_ENV=development/testing:
#   fuera de ahí settings exige CREDENTIALS_SECRET_KEY (fail fast).
#
# USO:
#   cipher = CredentialsCipher.from_settings()
#   token = cipher.encrypt(api_key="abc", api_secret="xyz")
#   creds = cipher.decrypt(token)
#   # creds == {"api_key": "abc", "api_secret": "xyz"}
# ======================================================================

from __future__ import annotations

import json

from cryptography.fernet import Fernet, MultiFernet


# Clave de desarrollo (solo para entornos locales sin .env configurado)
_DEV_KEY = b"QwM6cMsRGoJCjmK2nlqZuH3Or-ftjSx4jIfi-jdHahM="


class CredentialsCipher:
    """
    Cifrado/descifrado de credenciales de API con Fernet.

    Fernet garantiza:
    - Cifrado AES-128-CBC
    - HMAC-SHA256 para autenticidad
    - Timestamp en el token (permite expiración si se necesita)
    """

    def __init__(
        self,
        secret_key: str | None = None,
        previous_keys: list[str] | None = None,
    ):
        if not secret_key:
            # Lazy import para evitar ciclos
            from app.common.config import settings

            if settings.APP_ENV not in ("development", "testing"):
                raise RuntimeError("CREDENTIALS_SECRET_KEY is required outside development")

        current = Fernet(secret_key.encode() if secret_key else _DEV_KEY)
        older = [Fernet(key.encode()) for key in (previous_keys or [])]
        self._fernet = MultiFernet([current, *older])

    @classmethod
    def from_settings(cls) -> "CredentialsCipher":
        """Construye el cipher con la clave actual y las anteriores de settings."""
        from app.common.config import settings

        return cls(settings.CREDENTIALS_SECRET_KEY, settings.CREDENTIALS_PREVIOUS_KEYS)

    def encrypt(self, api_key: str, api_secret: str) -> str:
        """
        Cifra api_key + api_secret en un token Fernet.

        Returns:
            Token cifrado como string UTF-8.
        """
        payload = json.dumps({"api_key": api_key, "api_secret": api_secret})
        return self._fernet.encrypt(payload.encode()).decode()

    def encrypt_dict(self, data: dict[str, str]) -> str:
        """
        Cifra cualquier diccionario de textos (p. ej. los datos bancarios de un
        medio de pago del fondo). `decrypt` lo devuelve tal cual.
        """
        return self._fernet.encrypt(json.dumps(data).encode()).decode()

    def decrypt(self, token: str) -> dict[str, str]:
        """
        Descifra un token y retorna {"api_key": ..., "api_secret": ...}.

        Raises:
            cryptography.fernet.InvalidToken: si el token es inválido o fue alterado.
        """
        raw = self._fernet.decrypt(token.encode())
        return json.loads(raw.decode())

    def rotate(self, token: str) -> str:
        """Re-cifra un token (de cualquier clave conocida) con la clave actual."""
        return self._fernet.rotate(token.encode()).decode()
