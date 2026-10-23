# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/execution/live_executor.py
#
# Ejecutor de órdenes en modo live (exchange real via ccxt).
#
# Flujo de ejecución:
# 1. Obtener la cuenta del bot (para exchange y credenciales)
# 2. Descifrar credenciales API (Fernet, de account.meta['enc_creds'])
# 3. Inicializar cliente ccxt con api_key + api_secret
# 4. Enviar la orden al exchange
# 5. Traducir la respuesta al estado real (filled / partially_filled / sent)
#
# Además de `execute`, expone lo que necesitan la reconciliación y la
# protección nativa (mismo cliente, mismas credenciales):
# - fetch(order, bot)            → estado actual de la orden en el exchange
# - cancel(order, bot)           → cancelar una orden abierta
# - place_stop_loss(order, bot)  → stop loss nativo (si el exchange lo soporta)
#
# Exchanges soportados: los de CCXT_EXCHANGE_MAP (M2, ccxt_exchanges.py).
# Solo spot: los perpetuos (`XAU/USDT:USDT`) se rechazan, porque ccxt
# interpreta `amount` como contratos y no hay apalancamiento ni cortos.
#
# LIVE_USE_SANDBOX=true usa la testnet del exchange (set_sandbox_mode):
# permite probar todo el circuito live sin dinero real.
# ======================================================================

from __future__ import annotations

from decimal import Decimal
from typing import Any

import ccxt

from app.common.security.credentials_cipher import CredentialsCipher
from app.common.utils.datetime_utils import utc_now
from app.modules.accounts.domain.account_repository import AccountRepository
from app.modules.accounts.infrastructure.exchange_client import build_authenticated_client
from app.modules.bots.domain.bot_entity import Bot
from app.modules.market.domain.ccxt_exchanges import is_perpetual
from app.modules.market.domain.exchange_repository import ExchangeRepository
from app.modules.orders.domain.fill_entity import Fill
from app.modules.orders.domain.order_entity import Order
from app.modules.orders.execution.executor_interface import (
    ExecutionResult,
    ExecutionUncertainError,
    ExecutorInterface,
)


# Mapeo tipo de orden del dominio → tipo ccxt
_ORDER_TYPE_MAP: dict[str, str] = {
    "market":     "market",
    "limit":      "limit",
    "stop":       "stop",
    "stop_limit": "stop_limit",
}

# Estados de una orden ccxt (`status`) → estado de dominio cuando NO hay
# ejecución nueva que registrar
_CCXT_FINAL_STATUS: dict[str, str] = {
    "canceled": "canceled",
    "cancelled": "canceled",
    "rejected": "rejected",
    "expired": "rejected",
}


