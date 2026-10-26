# -*- coding: utf-8 -*-

ACCOUNT_ERROR_MESSAGES: dict[str, str] = {
    "ACCOUNT_NOT_FOUND":      "Cuenta no encontrada.",
    "ACCOUNT_FORBIDDEN":      "No tienes permiso para acceder a esta cuenta.",
    "ACCOUNT_INVALID_MODE":   "El modo no es válido. Elige Paper o Live.",
    "ACCOUNT_INVALID_STATUS": "El estado no es válido. Elige Activa o Suspendida.",
    "PLATFORM_EXCHANGE_MISSING": (
        "Falta Binance en el catálogo de exchanges. "
        "Carga los datos iniciales de mercado y vuelve a intentarlo."
    ),
}
