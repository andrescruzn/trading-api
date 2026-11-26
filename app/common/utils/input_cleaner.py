# -*- coding: utf-8 -*-

# ======================================================================
# app/common/utils/input_cleaner.py
#
# PROPÓSITO:
# - Limpieza y validación básica de inputs de texto plano.
# ======================================================================

from __future__ import annotations

import re


_EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def clean_email(raw: str) -> str:
    """
    Limpia y valida un email.
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


def clean_str(raw: str, *, min_len: int = 1, max_len: int = 255) -> str:
    """
    Limpia y valida texto plano.

    Reglas:
    - strip
    - no vacío (min_len)
    - longitud máxima (max_len)
    """
    if raw is None:
        raise ValueError("value is required")

    value = str(raw).strip()

    if len(value) < int(min_len):
        raise ValueError("value is too short")

    if len(value) > int(max_len):
        raise ValueError("value is too long")

    return value