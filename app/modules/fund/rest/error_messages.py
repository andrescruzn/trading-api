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

    # Salidas, comisiones y retiros (F5)
    "FUND_SETTLE_NO_FEE_SCHEDULE": (
        "Hay salidas en cola y aún no hay tabla de comisión. Configúrala en Administración → Fondo → Comisiones."
    ),
    "FUND_SETTLE_NO_COMMISSION_SHARES": (
        "Hay comisiones por cobrar y aún no hay reparto entre propietarios. Configúralo en Administración → Fondo → Comisiones."
    ),
    "FUND_FEE_INVALID_TIERS": (
        "Revisa los tramos: el primero empieza en 0 %, cada uno arranca en un retorno mayor que el anterior "
        "y cada comisión va de 0 % a 100 % (máximo 10 tramos)."
    ),
    "FUND_SHARES_INVALID": "Los porcentajes deben ser mayores que 0, sin repetir personas, y sumar exactamente 100 %.",
    "FUND_SHARES_NOT_OWNER": "Solo los super admin y los socios pueden recibir comisión.",
    "FUND_REDEMPTION_INVALID_AMOUNT": "Escribe un monto mayor que 0, o elige sacar todo.",
    "FUND_REDEMPTION_NO_UNITS": "No tienes dinero en ese agente.",
    "FUND_REDEMPTION_ALREADY_QUEUED": (
        "Ya tienes una salida en cola para ese agente. Anúlala si quieres cambiar el monto."
    ),
    "FUND_REDEMPTION_NOT_FOUND": "No encontramos esa salida.",
    "FUND_REDEMPTION_NOT_QUEUED": "Esa salida ya no está en cola: se aplicó o se anuló.",
    "FUND_PAYOUT_INVALID_KIND": "Los retiros solo se envían a una dirección cripto.",
    "FUND_PAYOUT_INVALID_DETAILS": "Escribe un nombre, la red y la dirección (máximo 120 caracteres cada uno).",
    "FUND_PAYOUT_INVALID_NETWORK": (
        "Esa red no está entre las que acepta el fondo. Elige una de la lista."
    ),
    "FUND_PAYOUT_INVALID_ADDRESS": (
        "Esa dirección no tiene el formato de la red elegida. Cópiala de nuevo desde tu billetera "
        "y revisa que sea de la misma red."
    ),
    "FUND_PAYOUT_TOO_MANY": "Ya tienes 5 direcciones activas. Desactiva una antes de agregar otra.",
    "FUND_PAYOUT_NOT_FOUND": "No encontramos esa dirección.",
    "FUND_PAYOUT_UNREADABLE": "No pudimos leer esa dirección. Pídele a la persona que la registre de nuevo.",
    "FUND_PAYOUT_COOLING_DOWN": (
        "Por seguridad, una dirección nueva se puede usar 48 horas después de registrarla."
    ),
    "FUND_WITHDRAWAL_INVALID_AMOUNT": "Escribe un monto mayor que 0.",
    "FUND_WITHDRAWAL_EXCEEDS_AVAILABLE": (
        "No tienes ese saldo disponible. Solo se retira lo que ya pasó por un agente, "
        "descontando otros retiros pedidos y lo que está en cola para reinvertir."
    ),
    "FUND_WITHDRAWAL_TOO_MANY_OPEN": "Tienes 5 retiros sin pagar. Espera a que se paguen antes de pedir otro.",
    "FUND_WITHDRAWAL_NOT_FOUND": "No encontramos ese retiro.",
    "FUND_WITHDRAWAL_NOT_OPEN": "Ese retiro ya se pagó, se rechazó o se anuló. Recarga la página.",
    "FUND_WITHDRAWAL_BELOW_NETWORK_MIN": (
        "El monto es menor que el mínimo de retiro de esa red, o no alcanza a cubrir su comisión. "
        "Pide un monto mayor."
    ),
    "FUND_WITHDRAWAL_INVALID_TXID": (
        "Ese no parece un ID de transacción. Cópialo completo desde el historial de retiros de Binance."
    ),
    "FUND_WITHDRAWAL_TXID_TAKEN": "Ese ID de transacción ya está registrado en otro retiro.",
    "FUND_WITHDRAWAL_TX_PENDING": (
        "Binance todavía está procesando ese envío. Regístralo cuando aparezca como completado."
    ),
    "FUND_WITHDRAWAL_TX_FAILED": (
        "Binance reporta ese envío como fallido o cancelado: el dinero no salió. "
        "Revisa el historial de retiros de Binance."
    ),
    "FUND_WITHDRAWAL_ADDRESS_MISMATCH": (
        "Ese envío no fue a la dirección de la persona (red, dirección o memo distintos). "
        "No se puede registrar en este retiro."
    ),
    "FUND_WITHDRAWAL_TX_NOT_FOUND": (
        "No encontramos ese envío en Binance. Revisa el ID o, si estás seguro, escribe el monto "
        "enviado, la comisión y una nota que lo explique."
    ),
    "FUND_WITHDRAWAL_INVALID_PAYMENT": "Escribe el monto que recibió la persona y la comisión de red.",
    "FUND_WITHDRAWAL_PAYMENT_NOTE_REQUIRED": (
        "Lo que salió (enviado + comisión) no coincide con lo pedido, o Binance no muestra la "
        "dirección. Escribe una nota que lo explique."
    ),
    "FUND_WITHDRAWAL_NOTE_REQUIRED": "Escribe el motivo: la persona lo ve en su historial.",
    "FUND_WITHDRAWAL_INVALID_STATUS": "Ese estado no existe.",
    "FUND_RECEIPT_INVALID": "El comprobante debe ser un PDF, PNG o JPG.",
    "FUND_RECEIPT_TOO_LARGE": "El comprobante pesa más de 5 MB. Sube uno más liviano.",
    "FUND_RECEIPT_NOT_PAID": "Solo se adjunta el comprobante a un retiro pagado.",
    "FUND_RECEIPT_NOT_FOUND": "Ese retiro no tiene comprobante.",

    "FUND_REFUND_EXCEEDS_PENDING": (
        "Solo se puede devolver saldo pendiente de asignar, y esta persona tiene menos que ese monto."
    ),
}
