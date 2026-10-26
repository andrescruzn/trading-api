# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/accounts/rest/wallet/error_messages.py
#
# Textos de UI de la billetera de la plataforma (super admin y socio).
# ======================================================================

WALLET_ERROR_MESSAGES: dict[str, str] = {
    "WALLET_NOT_CONFIGURED": (
        "La billetera de Binance aún no está conectada. Pide a quien administra el servidor que "
        "cargue la API key de Binance."
    ),
    "WALLET_ACCOUNT_NOT_FOUND": "No encontramos la billetera de Binance.",
    "WALLET_ACCOUNT_INACTIVE": (
        "La billetera de Binance está suspendida, así que no podemos leer su saldo."
    ),
    "WALLET_ACCOUNT_NO_EXCHANGE": (
        "No encontramos Binance en el catálogo de exchanges. Revisa los datos iniciales del sistema."
    ),
    "WALLET_CREDENTIALS_MISSING": (
        "Faltan la API key y el secret de Binance en el servidor. Sin ellos no podemos leer el saldo "
        "ni operar con dinero real."
    ),
    "WALLET_EXCHANGE_NOT_SUPPORTED": (
        "La billetera no está en Binance. La plataforma solo opera con Binance."
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
