# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/users/rest/users/error_messages.py
#
# Textos de UI para la gestión de usuarios (solo super admin).
# ======================================================================

USER_ERROR_MESSAGES: dict[str, str] = {
    "USER_NOT_FOUND":              "No encontramos ese usuario.",
    "USER_INVALID_ROLE":           "Ese rol no existe. Elige Socio o Inversor.",
    "USER_CANNOT_CHANGE_OWN_ROLE": "No puedes cambiar tu propio rol.",
    "USER_SUPER_ADMIN_PROTECTED": (
        "No puedes cambiar el rol ni el estado de un super admin desde la app."
    ),
    "USER_INVALID_EMAIL":          "Escribe un correo válido, por ejemplo nombre@empresa.com.",
    "USER_INVALID_NAME":           "El nombre es demasiado largo.",
    "USER_EMAIL_TAKEN":            "Ya existe una cuenta con ese correo.",
    "USER_INVALID_STATUS":         "Ese estado no existe. Elige Activo, Bloqueado o Desactivado.",
    "USER_CANNOT_CHANGE_OWN_STATUS": (
        "No puedes cambiar el estado de tu propia cuenta."
    ),
}
