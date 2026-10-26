# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/accounts/rest/wallet/error_messages.py
#
# Textos de UI de la billetera de la plataforma (super admin y socio).
# ======================================================================

WALLET_ERROR_MESSAGES: dict[str, str] = {
    "WALLET_NOT_CONFIGURED": (
        "Aún no hay billetera de la plataforma. Elige la cuenta de exchange que guarda el dinero del fondo."
    ),
    "WALLET_ACCOUNT_NOT_FOUND": "No encontramos esa cuenta.",
    "WALLET_ACCOUNT_INACTIVE": (
        "La cuenta de la billetera está suspendida. Actívala en Mis cuentas para leer su saldo."
    ),
    "WALLET_ACCOUNT_NO_EXCHANGE": (
        "La cuenta no tiene exchange. Elígelo en Mis cuentas antes de usarla como billetera."
    ),
    "WALLET_ACCOUNT_NO_CREDENTIALS": (
        "La cuenta live no tiene API key. Agrégala en Mis cuentas para poder leer el saldo."
    ),
    "WALLET_CREDENTIALS_UNREADABLE": (
        "No pudimos leer la API key guardada. Vuelve a cargarla en Mis cuentas."
    ),
    "WALLET_EXCHANGE_NOT_SUPPORTED": (
        "Ese exchange no se puede conectar como billetera. La plataforma solo opera con Binance: "
        "elige una cuenta de Binance."
    ),
    "WALLET_EXCHANGE_AUTH_FAILED": (
        "El exchange rechazó la API key. Revisa que sea correcta y que tenga permiso de lectura."
    ),
    "WALLET_EXCHANGE_UNAVAILABLE": (
        "No pudimos conectar con el exchange. Inténtalo de nuevo en unos minutos."
    ),
    "WALLET_SYNC_FAILED": (
        "El exchange no devolvió el saldo. Inténtalo de nuevo en unos minutos."
    ),
}
