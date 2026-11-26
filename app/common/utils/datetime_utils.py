# -*- coding: utf-8 -*-

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

BOGOTA_TZ = ZoneInfo("America/Bogota")


def utc_now() -> datetime:
    """
    Reloj estándar del backend.

    Regla:
    - Siempre devolvemos UTC aware para evitar choques naive/aware.
    """
    return datetime.now(timezone.utc)


def ensure_aware_utc(dt: datetime | None) -> datetime | None:
    """
    Normaliza datetimes que vienen de DB (a veces naive) para poder compararlos.

    Reglas:
    - None -> None
    - Naive -> se asume UTC (porque MySQL muchas veces NO trae tzinfo)
    - Aware -> se convierte a UTC
    """
    if dt is None:
        return None

    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


def utc_to_bogota(dt: datetime | None) -> datetime | None:
    """
    Convierte datetime UTC (aware) a hora de Bogotá.

    Reglas:
    - None → None
    - Naive → lo normalizamos a UTC primero (defensivo)
    """
    dt_utc = ensure_aware_utc(dt)
    if dt_utc is None:
        return None

    return dt_utc.astimezone(BOGOTA_TZ)

def to_iso_utc(dt: datetime | None) -> str | None:
    """
    Serializa un datetime para la API: ISO 8601 en UTC con offset explícito.

    Contrato front ↔ back:
    - La BD guarda UTC y la API responde SIEMPRE `...+00:00`.
    - El front convierte a hora de Colombia (America/Bogota, UTC-5) al pintar.

    Por qué no basta `dt.isoformat()`:
    - MySQL devuelve datetimes naive; `isoformat()` los deja sin offset
      (`2026-10-23T15:00:00`) y el navegador los interpreta como hora local.
    """
    dt_utc = ensure_aware_utc(dt)
    return dt_utc.isoformat() if dt_utc else None
