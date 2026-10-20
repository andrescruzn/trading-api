# -*- coding: utf-8 -*-

BILLING_PERIOD_ERROR_MESSAGES: dict[str, str] = {
    "BILLING_PERIOD_NOT_FOUND":        "Período de facturación no encontrado.",
    "BILLING_PERIOD_ALREADY_OPEN":     "Ya existe un período abierto para esta cuenta. Ciérralo primero.",
    "BILLING_PERIOD_ALREADY_CLOSED":   "El período ya está cerrado.",
    "BILLING_MANAGED_ACCOUNT_NOT_FOUND": "Cuenta gestionada no encontrada.",
    "BILLING_MANAGED_ACCOUNT_INACTIVE":  "La cuenta gestionada no está activa.",
    "BILLING_MANAGED_ACCOUNT_FORBIDDEN": "No tienes acceso a esta cuenta gestionada.",
    "FEE_TX_NOT_FOUND":                "No encontramos esa comisión.",
    "FEE_TX_NOT_PENDING":              "Esta comisión ya se marcó como cobrada o condonada.",
    "FEE_TX_INVALID_ACTION":           "Acción no válida para la comisión.",
}
