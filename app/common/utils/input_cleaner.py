# -*- coding: utf-8 -*-

# ======================================================================
# app/common/utils/input_cleaner.py
#
# PROPÓSITO:
# - Limpieza y validación básica de inputs de texto plano.
#
# ALCANCE:
# - NO es sanitización HTML (eso es bleach).
# - NO es formateo UI.
# - Es validación defensiva y normalización básica.
#
# USO:
# - Services llaman estas funciones.
# - Services NO implementan lógica de limpieza propia.
# ======================================================================

from __future__ import annotations

import re


# Regex simple y suficiente para login (no pretende RFC completa)
_EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def clean_email(raw: str) -> str:
    """
    Limpia y valida un email.

    Reglas:
    - strip
    - lower
    - longitud razonable
    - formato básico válido

    Retorna:
    - email limpio (string)

    Lanza:
    - ValueError si es inválido
    """
    if raw is None:
        raise ValueError("email is required")

    email = raw.strip().lower()

    if not email:
        raise ValueError("email is required")

    if len(email) > 255:
        raise ValueError("email is too long")

    if not _EMAIL_REGEX.match(email):
        raise ValueError("email is invalid")

    return email