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
# 5. Parsear la respuesta y construir el Fill con datos reales
#
# Exchanges soportados (mismo mapa que M2 - FetchCandlesService):
# binance, bybit, kraken, coinbase, bitget, okx
# ======================================================================

from __future__ import annotations

from decimal import Decimal

import ccxt

from app.common.security.credentials_cipher import CredentialsCipher
from app.common.utils.datetime_utils import utc_now
from app.modules.accounts.domain.account_repository import AccountRepository
from app.modules.bots.domain.bot_entity import Bot
from app.modules.market.domain.exchange_repository import ExchangeRepository
from app.modules.orders.domain.fill_entity import Fill
from app.modules.orders.domain.order_entity import Order
from app.modules.orders.execution.executor_interface import ExecutorInterface


# Mapeo nombre del exchange en BD → id de ccxt
# Mismo mapa que FetchCandlesService (M2) para consistencia
_CCXT_EXCHANGE_MAP: dict[str, str] = {
    "binance":  "binance",
    "bybit":    "bybit",
    "kraken":   "kraken",
    "coinbase": "coinbase",
    "bitget":   "bitget",
    "okx":      "okx",
}

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
    5. Construye el Fill con datos reales (precio, cantidad, comisión).

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

    def execute(self, order: Order, bot: Bot) -> Fill:
        """
        Envía la orden al exchange real y retorna el Fill con
        precio, cantidad y comisión reales.

        Raises:
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

        ccxt_id = _CCXT_EXCHANGE_MAP.get(exchange_entity.name.lower())
        if ccxt_id is None:
            raise RuntimeError(
                f"El exchange '{exchange_entity.name}' no está soportado para live trading. "
                f"Exchanges disponibles: {', '.join(_CCXT_EXCHANGE_MAP.keys())}."
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
        except ccxt.NetworkError as e:
            raise RuntimeError(f"Error de red al conectar con el exchange: {e}")
        except ccxt.ExchangeError as e:
            raise RuntimeError(f"Error del exchange: {e}")
        except Exception as e:
            raise RuntimeError(f"Error inesperado al enviar la orden: {e}")

        # 8. Parsear respuesta y construir Fill con datos reales
        # ccxt retorna un dict con: id, price, amount, cost, fee, etc.
        exec_price = Decimal(str(response.get("price") or response.get("average") or 0))
        exec_qty = Decimal(str(response.get("filled") or response.get("amount") or order.qty))

        fee_info = response.get("fee") or {}
        exec_fee = Decimal(str(fee_info.get("cost", 0)))
        fee_asset = fee_info.get("currency")

        exchange_trade_id = str(response.get("id", ""))
        now = utc_now()

        return Fill(
            id=0,
            order_id=order.id,
            exchange_trade_id=exchange_trade_id or None,
            qty=exec_qty,
            price=exec_price,
            fee=exec_fee,
            fee_asset=fee_asset,
            ts=now,
            created_at=now,
        )
