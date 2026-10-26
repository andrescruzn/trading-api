# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/fund/domain/withdrawal_entity.py
#
# Retiros del fondo común (F5):
#
# - PayoutMethod      → a dónde se le envía el dinero a una persona: una
#                       dirección cripto (red + dirección + memo). Sin bancos
#                       (decisión legal, 2026-10-26): solo movimientos entre
#                       billeteras. Los datos van cifrados; en pantalla solo
#                       un resumen enmascarado. Un medio nuevo espera un
#                       tiempo antes de usarse (si alguien toma la cuenta, no
#                       puede desviar un retiro al instante).
# - WithdrawalRequest → "envíame X USDT de mi saldo disponible". Un super
#                       admin lo envía desde Binance y registra el txid; la
#                       comisión de red la paga la persona (recibe X − fee).
# - WithdrawalReceipt → el comprobante del pago (PDF / PNG / JPG, F6). Se
#                       guarda en la BD: entra en los respaldos y sirve con
#                       varios servidores. El tipo se valida por el contenido,
#                       no por el nombre del archivo.
# ======================================================================

from __future__ import annotations

import base64
import binascii
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

# `bank` y `nequi` solo quedan en filas viejas (desactivadas): ya no se crean
PAYOUT_KINDS = ("crypto",)
WITHDRAWAL_STATUSES = ("requested", "paid", "rejected", "canceled")

# Campos de los datos de cada tipo (los que el formulario pide)
PAYOUT_FIELDS: dict[str, tuple[str, ...]] = {
    "crypto": ("network", "address", "memo"),
}
# Los que pueden ir vacíos (el memo solo lo usan algunas redes)
PAYOUT_OPTIONAL_FIELDS = frozenset({"memo"})

# Diferencia aceptada entre lo pedido y lo que salió (enviado + comisión)
# sin exigir nota: redondeos de la comisión de red.
PAYMENT_TOLERANCE_RATIO = Decimal("0.01")

# Redes EVM (misma forma de dirección: 0x + 40 hex). Binance usa a veces el
# código de la red (BSC) y a veces el del estándar (BEP20): se aceptan ambos.
_EVM_NETWORKS = frozenset({
    "ETH", "ERC20", "BSC", "BEP20", "ARBITRUM", "ARB", "MATIC", "POLYGON",
    "OPTIMISM", "OP", "AVAXC", "BASE", "OPBNB",
})
_TRON_NETWORKS = frozenset({"TRX", "TRC20"})
_SOLANA_NETWORKS = frozenset({"SOL", "SPL"})

_EVM_ADDRESS = re.compile(r"^0x[0-9a-fA-F]{40}$")
_TRON_ADDRESS = re.compile(r"^T[1-9A-HJ-NP-Za-km-z]{33}$")
_SOLANA_ADDRESS = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")
_GENERIC_ADDRESS = re.compile(r"^[A-Za-z0-9:_\-]{20,128}$")

# Explorador público de cada red: `{txid}` se reemplaza por el hash
_EXPLORERS: dict[str, str] = {
    "TRX": "https://tronscan.org/#/transaction/{txid}",
    "TRC20": "https://tronscan.org/#/transaction/{txid}",
    "BSC": "https://bscscan.com/tx/{txid}",
    "BEP20": "https://bscscan.com/tx/{txid}",
    "ETH": "https://etherscan.io/tx/{txid}",
    "ERC20": "https://etherscan.io/tx/{txid}",
    "ARBITRUM": "https://arbiscan.io/tx/{txid}",
    "ARB": "https://arbiscan.io/tx/{txid}",
    "MATIC": "https://polygonscan.com/tx/{txid}",
    "POLYGON": "https://polygonscan.com/tx/{txid}",
    "OPTIMISM": "https://optimistic.etherscan.io/tx/{txid}",
    "OP": "https://optimistic.etherscan.io/tx/{txid}",
    "SOL": "https://solscan.io/tx/{txid}",
}


def normalize_network(network: str | None) -> str:
    return (network or "").strip().upper()


def is_valid_address(network: str, address: str) -> bool:
    """Forma de la dirección según la red (no garantiza que exista)."""
    code = normalize_network(network)
    value = (address or "").strip()
    if code in _EVM_NETWORKS:
        return bool(_EVM_ADDRESS.match(value))
    if code in _TRON_NETWORKS:
        return bool(_TRON_ADDRESS.match(value))
    if code in _SOLANA_NETWORKS:
        return bool(_SOLANA_ADDRESS.match(value))
    return bool(_GENERIC_ADDRESS.match(value))


