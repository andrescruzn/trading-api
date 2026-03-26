# -*- coding: utf-8 -*-

# ======================================================================
# Mensajes UI para errores del recurso Investor.
# El servicio solo retorna códigos estables; aquí se mapean a texto UI.
# ======================================================================

INVESTOR_ERROR_MESSAGES: dict[str, str] = {
    "BILLING_INVESTOR_NOT_FOUND":       "Inversor no encontrado.",
    "BILLING_INVESTOR_ALREADY_EXISTS":  "Ya existe un perfil de inversor para este usuario.",
    "BILLING_INVESTOR_INACTIVE":        "El inversor no está activo.",
    "BILLING_INVALID_FEE_PCT":          "El porcentaje de fee debe estar entre 0 y 100.",
}
