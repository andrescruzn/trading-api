# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/alerts/channels/fund_messages.py
#
# Textos de los avisos del fondo común (campana, correo y Telegram). El
# fondo manda un código y datos (FundEvent); aquí se arma lo que lee la
# persona. Tono de notificación: qué pasó, con cifras, y qué sigue.
# ======================================================================

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from app.modules.alerts.channels.telegram_messages import format_number
from app.modules.fund.domain.fund_notifier import (
    FUND_ALLOCATION_APPLIED,
    FUND_DEPOSIT_CONFIRMED,
    FUND_DEPOSIT_IN_REVIEW,
    FUND_DEPOSIT_REJECTED,
    FUND_REDEMPTION_APPLIED,
    FUND_WITHDRAWAL_PAID,
    FUND_WITHDRAWAL_REJECTED,
    FUND_WITHDRAWAL_REQUESTED,
)

_REVIEW_REASONS = {
    "amount_mismatch": "el monto que llegó no coincide con el declarado",
    "over_threshold": "supera el tope de confirmación automática",
    "exchange_failed": "el exchange lo marcó como fallido o cancelado",
    "wrong_asset": "llegó en otra moneda",
}


@dataclass(frozen=True)
class FundNotice:
    title: str
    message: str
    severity: str = "info"
    # Ruta del front (hash routing) a la que lleva el aviso
    link: str = "/my-fund"


def _num(value: str | None, decimals: int = 2) -> str:
    try:
        return format_number(Decimal(value or "0"), decimals)
    except (InvalidOperation, ValueError):
        return value or "—"


def fund_notice(code: str, data: dict[str, str]) -> FundNotice | None:
    """Texto del aviso; None si el código no se conoce (no se avisa)."""
    asset = data.get("asset", "USDT")
    amount = f"{_num(data.get('amount'))} {asset}"
    agent = data.get("agent", "el agente")
    person = data.get("person", "Una persona")

    if code == FUND_DEPOSIT_CONFIRMED:
        return FundNotice(
            title="Depósito confirmado",
            message=(
                f"Recibimos {amount}. Ya están en tu saldo pendiente de asignar y "
                "entran a un agente en su próxima liquidación."
            ),
        )
    if code == FUND_DEPOSIT_REJECTED:
        return FundNotice(
            title="Depósito rechazado",
            message=f"Tu depósito de {amount} no se acreditó. Motivo: {data.get('note', '—')}",
            severity="warning",
        )
    if code == FUND_DEPOSIT_IN_REVIEW:
        reason = _REVIEW_REASONS.get(data.get("reason", ""), "necesita revisión")
        return FundNotice(
            title="Depósito por revisar",
            message=f"{person} registró un depósito de {amount}: {reason}. Confírmalo o recházalo.",
            severity="warning",
            link="/admin/deposits",
        )
    if code == FUND_ALLOCATION_APPLIED:
        return FundNotice(
            title="Tu dinero entró a un agente",
            message=(
                f"{amount} entraron a «{agent}»: recibiste {_num(data.get('units'), 4)} "
                f"unidades a {_num(data.get('nav'), 6)} cada una."
            ),
        )
    if code == FUND_REDEMPTION_APPLIED:
        message = (
            f"Salieron {_num(data.get('value'))} {asset} de «{agent}». "
            f"Comisión: {_num(data.get('fee'))} {asset}. Recibiste {_num(data.get('net'))} {asset} "
            "en tu saldo disponible; ya puedes retirarlos."
        )
        pending = data.get("pending")
        if pending and Decimal(pending) > 0:
            message += (
                f" {_num(pending)} {asset} aún no cumplen la permanencia mínima y siguen en el agente."
            )
        return FundNotice(title="Salida aplicada", message=message)
    if code == FUND_WITHDRAWAL_REQUESTED:
        return FundNotice(
            title="Retiro por enviar",
            message=(
                f"{person} pidió retirar {amount}. Envíalo desde Binance a su dirección "
                f"y registra el ID de la transacción en Retiros."
            ),
            link="/admin/withdrawals",
        )
    if code == FUND_WITHDRAWAL_PAID:
        # Detalles del envío entre billeteras; el explorador solo si la red tiene uno público
        explorer = data.get("explorer_url")
        message = (
            f"Te enviamos {_num(data.get('sent'))} {asset} por la red {data.get('network', '—')} "
            f"a tu dirección {data.get('address', '—')}. "
            f"Comisión de red: {_num(data.get('fee'))} {asset} (se descontó de tu retiro de {amount}). "
            f"ID de la transacción: {data.get('txid', '—')}."
        )
        if explorer:
            message += f" Consúltala en {explorer}"
        return FundNotice(title="Retiro enviado", message=message)
    if code == FUND_WITHDRAWAL_REJECTED:
        return FundNotice(
            title="Retiro rechazado",
            message=(
                f"Tu retiro de {amount} no se pagó y el dinero vuelve a tu saldo disponible. "
                f"Motivo: {data.get('note', '—')}"
            ),
            severity="warning",
        )
    return None
