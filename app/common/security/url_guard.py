# -*- coding: utf-8 -*-

# ======================================================================
# app/common/security/url_guard.py
#
# PROPÓSITO:
# - Proteger las llamadas salientes a URLs que escribe un usuario (webhooks
#   de alertas) contra SSRF: que la API termine llamando a servicios
#   internos (MySQL en localhost, metadatos de la nube 169.254.169.254,
#   la red privada).
#
# REGLAS:
# - Solo https, sin usuario/contraseña en la URL, ≤ 2048 caracteres.
# - El host no puede ser localhost ni una IP privada/reservada.
# - Al enviar, el host se resuelve y TODAS sus IPs deben ser públicas
#   (un dominio público puede apuntar a 127.0.0.1).
#
# LIMITACIÓN CONOCIDA:
# - Entre la resolución y la conexión hay una ventana (DNS rebinding con
#   TTL 0). El riesgo residual es bajo con redirects desactivados; cerrarlo
#   del todo exige un proxy de salida (egress) que filtre IPs.
# ======================================================================

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlsplit

_MAX_URL_LENGTH = 2048
_BLOCKED_HOSTNAMES = frozenset({"localhost", "localhost.localdomain", "metadata.google.internal"})


def _is_public_ip(value: str) -> bool:
    try:
        ip = ipaddress.ip_address(value)
    except ValueError:
        return False
    # ::ffff:127.0.0.1 es 127.0.0.1: se evalúa la IPv4 real
    if ip.version == 6 and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped
    return ip.is_global and not ip.is_multicast


def is_allowed_webhook_url(url: object) -> bool:
    """
    Validación estática (sin red): forma de la URL y host no interno.

    Se usa al guardar la regla; al enviar se valida además la resolución DNS
    con `resolves_to_public_ips`.
    """
    if not isinstance(url, str) or not url or len(url) > _MAX_URL_LENGTH:
        return False

    try:
        parts = urlsplit(url.strip())
        port = parts.port  # lanza ValueError si el puerto no es válido
    except ValueError:
        return False

    if parts.scheme != "https" or not parts.hostname:
        return False
    if parts.username or parts.password:
        return False
    if port is not None and not 1 <= port <= 65535:
        return False

    host = parts.hostname.lower().rstrip(".")
    if host in _BLOCKED_HOSTNAMES or host.endswith(".localhost") or host.endswith(".internal"):
        return False

    # Host escrito como IP: debe ser pública
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return "." in host  # nombres sin punto (intranet) no se aceptan
    return _is_public_ip(host)


def resolves_to_public_ips(url: str) -> bool:
    """True si todas las IPs a las que resuelve el host de la URL son públicas."""
    if not is_allowed_webhook_url(url):
        return False

    parts = urlsplit(url.strip())
    try:
        infos = socket.getaddrinfo(parts.hostname, parts.port or 443, proto=socket.IPPROTO_TCP)
    except (socket.gaierror, UnicodeError):
        return False

    addresses = {info[4][0] for info in infos}
    return bool(addresses) and all(_is_public_ip(address) for address in addresses)
