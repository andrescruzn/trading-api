# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/market/domain/timeframe_entity.py
#
# Entidad de dominio: Timeframe (marco temporal de velas).
# ======================================================================

from __future__ import annotations


class Timeframe:
    """
    Entidad de dominio: Timeframe.

    Representa un marco temporal: 1m, 5m, 15m, 1h, 4h, 1d, etc.
    El campo `seconds` permite comparaciones y ordenamiento.
    """

    def __init__(
        self,
        id: int,
        code: str,
        seconds: int,
    ):
        self.id = id
        self.code = code
        self.seconds = seconds

    def is_valid(self) -> bool:
        """Un timeframe es válido si su código no está vacío y seconds > 0."""
        return bool(self.code.strip()) and self.seconds > 0
