# -*- coding: utf-8 -*-

# ======================================================================
# app/modules/orders/execution/live_executor.py
#
# Ejecutor de órdenes en modo live (exchange real via ccxt).
#
# Flujo de ejecución:
# 1. Obtener la cuenta del bot (para exchange y credenciales)
# 2. Inicializar cliente ccxt con las credenciales de la billetera de
#    Binance (BINANCE_API_KEY / BINANCE_API_SECRET del .env)
# 4. Enviar la orden al exchange
# 5. Traducir la respuesta al estado real (filled / partially_filled / sent)
#
# Además de `execute`, expone lo que necesitan la reconciliación y la
# protección nativa (mismo cliente, mismas credenciales):
# - fetch(order, bot)            → estado actual de la orden en el exchange
# - cancel(order, bot)           → cancelar una orden abierta
# - place_stop_loss(order, bot)  → stop loss nativo (si el exchange lo soporta)
# - fetch_funding(bot, symbol, since) → funding cobrado/pagado de un perpetuo
#
# Exchange: Binance (CCXT_EXCHANGE_MAP, M2). Spot y perpetuos USDⓈ-M
# (`XAU/USDT:USDT`: metales, materias primas, ETFs, acciones) desde el
# 2026-10-26, con estas reglas en los perpetuos:
# - Solo largos: toda venta y todo stop loss llevan `reduceOnly` (nunca
#   abren un corto aunque la posición ya se haya cerrado en el exchange).
# - 1x y margen aislado: antes de la primera compra de cada símbolo se fija
#   `isolated` y apalancamiento 1 (una pérdida no toca el resto de la
#   billetera de Futuros). La cuenta debe estar en modo one-way.
# - El USDT debe estar en la billetera de Futuros (lo pasa un super admin a
#   mano): antes de comprar se revisa el margen libre.
# - Binance no devuelve la comisión al crear una orden de futuros: se suma
#   de los trades de la orden.
#
# Cantidades: se redondean a la precisión del mercado (hacia abajo) y se
# revisan los mínimos de cantidad y de valor. La orden queda con la cantidad
# que de verdad se envió (`order.qty`), y el llamador la guarda.
#
# LIVE_USE_SANDBOX=true usa la testnet del exchange (set_sandbox_mode):
# permite probar todo el circuito live sin dinero real.
# ======================================================================

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

import ccxt

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

logger = logging.getLogger(__name__)

