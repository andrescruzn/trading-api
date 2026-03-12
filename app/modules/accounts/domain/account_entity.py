# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/accounts/domain/account_entity.py
#
# Entidad de dominio: Account.
# Representa una cuenta de trading asociada a un usuario y un exchange.
# ======================================================================

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional


class Account:
    """
    Entidad de dominio: Account.

    Una cuenta vincula a un usuario con un exchange y define el modo
    de operación (paper o live). Las credenciales de API se almacenan
    cifradas en `meta['enc_creds']`.

    Modos válidos:    paper | live
    Estados válidos:  active | suspended
    """

    VALID_MODES = ("paper", "live")
    VALID_STATUSES = ("active", "suspended")

    def __init__(
        self,
        id: int,
        user_id: int,
        name: str,
        mode: str,
        meta: dict[str, Any],
        exchange_id: Optional[int] = None,
        base_currency: str = "USD",
        status: str = "active",
        credentials_ref: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        # Campo de presentación (no persistido)
        exchange_name: Optional[str] = None,
    ):
        self.id = id
        self.user_id = user_id
        self.exchange_id = exchange_id
        self.name = name
        self.mode = mode
        self.base_currency = base_currency
        self.status = status
        self.credentials_ref = credentials_ref
        self.meta = meta
        self.created_at = created_at
        self.updated_at = updated_at
        self.exchange_name = exchange_name

    def is_active(self) -> bool:
        return self.status == "active"

    def belongs_to(self, user_id: int) -> bool:
        return self.user_id == user_id
