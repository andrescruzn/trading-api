# -*- coding: utf-8 -*-

# ======================================================================
# scripts/testnet_check.py
#
# PROPÓSITO:
# - Probar el circuito live de M8 contra la TESTNET de un exchange con el
#   LiveExecutor real (mismo código que usa la app), sin tocar la BD:
#     1. compra a mercado
#     2. consultar la compra (fetch)
#     3. stop loss nativo por lo comprado
#     4. consultar y cancelar el stop loss
#     5. límite de compra lejos del precio y cancelarla
#     6. vender a mercado lo comprado (deja la cuenta como estaba)
#
# USO (lo ejecuta una persona, nunca el agente):
#   TESTNET_EXCHANGE=binance TESTNET_API_KEY=... TESTNET_API_SECRET=... \
#   TESTNET_SYMBOL=BTC/USDT TESTNET_QTY=0.001 \
#   uv run python -m scripts.testnet_check --yes
#
# SEGURIDAD:
# - Fuerza LIVE_USE_SANDBOX y se niega a seguir si el cliente no quedó en
#   modo sandbox. Las claves deben ser de la testnet (las de producción no
#   funcionan allí). Sin --yes no envía nada.
# ======================================================================

from __future__ import annotations

import argparse
import os
import sys
from decimal import Decimal
from types import SimpleNamespace

from app.common.config import settings
from app.modules.orders.domain.order_entity import Order
from app.modules.orders.execution.executor_interface import ExecutionUncertainError
from app.modules.orders.execution.live_executor import LiveExecutor


class _EnvCipher:
    """Devuelve las claves de las variables de entorno (sin cifrado: no hay BD)."""

    def decrypt(self, _token: str) -> dict[str, str]:
        return {
            "api_key": os.environ["TESTNET_API_KEY"],
            "api_secret": os.environ["TESTNET_API_SECRET"],
        }


class _Repo:
    def __init__(self, item):
        self._item = item

    def get_by_id(self, _id):
        return self._item


def _order(order_id: int, side: str, order_type: str, qty: Decimal, **extra) -> Order:
    order = Order(
        id=order_id,
        bot_id=0,
        side=side,
        type=order_type,
        qty=qty,
        meta={"symbol": os.environ["TESTNET_SYMBOL"], "mode": "live", "reason": "testnet_check"},
        **extra,
    )
    # clientOrderId único por corrida para no chocar con pruebas anteriores
    order.client_order_id = f"ta-tn-{os.getpid()}-{order_id}"
    return order


def _step(title: str) -> None:
    print(f"\n=== {title}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Prueba el LiveExecutor contra una testnet.")
    parser.add_argument("--yes", action="store_true", help="enviar órdenes de verdad a la testnet")
    args = parser.parse_args()

    missing = [
        name for name in ("TESTNET_EXCHANGE", "TESTNET_API_KEY", "TESTNET_API_SECRET",
                          "TESTNET_SYMBOL", "TESTNET_QTY")
        if not os.environ.get(name)
    ]
    if missing:
        print(f"Faltan variables de entorno: {', '.join(missing)}")
        return 2
    if not args.yes:
        print("Nada enviado. Revisa las variables y vuelve a correr con --yes.")
        return 2

    settings.LIVE_USE_SANDBOX = True
    qty = Decimal(os.environ["TESTNET_QTY"])
    account = SimpleNamespace(meta={"enc_creds": "env"}, exchange_id=1)
    exchange = SimpleNamespace(name=os.environ["TESTNET_EXCHANGE"])
    bot = SimpleNamespace(id=0, account_id=1)
    live = LiveExecutor(account_repo=_Repo(account), exchange_repo=_Repo(exchange), cipher=_EnvCipher())

    client = live._build_client(bot)
    if not getattr(client, "isSandboxModeEnabled", False):
        print("El cliente NO quedó en modo sandbox: se cancela la prueba.")
        return 1
    print(f"Testnet de {client.id} — has createStopLossOrder: {client.has.get('createStopLossOrder')}")

    try:
        _step("1. Compra a mercado")
        buy = _order(1, "buy", "market", qty)
        result = live.execute(buy, bot)
        buy.exchange_order_id = result.exchange_order_id
        print(f"estado={result.status} id={result.exchange_order_id} "
              f"fill={result.fill.qty if result.fill else None} @ {result.fill.price if result.fill else None}")
        if result.fill is None:
            print("La compra no se ejecutó: no se puede seguir.")
            return 1
        filled, price = result.fill.qty, result.fill.price

        _step("2. Consultar la compra")
        remote = live.fetch(buy, bot)
        print(f"status ccxt={remote.get('status') if remote else None} filled={remote.get('filled') if remote else None}")

        _step("3. Stop loss nativo (10 % por debajo)")
        stop = _order(2, "sell", "stop", filled, stop_price=(price * Decimal("0.9")).quantize(Decimal("0.01")))
        try:
            sl = live.place_stop_loss(stop, bot)
            stop.exchange_order_id = sl.exchange_order_id
            print(f"estado={sl.status} id={sl.exchange_order_id}")

            _step("4. Consultar y cancelar el stop loss")
            print(f"status ccxt={(live.fetch(stop, bot) or {}).get('status')}")
            print(f"cancelado={live.cancel(stop, bot)}")
        except RuntimeError as exc:
            print(f"SL nativo no disponible: {exc} (la app usaría el scheduler)")

        _step("5. Límite de compra lejos del precio y cancelarla")
        limit = _order(3, "buy", "limit", qty, price=(price * Decimal("0.5")).quantize(Decimal("0.01")))
        res = live.execute(limit, bot)
        limit.exchange_order_id = res.exchange_order_id
        print(f"estado={res.status} id={res.exchange_order_id} cancelada={live.cancel(limit, bot)}")
        print(f"status tras cancelar={(live.fetch(limit, bot) or {}).get('status')}")

        _step("6. Vender lo comprado")
        sell = live.execute(_order(4, "sell", "market", filled), bot)
        print(f"estado={sell.status} fill={sell.fill.qty if sell.fill else None}")
    except ExecutionUncertainError as exc:
        print(f"\nSin respuesta del exchange: {exc}. Revisa la testnet a mano.")
        return 1
    except RuntimeError as exc:
        print(f"\nEl exchange rechazó un paso: {exc}")
        return 1

    print("\nListo: el circuito live respondió en la testnet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
