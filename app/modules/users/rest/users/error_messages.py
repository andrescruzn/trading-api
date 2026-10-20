# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/rest/users/error_messages.py
#
# Textos de UI para la gestión de usuarios (solo admin).
# ======================================================================

USER_ERROR_MESSAGES: dict[str, str] = {
    "USER_NOT_FOUND":              "No encontramos ese usuario.",
    "USER_INVALID_ROLE":           "Ese rol no existe. Elige Usuario, Administrador o Inversor.",
    "USER_CANNOT_CHANGE_OWN_ROLE": "No puedes cambiar tu propio rol. Pídeselo a otro administrador.",
}