# Margen extra al revisar el margen libre de Futuros (comisión y redondeos)
_MARGIN_BUFFER = Decimal("1.01")


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

    # (cuenta, símbolo) ya preparados en este proceso: aislado, 1x y one-way
    _prepared: set[tuple[int, str]] = set()

    def __init__(
        self,
        account_repo: AccountRepository,
        exchange_repo: ExchangeRepository,
    ):
        self._account_repo = account_repo
        self._exchange_repo = exchange_repo

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
        market = self._market(client, symbol_str)
        perpetual = is_perpetual(symbol_str)
        # Las compras abren posición: revisan mínimos; vender cierra lo que hay
        order.qty = self._precise_amount(
            client, market, symbol_str, order, check_minimums=order.side == "buy"
        )

        # ccxt espera: symbol (str), type (str), side (str), amount (float), price (float|None)
        ccxt_type = _ORDER_TYPE_MAP.get(order.type, order.type)
        ccxt_price = float(order.price) if order.price is not None else None

        params: dict = {}
        if perpetual:
            if order.side == "buy":
                self._prepare_perpetual(client, bot, symbol_str)
                self._check_futures_margin(client, market, order)
            else:
                params["reduceOnly"] = True
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
        return self._to_result(order, self._with_fee(client, symbol_str, response))

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
        market = self._market(client, symbol_str)
        order.qty = self._precise_amount(client, market, symbol_str, order, check_minimums=False)
        params: dict = {}
        if order.client_order_id:
            params["clientOrderId"] = order.client_order_id
        if is_perpetual(symbol_str):
            # Solo cierra el largo: si la posición ya no está, no abre un corto
            params["reduceOnly"] = True

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
                remote = client.fetch_order(order.exchange_order_id, symbol_str)
            elif not order.client_order_id:
                return None
            else:
                try:
                    remote = client.fetch_order(
                        None, symbol_str, {"clientOrderId": order.client_order_id}
                    )
                except (ccxt.ArgumentsRequired, ccxt.NotSupported, ccxt.BadRequest):
                    remote = self._find_by_client_id(client, symbol_str, order.client_order_id)
            return self._with_fee(client, symbol_str, remote) if remote else remote
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

    def fetch_funding(self, bot: Bot, symbol: str, since_ms: int | None) -> list[dict[str, Any]]:
        """
        Historial de funding del perpetuo en la cuenta del bot desde `since_ms`
        (`{id, amount, code, timestamp}` de ccxt).

        Raises:
            ExecutionUncertainError: error de red (se reintenta luego).
            RuntimeError: configuración o error del exchange.
        """
        client = self._build_client(bot)
        try:
            return client.fetch_funding_history(symbol, since_ms) or []
        except (ccxt.RequestTimeout, ccxt.NetworkError) as e:
            raise ExecutionUncertainError(f"Sin respuesta del exchange: {e}")
        except ccxt.BaseError as e:
            raise RuntimeError(f"Error del exchange al leer el funding: {e}")

    # ==================================================================
    # Lógica interna
    # ==================================================================

    def _build_client(self, bot: Bot):
        """Cliente ccxt autenticado con las credenciales de la cuenta del bot."""
        # 1. Obtener cuenta del bot
        if bot.account_id is None:
            raise RuntimeError("El agente real no está ligado a la billetera de Binance.")

        account = self._account_repo.get_by_id(bot.account_id)
        if account is None:
            raise RuntimeError(
                f"Cuenta no encontrada: account_id={bot.account_id}."
            )

        # 2. Cliente ccxt con las credenciales de la billetera (helper
        #    compartido con la billetera de la plataforma; respeta LIVE_USE_SANDBOX)
        return build_authenticated_client(account, self._exchange_repo)

    @staticmethod
    def _order_symbol(order: Order) -> str:
        """Símbolo unificado guardado en meta por CreateOrderService."""
        symbol_str = order.meta.get("symbol")
        if not symbol_str:
            raise RuntimeError(
                "La orden no tiene el símbolo en meta. "
                "Asegúrate de que CreateOrderService lo incluya."
            )
        return symbol_str

    @staticmethod
    def _market(client, symbol: str) -> dict[str, Any]:
        """Mercado de ccxt (precisión, mínimos, tipo); carga los mercados una vez por cliente."""
        try:
            client.load_markets()
            market = client.market(symbol)
        except ccxt.BadSymbol as e:
            raise RuntimeError(f"El exchange no tiene el mercado '{symbol}': {e}")
        except (ccxt.RequestTimeout, ccxt.NetworkError) as e:
            raise ExecutionUncertainError(f"Sin respuesta del exchange al cargar los mercados: {e}")
        except ccxt.BaseError as e:
            raise RuntimeError(f"No se pudieron cargar los mercados del exchange: {e}")
        contract_size = market.get("contractSize")
        if market.get("contract") and contract_size not in (None, 1, 1.0):
            # Un contrato que no vale 1 unidad cambiaría tamaños y P&L: no se opera
            raise RuntimeError(
                f"'{symbol}' tiene contratos de {contract_size} unidades; la app solo opera "
                "perpetuos de 1 unidad por contrato."
            )
        return market

    @staticmethod
    def _precise_amount(
        client, market: dict[str, Any], symbol: str, order: Order, *, check_minimums: bool
    ) -> Decimal:
        """
        Cantidad redondeada (hacia abajo) a la precisión del mercado. En las
        compras revisa además el mínimo de cantidad y de valor: una compra
        que el exchange rechazaría se rechaza aquí con un motivo claro.
        """
        try:
            amount = Decimal(str(client.amount_to_precision(symbol, float(order.qty))))
        except ccxt.BaseError:
            amount = Decimal("0")
        limits = market.get("limits") or {}
        min_amount = (limits.get("amount") or {}).get("min")
        if amount <= 0 or (check_minimums and min_amount and amount < Decimal(str(min_amount))):
            raise RuntimeError(
                f"La cantidad {order.qty} es menor que el mínimo de {symbol} en el exchange "
                f"({min_amount or 'precisión del mercado'})."
            )
        price = _reference_price(order)
        min_cost = (limits.get("cost") or {}).get("min")
        if check_minimums and price and min_cost and amount * price < Decimal(str(min_cost)):
            raise RuntimeError(
                f"La orden vale {amount * price:.2f} y el mínimo de {symbol} en el exchange "
                f"es {min_cost}."
            )
        return amount

    def _prepare_perpetual(self, client, bot: Bot, symbol: str) -> None:
        """Modo one-way, margen aislado y 1x, una vez por cuenta y símbolo."""
        key = (int(bot.account_id or 0), symbol)
        if key in self._prepared:
            return
        try:
            mode = client.fetch_position_mode(symbol) or {}
            if mode.get("hedged"):
                raise RuntimeError(
                    "La cuenta de Futuros de Binance está en modo de cobertura (Hedge). "
                    "Cámbiala a modo unidireccional (One-way) en las preferencias de Futuros."
                )
            try:
                client.set_margin_mode("isolated", symbol)
            except ccxt.MarginModeAlreadySet:
                pass
            client.set_leverage(1, symbol)
        except (ccxt.RequestTimeout, ccxt.NetworkError) as e:
            # Nada se envió todavía: es seguro rechazar y reintentar después
            raise RuntimeError(f"Sin respuesta del exchange al preparar {symbol}: {e}")
        except ccxt.BaseError as e:
            if "no need to change" not in str(e).lower():
                raise RuntimeError(f"No se pudo fijar margen aislado y 1x en {symbol}: {e}")
        self._prepared.add(key)

    @staticmethod
    def _check_futures_margin(client, market: dict[str, Any], order: Order) -> None:
        """Con 1x la compra usa como margen su valor completo: debe estar libre en Futuros."""
        price = _reference_price(order)
        if not price:
            return
        settle = market.get("settle") or market.get("quote") or "USDT"
        try:
            balance = client.fetch_balance({"type": "future"}) or {}
        except ccxt.BaseError as e:
            raise RuntimeError(f"No se pudo leer el margen de la billetera de Futuros: {e}")
        free = Decimal(str((balance.get(settle) or {}).get("free") or 0))
        needed = order.qty * price * _MARGIN_BUFFER
        if free < needed:
            raise RuntimeError(
                f"Margen insuficiente en la billetera de Futuros de Binance: hay {free:.2f} "
                f"{settle} libres y la orden necesita {needed:.2f}. Transfiere {settle} de "
                "Spot a Futuros."
            )

    @staticmethod
    def _with_fee(client, symbol: str, response: dict[str, Any]) -> dict[str, Any]:
        """
        Completa la comisión cuando la respuesta no la trae (Binance Futuros):
        suma la de los trades de la orden. Si falla, sigue sin comisión.
        """
        if (response.get("fee") or {}).get("cost") is not None or not response.get("filled"):
            return response
        if not response.get("id") or not client.has.get("fetchOrderTrades"):
            return response
        try:
            trades = client.fetch_order_trades(response["id"], symbol) or []
        except ccxt.BaseError as e:
            logger.warning("[Live] No se pudo leer la comisión de la orden %s: %s", response.get("id"), e)
            return response
        cost = Decimal("0")
        currency = None
        for trade in trades:
            fee = trade.get("fee") or {}
            if fee.get("cost") is not None:
                cost += Decimal(str(fee["cost"]))
                currency = currency or fee.get("currency")
        if currency is None:
            return response
        return {**response, "fee": {"cost": float(cost), "currency": currency}}

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
        # `order.qty` ya es la cantidad redondeada que se envió
        status = "filled" if filled >= order.qty else "partially_filled"
        return ExecutionResult(status=status, exchange_order_id=exchange_order_id, fill=fill)


def _reference_price(order: Order) -> Decimal | None:
    """Precio para valorar la orden: límite, stop o el de referencia que guardó el servicio."""
    for value in (order.price, order.stop_price, order.meta.get("reference_price")):
        if value:
            return Decimal(str(value))
    return None
