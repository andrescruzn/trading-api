# -*- coding: utf-8 -*-

# ======================================================================
# app/common/security/sanitization/html_sanitizer.py
#
# PROPÓSITO:
# - Sanitizar HTML NO confiable usando Bleach (allowlist).
#
# CUÁNDO USARLO:
# - SOLO si algún endpoint permite HTML (rich text).
# - NO usar en login (email/password), porque deben tratarse como texto plano.
#
# POR QUÉ:
# - Prevención defensiva contra XSS cuando se acepta/almacena HTML.
# - Bloquea vectores comunes (scripts, atributos on*, javascript: URLs).
# ======================================================================

from __future__ import annotations

from typing import Iterable, Mapping, Optional

import bleach

# ----------------------------------------------------------------------
# Allowlist mínima (segura) - ajustar SOLO si el dominio lo exige.
# ----------------------------------------------------------------------
DEFAULT_ALLOWED_TAGS: list[str] = [
    "b", "strong", "i", "em", "u",
    "p", "br", "ul", "ol", "li",
    "blockquote", "code", "pre",
    "a",
]

DEFAULT_ALLOWED_ATTRIBUTES: dict[str, list[str]] = {
    # Sin handlers on*; solo atributos seguros para enlaces
    "a": ["href", "title", "rel", "target"],
}

DEFAULT_ALLOWED_PROTOCOLS: list[str] = ["http", "https", "mailto"]


def sanitize_html(
    raw_html: str,
    *,
    allowed_tags: Optional[Iterable[str]] = None,
    allowed_attributes: Optional[Mapping[str, Iterable[str]]] = None,
    allowed_protocols: Optional[Iterable[str]] = None,
    strip: bool = True,
) -> str:
    """
    Sanitiza HTML usando Bleach (allowlist).

    Parámetros clave:
    - strip=True: elimina tags no permitidos (más estricto).
    - allowed_protocols: bloquea href="javascript:..." y similares.
    """
    tags = list(allowed_tags) if allowed_tags is not None else DEFAULT_ALLOWED_TAGS
    attrs = (
        {k: list(v) for k, v in allowed_attributes.items()}
        if allowed_attributes is not None
        else DEFAULT_ALLOWED_ATTRIBUTES
    )
    protocols = list(allowed_protocols) if allowed_protocols is not None else DEFAULT_ALLOWED_PROTOCOLS

    return bleach.clean(
        raw_html,
        tags=tags,
        attributes=attrs,
        protocols=protocols,
        strip=strip,
    )