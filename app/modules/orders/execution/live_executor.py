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
# 5. Traducir la respuesta al estado real (sin asumir ejecución total)
#
# Exchanges soportados: los de CCXT_EXCHANGE_MAP (M2, ccxt_exchanges.py).
# Solo spot: los perpetuos (`XAU/USDT:USDT`) se rechazan, porque ccxt
# interpreta `amount` como contratos y no hay apalancamiento ni cortos.
# ======================================================================

from __future__ import annotations

from decimal import Decimal

import ccxt

from app.common.security.credentials_cipher import CredentialsCipher
from app.common.utils.datetime_utils import utc_now
from app.modules.accounts.domain.account_repository import AccountRepository
from app.modules.bots.domain.bot_entity import Bot
from app.modules.market.domain.ccxt_exchanges import CCXT_EXCHANGE_MAP, ccxt_id_for, is_perpetual
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

    def execute(self, order: Order, bot: Bot) -> ExecutionResult:
        """
        Envía la orden al exchange real y retorna su resultado, con el Fill
        (precio, cantidad y comisión reales) si se ejecutó algo.

        Raises:
            ExecutionUncertainError: timeout o error de red tras enviarla.
            RuntimeError: ante cualquier error de configuración,
                          credenciales o rechazo del exchange.
        """
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

        # 2. Validar credenciales cifradas
        enc_creds = account.meta.get("enc_creds")
        if not enc_creds:
            raise RuntimeError(
                "La cuenta no tiene credenciales API configuradas. "
                "Agrega api_key y api_secret desde la página de cuentas."
            )

        # 3. Descifrar credenciales
        try:
            creds = self._cipher.decrypt(enc_creds)
        except Exception:
            raise RuntimeError(
                "No se pudieron descifrar las credenciales API. "
                "Reconfigura las credenciales de la cuenta."
            )

        api_key: str = creds.get("api_key", "")
        api_secret: str = creds.get("api_secret", "")

        if not api_key or not api_secret:
            raise RuntimeError(
                "Las credenciales API están incompletas (api_key o api_secret vacíos)."
            )

        # 4. Resolver exchange via account.exchange_id
        if account.exchange_id is None:
            raise RuntimeError(
                "La cuenta no tiene un exchange asociado. "
                "Configura el exchange desde la página de cuentas."
            )

        exchange_entity = self._exchange_repo.get_by_id(account.exchange_id)
        if exchange_entity is None:
            raise RuntimeError(
                f"Exchange no encontrado: exchange_id={account.exchange_id}."
            )

        ccxt_id = ccxt_id_for(exchange_entity.name)
        if ccxt_id is None:
            raise RuntimeError(
                f"El exchange '{exchange_entity.name}' no está soportado para live trading. "
                f"Exchanges disponibles: {', '.join(CCXT_EXCHANGE_MAP.keys())}."
            )

        # 5. Inicializar cliente ccxt con credenciales reales
        try:
            exchange_cls = getattr(ccxt, ccxt_id)
            client = exchange_cls({
                "apiKey": api_key,
                "secret": api_secret,
                "enableRateLimit": True,
            })
        except Exception as e:
            raise RuntimeError(
                f"No se pudo inicializar el cliente ccxt para '{ccxt_id}': {e}"
            )

        # 6. Construir parámetros de la orden para ccxt
        # ccxt espera: symbol (str), type (str), side (str), amount (float), price (float|None)
        ccxt_type = _ORDER_TYPE_MAP.get(order.type, order.type)
        ccxt_price = float(order.price) if order.price is not None else None

        params: dict = {}
        if order.stop_price is not None:
            params["stopPrice"] = float(order.stop_price)
        if order.time_in_force is not None:
            params["timeInForce"] = order.time_in_force

        # Necesitamos el símbolo como string (ej: "BTC/USDT")
        # Esto se resuelve via el símbolo asociado al bot
        # Por ahora lo recuperamos desde meta de la orden si fue guardado
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

        # Idempotencia: el exchange rechaza un segundo clientOrderId igual y
        # permite buscar la orden si la respuesta se pierde por red.
        if order.client_order_id:
            params["clientOrderId"] = order.client_order_id

        # 7. Enviar la orden al exchange
        try:
            response = client.create_order(
                symbol=symbol_str,
                type=ccxt_type,
                side=order.side,
                amount=float(order.qty),
                price=ccxt_price,
                params=params,
            )
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

        return self._to_result(order, response)

    # ------------------------------------------------------------------
    # Lógica interna
    # ------------------------------------------------------------------

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
            # Aceptada pero sin ejecutar (límite/stop en el libro)
            return ExecutionResult(status="sent", exchange_order_id=exchange_order_id)

        price_raw = response.get("average") or response.get("price")
        if price_raw:
            exec_price = Decimal(str(price_raw))
        elif response.get("cost"):
            exec_price = Decimal(str(response["cost"])) / filled
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
