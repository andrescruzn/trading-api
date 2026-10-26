# -*- coding: utf-8 -*-

SYMBOL_ERROR_MESSAGES: dict[str, str] = {
    "SYMBOL_NOT_FOUND": "Símbolo no encontrado.",
    "SYMBOL_ALREADY_EXISTS": "Ese símbolo ya existe.",
    "SYMBOL_INVALID_ASSET_CLASS": "Clase de activo inválida. Opciones: cripto, metal, materia prima, índice, ETF, acción o forex.",
    "PLATFORM_EXCHANGE_MISSING": (
        "Falta Binance en el catálogo de exchanges. "
        "Carga los datos iniciales de mercado y vuelve a intentarlo."
    ),
}
