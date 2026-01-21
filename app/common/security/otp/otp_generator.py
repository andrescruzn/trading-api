# app/common/security/otp/otp_generator.py
# -*- coding: utf-8 -*-

# ======================================================================
# app/common/security/otp/otp_generator.py
#
# PROPÓSITO:
# - Generar OTP numérico seguro (defensa contra predicción).
#
# POR QUÉ:
# - El OTP debe ser impredecible (usar secrets, no random).
# ======================================================================

from __future__ import annotations

import secrets


def generate_numeric_otp(length: int = 6) -> str:
    """
    Genera un OTP numérico de longitud 'length'.

    Decisiones:
    - Usamos secrets para seguridad criptográfica.
    - OTP numérico para facilidad de ingreso.
    """
    if length <= 0:
        raise ValueError("OTP length must be > 0")

    # Genera dígitos criptográficamente seguros
    return "".join(str(secrets.randbelow(10)) for _ in range(length))