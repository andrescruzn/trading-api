# -*- coding: utf-8 -*-

CANDLE_ERROR_MESSAGES: dict[str, str] = {
    "SYMBOL_NOT_FOUND": "Símbolo no encontrado.",
    "TIMEFRAME_NOT_FOUND": "Timeframe no encontrado.",
    "EXCHANGE_NOT_FOUND": "Exchange no encontrado.",
    "EXCHANGE_NOT_SUPPORTED_CCXT": "Este exchange no está soportado para descarga automática.",
    "CCXT_SYMBOL_NOT_FOUND": "El símbolo no existe en el exchange.",
    "CCXT_NETWORK_ERROR": "Error de red al conectar con el exchange. Intenta de nuevo.",
    "CCXT_FETCH_ERROR": "Error al descargar velas del exchange.",
    "CANDLES_EMPTY_PAYLOAD": "El payload no contiene velas.",
    "CANDLES_INVALID_ROW": "Una o más filas tienen datos inválidos o faltantes.",
    "CANDLES_INVALID_OHLCV": "Una fila tiene valores OHLCV inválidos (high < low o precios negativos).",
}
