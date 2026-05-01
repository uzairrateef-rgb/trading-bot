"""
orders.py

Handles the actual order placement flow — logging, printing, sending, and
reporting back. Kept separate from the client so there's a clear line between
"talking to the API" and "deciding what to say and how to display it".
"""

import logging

from bot.client import BinanceClient

logger = logging.getLogger("trading_bot")

# Just a visual divider — makes the terminal output easier to scan quickly
DIVIDER = "─" * 50


def _print_request_summary(symbol, side, order_type, quantity, price=None):
    """
    Prints what we're about to send before we actually send it.
    Gives you a chance to catch a typo in the quantity or wrong side
    before the order hits the exchange.
    """
    print(f"\n{DIVIDER}")
    print("  ORDER REQUEST")
    print(DIVIDER)
    print(f"  Symbol     : {symbol}")
    print(f"  Side       : {side}")
    print(f"  Type       : {order_type}")
    print(f"  Quantity   : {quantity}")
    if price is not None:
        print(f"  Price      : {price}")
    print(f"{DIVIDER}\n")


def _print_order_response(resp: dict):
    """
    Pulls out the fields that actually matter and prints them in a clean table.

    Side note: avgPrice will show '0' on MARKET orders immediately after
    placement — Binance populates it once the trade settles. This is expected.
    """
    print(f"\n{DIVIDER}")
    print("  ORDER RESPONSE")
    print(DIVIDER)
    print(f"  Order ID     : {resp.get('orderId', 'N/A')}")
    print(f"  Client OID   : {resp.get('clientOrderId', 'N/A')}")
    print(f"  Symbol       : {resp.get('symbol', 'N/A')}")
    print(f"  Side         : {resp.get('side', 'N/A')}")
    print(f"  Type         : {resp.get('type', 'N/A')}")
    print(f"  Status       : {resp.get('status', 'N/A')}")
    print(f"  Exec Qty     : {resp.get('executedQty', '0')}")
    print(f"  Avg Price    : {resp.get('avgPrice', '0')}")
    # origQty is the right field here, but fall back to 'quantity' just in case
    orig_qty = resp.get("origQty", resp.get("quantity", "N/A"))
    print(f"  Orig Qty     : {orig_qty}")
    print(f"{DIVIDER}")


def place_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: float = None,
) -> dict:
    """
    Top-level function for placing an order. Wraps the client call with
    logging, terminal output, and error handling.

    Flow:
      1. Log + print the request details
      2. Call the API
      3. Log + print the response
      4. Print a clear success or failure message

    Returns the raw API response dict on success.
    Re-raises any exception on failure so the CLI can exit cleanly with code 1.
    """
    price_note = f" @ {price}" if price else ""
    logger.info(f"Order request | {order_type} {side} {quantity} {symbol}{price_note}")
    _print_request_summary(symbol, side, order_type, quantity, price)

    try:
        resp = client.place_order(symbol, side, order_type, quantity, price)
    except Exception as e:
        logger.error(f"Order placement failed: {e}")
        print(f"\n  ❌  Order failed: {e}\n")
        raise

    logger.info(
        f"Order placed | orderId={resp.get('orderId')} "
        f"status={resp.get('status')} "
        f"execQty={resp.get('executedQty')} "
        f"avgPrice={resp.get('avgPrice')}"
    )
    logger.debug(f"Full response payload: {resp}")

    _print_order_response(resp)
    print(f"\n  ✅  Order placed successfully!\n")

    return resp