class LiveExecutor(ExecutorInterface):
    """
    Ejecuta órdenes en un exchange real usando ccxt.

    Pasos internos:
    1. Recupera la cuenta del bot para obtener exchange y credenciales.
    2. Descifra las credenciales API (Fernet).
    3. Crea el cliente ccxt con las credenciales.
    4. Envía la orden al exchange.
    5. Traduce la respuesta al estado real (filled / partially_filled / sent).

    Raises RuntimeError si:
    - La cuenta no existe o no tiene credenciales configuradas.
    - El exchange del símbolo no está soportado por ccxt.
    - La orden es rechazada por el exchange.
    """

    def __init__(
        self,
        account_repo: AccountRepository,
        exchange_repo: ExchangeRepository,
        cipher: CredentialsCipher,
    ):
        self._account_repo = account_repo
        self._exchange_repo = exchange_repo
        self._cipher = cipher

    # ==================================================================
    # Enviar una orden
    # ==================================================================

    def execute(self, order: Order, bot: Bot) -> ExecutionResult:
        """
        Envía la orden al exchange real y retorna su resultado, con el Fill
        (precio, cantidad y comisión reales) si se ejecutó algo.

        Raises:
            ExecutionUncertainError: timeout o error de red tras enviarla.
            RuntimeError: ante cualquier error de configuración,
                          credenciales o rechazo del exchange.
        """
        client = self._build_client(bot)
        symbol_str = self._order_symbol(order)

        # ccxt espera: symbol (str), type (str), side (str), amount (float), price (float|None)
        ccxt_type = _ORDER_TYPE_MAP.get(order.type, order.type)
        ccxt_price = float(order.price) if order.price is not None else None

        params: dict = {}
        if order.stop_price is not None:
            params["stopPrice"] = float(order.stop_price)
        if order.time_in_force is not None:
            params["timeInForce"] = order.time_in_force
        # Idempotencia: el exchange rechaza un segundo clientOrderId igual y
        # permite buscar la orden si la respuesta se pierde por red.
        if order.client_order_id:
            params["clientOrderId"] = order.client_order_id

        response = self._send(
            lambda: client.create_order(
                symbol=symbol_str,
                type=ccxt_type,
                side=order.side,
                amount=float(order.qty),
                price=ccxt_price,
                params=params,
            )
        )
        return self._to_result(order, response)

    def place_stop_loss(self, order: Order, bot: Bot) -> ExecutionResult:
        """
        Stop loss nativo: orden de venta a mercado que el exchange dispara al
        tocar `order.stop_price`. Protege aunque la API esté caída.

        Raises:
            RuntimeError: el exchange no soporta stop loss por la API unificada
                          de ccxt o lo rechazó (el llamador deja la protección
                          del scheduler como respaldo).
            ExecutionUncertainError: sin respuesta tras enviarla.
        """
        if order.stop_price is None:
            raise RuntimeError("El stop loss nativo necesita stop_price.")

        client = self._build_client(bot)
        if not client.has.get("createStopLossOrder"):
            raise RuntimeError(f"{client.id} no soporta stop loss nativo por la API de ccxt.")

        symbol_str = self._order_symbol(order)
        params: dict = {}
        if order.client_order_id:
            params["clientOrderId"] = order.client_order_id

        response = self._send(
            lambda: client.create_stop_loss_order(
                symbol_str,
                "market",
                order.side,
                float(order.qty),
                None,
                float(order.stop_price),
                params,
            )
        )
        return self._to_result(order, response)

    # ==================================================================
    # Consultar y cancelar (reconciliación / protección)
    # ==================================================================

    def fetch(self, order: Order, bot: Bot) -> dict[str, Any] | None:
        """
        Estado actual de la orden en el exchange, o None si el exchange no
        la conoce (nunca llegó).

        Busca por exchange_order_id; sin él (timeout al enviarla), por
        clientOrderId, y si el exchange no acepta ese filtro, entre las
        órdenes abiertas y cerradas recientes.

        Raises:
            ExecutionUncertainError: error de red (se reintenta en el siguiente ciclo).
            RuntimeError: configuración o error del exchange.
        """
        client = self._build_client(bot)
        symbol_str = self._order_symbol(order)

        try:
            if order.exchange_order_id:
                return client.fetch_order(order.exchange_order_id, symbol_str)
            if not order.client_order_id:
                return None
            try:
                return client.fetch_order(
                    None, symbol_str, {"clientOrderId": order.client_order_id}
                )
            except (ccxt.ArgumentsRequired, ccxt.NotSupported, ccxt.BadRequest):
                return self._find_by_client_id(client, symbol_str, order.client_order_id)
        except ccxt.OrderNotFound:
            return None
        except (ccxt.RequestTimeout, ccxt.NetworkError) as e:
            raise ExecutionUncertainError(f"Sin respuesta del exchange: {e}")
        except ccxt.ExchangeError as e:
            raise RuntimeError(f"Error del exchange al consultar la orden: {e}")

    def cancel(self, order: Order, bot: Bot) -> bool:
        """
        Cancela una orden abierta. True si quedó cancelada; False si el
        exchange ya no la tiene abierta (ejecutada o cancelada antes).

        Raises:
            ExecutionUncertainError: error de red.
            RuntimeError: configuración o error del exchange.
        """
        if not order.exchange_order_id:
            return False
        client = self._build_client(bot)
        try:
            client.cancel_order(order.exchange_order_id, self._order_symbol(order))
            return True
        except ccxt.OrderNotFound:
            return False
        except (ccxt.RequestTimeout, ccxt.NetworkError) as e:
            raise ExecutionUncertainError(f"Sin respuesta del exchange: {e}")
        except ccxt.ExchangeError as e:
            raise RuntimeError(f"Error del exchange al cancelar la orden: {e}")

    # ==================================================================
    # Lógica interna
    # ==================================================================

    def _build_client(self, bot: Bot):
        """Cliente ccxt autenticado con las credenciales de la cuenta del bot."""
        # 1. Obtener cuenta del bot
        if bot.account_id is None:
            raise RuntimeError(
                "El bot no tiene cuenta asociada. "
                "Configura una cuenta live antes de operar."
            )

        account = self._account_repo.get_by_id(bot.account_id)
        if account is None:
            raise RuntimeError(
                f"Cuenta no encontrada: account_id={bot.account_id}."
            )

        # 2. Credenciales descifradas + cliente ccxt (helper compartido con la
        #    billetera de la plataforma; respeta LIVE_USE_SANDBOX)
        return build_authenticated_client(account, self._exchange_repo, self._cipher)

    @staticmethod
    def _order_symbol(order: Order) -> str:
        """Símbolo unificado guardado en meta por CreateOrderService (solo spot)."""
        symbol_str = order.meta.get("symbol")
        if not symbol_str:
            raise RuntimeError(
                "La orden no tiene el símbolo en meta. "
                "Asegúrate de que CreateOrderService lo incluya."
            )
        if is_perpetual(symbol_str):
            raise RuntimeError(
                f"'{symbol_str}' es un perpetuo y solo se opera en paper: "
                "la ejecución live no maneja contratos, apalancamiento ni cortos."
            )
        return symbol_str

    @staticmethod
    def _send(call) -> dict[str, Any]:
        """Envía al exchange traduciendo los errores de ccxt a los del dominio."""
        try:
            return call()
        except ccxt.InsufficientFunds as e:
            raise RuntimeError(f"Fondos insuficientes en el exchange: {e}")
        except ccxt.InvalidOrder as e:
            raise RuntimeError(f"Orden inválida rechazada por el exchange: {e}")
        except (ccxt.RequestTimeout, ccxt.NetworkError) as e:
            # La petición pudo llegar: no se puede asumir que la orden no existe.
            raise ExecutionUncertainError(f"Sin respuesta del exchange: {e}")
        except ccxt.ExchangeError as e:
            raise RuntimeError(f"Error del exchange: {e}")
        except Exception as e:
            raise ExecutionUncertainError(f"Error inesperado al enviar la orden: {e}")

    @staticmethod
    def _find_by_client_id(client, symbol: str, client_order_id: str) -> dict[str, Any] | None:
        for method in ("fetch_open_orders", "fetch_closed_orders"):
            try:
                orders = getattr(client, method)(symbol)
            except (ccxt.NotSupported, ccxt.ArgumentsRequired):
                continue
            for item in orders or []:
                if item.get("clientOrderId") == client_order_id:
                    return item
        return None

    @staticmethod
    def _to_result(order: Order, response: dict) -> ExecutionResult:
        """
        Traduce la respuesta de ccxt al resultado de dominio.

        Solo se registra un Fill con lo que el exchange dice que se ejecutó
        (`filled`) y a un precio conocido (`average`, o `cost / filled`).
        Nunca se inventa precio 0 ni se asume ejecución total.
        """
        exchange_order_id = str(response.get("id") or "") or None

        filled_raw = response.get("filled")
        filled = Decimal(str(filled_raw)) if filled_raw is not None else None

        if response.get("status") == "closed" and filled is None:
            filled = Decimal(str(response.get("amount") or order.qty))

        if not filled or filled <= Decimal("0"):
            # Sin ejecución: abierta en el libro, o cerrada sin ejecutarse
            status = _CCXT_FINAL_STATUS.get(str(response.get("status") or ""), "sent")
            return ExecutionResult(status=status, exchange_order_id=exchange_order_id)

        # Precio real: `average`, o `cost / filled`. `price` es el último
        # recurso: en una límite es el precio límite, no el de ejecución (una
        # límite que se ejecutó a mejor precio quedaría con el P&L mal).
        if response.get("average"):
            exec_price = Decimal(str(response["average"]))
        elif response.get("cost"):
            exec_price = Decimal(str(response["cost"])) / filled
        elif response.get("price"):
            exec_price = Decimal(str(response["price"]))
        else:
            raise ExecutionUncertainError(
                "El exchange reportó la ejecución sin precio; hay que reconciliar la orden."
            )

        fee_info = response.get("fee") or {}
        now = utc_now()
        fill = Fill(
            id=0,
            order_id=order.id,
            exchange_trade_id=exchange_order_id,
            qty=filled,
            price=exec_price,
            fee=Decimal(str(fee_info.get("cost") or 0)),
            fee_asset=fee_info.get("currency"),
            ts=now,
            created_at=now,
        )
        status = "filled" if filled >= order.qty else "partially_filled"
        return ExecutionResult(status=status, exchange_order_id=exchange_order_id, fill=fill)
