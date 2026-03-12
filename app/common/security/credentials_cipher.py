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
# - En desarrollo sin clave configurada se usa una clave fija de ejemplo
#   (nunca usar en producción).
#
# USO:
#   cipher = CredentialsCipher(settings.CREDENTIALS_SECRET_KEY)
#   token = cipher.encrypt(api_key="abc", api_secret="xyz")
#   creds = cipher.decrypt(token)
#   # creds == {"api_key": "abc", "api_secret": "xyz"}
# ======================================================================

from __future__ import annotations

import json

from cryptography.fernet import Fernet


# Clave de desarrollo (solo para entornos locales sin .env configurado)
_DEV_KEY = b"ZmRldmtleS1mb3ItZGV2LW9ubHktMzItY2hhcnM="


class CredentialsCipher:
    """
    Cifrado/descifrado de credenciales de API con Fernet.

    Fernet garantiza:
    - Cifrado AES-128-CBC
    - HMAC-SHA256 para autenticidad
    - Timestamp en el token (permite expiración si se necesita)
    """

    def __init__(self, secret_key: str | None = None):
        # Si no hay clave, usar dev key (solo development)
        key_bytes = secret_key.encode() if secret_key else _DEV_KEY
        self._fernet = Fernet(key_bytes)

    def encrypt(self, api_key: str, api_secret: str) -> str:
        """
        Cifra api_key + api_secret en un token Fernet.

        Returns:
            Token cifrado como string UTF-8.
        """
        payload = json.dumps({"api_key": api_key, "api_secret": api_secret})
        return self._fernet.encrypt(payload.encode()).decode()

    def decrypt(self, token: str) -> dict[str, str]:
        """
        Descifra un token y retorna {"api_key": ..., "api_secret": ...}.

        Raises:
            cryptography.fernet.InvalidToken: si el token es inválido o fue alterado.
        """
        raw = self._fernet.decrypt(token.encode())
        return json.loads(raw.decode())
