# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/rest/error_messages.py
#
# Textos de UI del fondo común (ajustes, depósitos y libro mayor). Incluye
# los de la billetera (M4): los servicios del fondo pueden devolver los
# códigos WALLET_* del gateway del exchange.
# ======================================================================

from app.modules.accounts.rest.wallet.error_messages import WALLET_ERROR_MESSAGES

FUND_ERROR_MESSAGES: dict[str, str] = {
    **WALLET_ERROR_MESSAGES,
    "WALLET_NO_DEPOSIT_ADDRESS": (
        "El exchange no devolvió una dirección de depósito para esa red. Revisa que la red "
        "acepte depósitos y que la API key pueda leer direcciones."
    ),

    # Billetera
    "FUND_WALLET_NOT_CONFIGURED": (
        "Aún no hay billetera de la plataforma. Un super admin debe elegirla en Administración → Fondo → Billetera."
    ),
    "FUND_WALLET_UNAVAILABLE": (
        "La billetera de la plataforma no está disponible (cuenta suspendida o borrada). Avísale a un super admin."
    ),
    "FUND_WALLET_NOT_LIVE": "Esto solo se puede con una billetera live: en práctica no hay depósitos reales.",

    # Ajustes
    "FUND_INVALID_MIN_HOLD_DAYS": "La permanencia mínima debe estar entre 0 y 365 días.",
    "FUND_INVALID_AUTO_CONFIRM_MAX": "El tope de confirmación automática no puede ser negativo.",
    "FUND_INVALID_REQUEST_TTL": "El vencimiento de las solicitudes debe estar entre 1 y 720 horas.",
    "FUND_INVALID_NETWORKS": (
        "Revisa las redes: elige hasta 10, sin repetir, que acepten depósitos en el exchange. "
        "Con billetera de práctica, cada red necesita su dirección."
    ),

    # Depósitos
    "FUND_DEPOSIT_INVALID_NETWORK": "Esa red no está habilitada para depositar. Elige una de la lista.",
    "FUND_DEPOSIT_INVALID_TXID": (
        "El hash de la transacción no es válido. Cópialo completo desde tu billetera o el explorador de la red."
    ),
    "FUND_DEPOSIT_INVALID_AMOUNT": "Escribe un monto mayor que 0.",
    "FUND_DEPOSIT_TXID_TAKEN": (
        "Ese hash de transacción ya está registrado. Si no lo registraste tú, escríbele a un super admin."
    ),
    "FUND_DEPOSIT_TOO_MANY_OPEN": (
        "Tienes 10 depósitos sin resolver. Espera a que se confirmen antes de registrar otro."
    ),
    "FUND_DEPOSIT_NOT_FOUND": "No encontramos ese depósito.",
    "FUND_DEPOSIT_NOT_CANCELABLE": "Este depósito ya no se puede anular: está en revisión o ya se resolvió.",
    "FUND_DEPOSIT_ALREADY_RESOLVED": "Este depósito ya se resolvió. Recarga la página para ver su estado.",
    "FUND_DEPOSIT_NOTE_REQUIRED": "Escribe una nota que explique la decisión.",
    "FUND_DEPOSIT_INVALID_STATUS": "Ese estado no existe.",
    "FUND_UNCLAIMED_NOT_FOUND": (
        "Ese depósito ya no está sin reclamar: alguien lo registró o no aparece en el exchange."
    ),
    "FUND_USER_NOT_FOUND": "No encontramos esa persona.",

    # Libro mayor
    "FUND_REFUND_REASON_REQUIRED": "Escribe el motivo de la devolución (entre 5 y 500 caracteres).",
    "FUND_REFUND_INVALID_AMOUNT": "Escribe un monto mayor que 0.",
    # Agentes del fondo (F4)
    "FUND_BOT_NOT_FOUND": "No encontramos ese agente.",
    "FUND_BOT_NOT_ON_WALLET": (
        "Ese agente no opera sobre la billetera de la plataforma. Solo esos agentes pueden recibir dinero del fondo."
    ),
    "FUND_BOT_WRONG_QUOTE": (
        "El mercado del agente no cotiza en la moneda del fondo (USDT). Elige un agente con un par en USDT."
    ),
    "FUND_POOL_EXISTS": "Ese agente ya está abierto al fondo.",
    "FUND_POOL_NOT_FOUND": "No encontramos ese agente del fondo.",
    "FUND_ALLOCATION_INVALID_SOURCE": "Elige de qué saldo sale el dinero: pendiente de asignar o disponible.",
    "FUND_ALLOCATION_INVALID_AMOUNT": "Escribe un monto mayor que 0.",
    "FUND_ALLOCATION_EXCEEDS_BALANCE": (
        "La persona no tiene ese saldo libre (ya descontado lo que tiene en cola)."
    ),
    "FUND_ALLOCATION_NOT_FOUND": "No encontramos esa asignación.",
    "FUND_ALLOCATION_NOT_QUEUED": "Esa asignación ya no está en cola.",
    "FUND_SETTLE_BOT_RUNNING": "Pausa o detén el agente antes de liquidarlo.",
    "FUND_SETTLE_OPEN_POSITIONS": (
        "El agente tiene posiciones abiertas. Espera a que se cierren (o ciérralas) antes de liquidar."
    ),
    "FUND_SETTLE_OPEN_ORDERS": (
        "El agente tiene órdenes sin terminar en el exchange. Espera a que se ejecuten o cancélalas antes de liquidar."
    ),
    "FUND_SETTLE_ORPHAN_EQUITY": (
        "El agente ganó o perdió dinero sin tener participantes. Revisa sus órdenes: así no se puede repartir."
    ),
    "FUND_SETTLE_NEGATIVE_EQUITY": (
        "El resultado deja al agente con saldo negativo. Revisa sus órdenes antes de liquidar."
    ),
    "FUND_SETTLE_CONFLICT": (
        "Alguien liquidó o cambió este agente al mismo tiempo. Recarga y vuelve a intentarlo."
    ),

    "FUND_REFUND_EXCEEDS_PENDING": (
        "Solo se puede devolver saldo pendiente de asignar, y esta persona tiene menos que ese monto."
    ),
}
