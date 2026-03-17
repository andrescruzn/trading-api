# -*- coding: utf-8 -*-

MODEL_ERROR_MESSAGES: dict[str, str] = {
    "MODEL_NOT_FOUND":              "Modelo no encontrado.",
    "MODEL_INVALID_TYPE":           "Tipo de modelo inválido. Valores válidos: xgboost, lightgbm, sklearn, nn.",
    "MODEL_INVALID_STATUS":         "Estado inválido. Valores válidos: active, deprecated, archived.",
    "MODEL_DUPLICATE_NAME_VERSION": "Ya existe un modelo con ese nombre y versión.",
}
