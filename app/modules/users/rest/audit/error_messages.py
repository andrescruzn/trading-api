# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/rest/audit/error_messages.py
#
# Textos de UI de la página Auditoría (solo admin).
# ======================================================================

AUDIT_ERROR_MESSAGES: dict[str, str] = {
    "AUDIT_INVALID_EVENT_TYPE": "Ese tipo de evento no existe. Elige uno de la lista.",
    "AUDIT_INVALID_KIND":       "Ese tipo de acción no existe. Elige Consultas o Cambios.",
    "AUDIT_INVALID_DATE_RANGE": "La fecha final debe ser posterior a la inicial.",
    "AUDIT_INVALID_PATH":       "El texto a buscar en la ruta es demasiado largo (máximo 200 caracteres).",
}