def same_address(network: str, a: str | None, b: str | None) -> bool:
    """En redes EVM la dirección no distingue mayúsculas; en las demás sí."""
    left, right = (a or "").strip(), (b or "").strip()
    if normalize_network(network) in _EVM_NETWORKS:
        return left.lower() == right.lower()
    return left == right


def short_address(address: str | None) -> str:
    """`TQ7xAbC…9aBc`: lo justo para reconocerla sin mostrarla entera."""
    value = (address or "").strip()
    return value if len(value) <= 14 else f"{value[:6]}…{value[-4:]}"


def explorer_url(network: str | None, txid: str | None) -> str | None:
    """Enlace al explorador de la red; None si no se conoce o es interno de Binance."""
    template = _EXPLORERS.get(normalize_network(network))
    # Un envío entre cuentas de Binance trae un id numérico, no un hash público
    if not template or not txid or txid.isdigit():
        return None
    return template.format(txid=txid)


def mask_payout(kind: str, details: dict[str, str]) -> str:
    """`TRX · TQ7xAb…9aBc` (sin la dirección completa)."""
    network = normalize_network(details.get("network"))
    return f"{network} · {short_address(details.get('address'))}"


@dataclass
class PayoutMethod:
    id: int
    user_id: int
    kind: str
    label: str
    masked: str
    usable_from: datetime
    is_active: bool = True
    # Solo en memoria (descifrados) cuando un super admin va a pagar
    details: dict[str, str] = field(default_factory=dict)
    created_at: datetime | None = None

    def is_usable(self, now: datetime) -> bool:
        return self.is_active and self.usable_from <= now

    def belongs_to(self, user_id: int) -> bool:
        return self.user_id == int(user_id)


@dataclass
class WithdrawalRequest:
    id: int
    user_id: int
    amount: Decimal
    payout_method_id: int
    status: str = "requested"
    # Lo que registró el super admin al enviarlo (o lo que reportó Binance)
    txid: str | None = None
    network: str | None = None
    sent_amount: Decimal | None = None
    network_fee: Decimal | None = None
    exchange_withdrawal_id: str | None = None
    resolution_note: str | None = None
    resolved_by_user_id: int | None = None
    resolved_at: datetime | None = None
    created_at: datetime | None = None
    # Nombre del comprobante, si tiene (lo llena el servicio)
    receipt_name: str | None = None

    def belongs_to(self, user_id: int) -> bool:
        return self.user_id == int(user_id)


# ----------------------------------------------------------------------
# Comprobante del pago (F6)
# ----------------------------------------------------------------------

MAX_RECEIPT_BYTES = 5 * 1024 * 1024
MAX_RECEIPT_NAME = 200

# Firma de los primeros bytes de cada tipo permitido
_RECEIPT_SIGNATURES: tuple[tuple[str, bytes], ...] = (
    ("application/pdf", b"%PDF-"),
    ("image/png", b"\x89PNG\r\n\x1a\n"),
    ("image/jpeg", b"\xff\xd8\xff"),
)
RECEIPT_CONTENT_TYPES = tuple(kind for kind, _ in _RECEIPT_SIGNATURES)


def decode_receipt(data_base64: str) -> bytes | None:
    """Base64 → bytes; None si no es base64 válido."""
    try:
        return base64.b64decode((data_base64 or "").strip(), validate=True)
    except (binascii.Error, ValueError):
        return None


def detect_receipt_type(content: bytes) -> str | None:
    """Tipo real del archivo por su firma; None si no es PDF, PNG ni JPG."""
    for kind, signature in _RECEIPT_SIGNATURES:
        if content.startswith(signature):
            return kind
    return None


def clean_receipt_name(filename: str | None) -> str:
    """Solo el nombre (sin rutas) y con límite de largo."""
    name = os.path.basename((filename or "").replace("\\", "/")).strip()
    return name[:MAX_RECEIPT_NAME] or "comprobante"


@dataclass
class WithdrawalReceipt:
    withdrawal_id: int
    filename: str
    content_type: str
    content: bytes
    uploaded_by_user_id: int | None = None
    created_at: datetime | None = None

    @property
    def size_bytes(self) -> int:
        return len(self.content)
