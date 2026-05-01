"""
validators.py

All CLI input validation lives here. Each function raises a ValueError with
a descriptive message if something looks wrong — the CLI layer catches those
and prints them cleanly without a traceback flooding the screen.

Keeping validation separate from order logic means it's easy to test in
isolation and reuse if we ever add a web UI or interactive prompt later.
"""

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT"}

# Approximate minimum quantities per symbol on Binance Futures Testnet.
# Binance will reject orders below these with a MIN_NOTIONAL or LOT_SIZE error.
# These are reasonable defaults — update them if you start hitting -1111 errors.
MIN_QTY = {
    "BTCUSDT": 0.001,
    "ETHUSDT": 0.01,
    "SOLUSDT": 0.1,
}
DEFAULT_MIN_QTY = 0.001  # fallback for symbols not in the table above


def validate_symbol(symbol: str) -> str:
    """
    Normalises the symbol to uppercase and checks it looks like a USDT-M pair.
    We're only wired up to the USDT-margined testnet, so COIN-margined pairs
    (which end in things like BUSD or are BTCUSD_PERP) will fail at the API level
    anyway — better to catch them here with a useful message.
    """
    s = symbol.upper().strip()
    if len(s) < 5:
        raise ValueError(
            f"'{symbol}' doesn't look right. Expected something like BTCUSDT or ETHUSDT."
        )
    if not s.endswith("USDT"):
        raise ValueError(
            f"Only USDT-margined perpetuals are supported. Got: '{symbol}'. "
            f"Try BTCUSDT, ETHUSDT, or SOLUSDT."
        )
    return s


def validate_side(side: str) -> str:
    """Accepts BUY/SELL in any case, returns the uppercase version."""
    s = side.upper().strip()
    if s not in VALID_SIDES:
        raise ValueError(f"Side must be BUY or SELL, got: '{side}'")
    return s


def validate_order_type(order_type: str) -> str:
    """Accepts MARKET/LIMIT in any case, returns uppercase."""
    t = order_type.upper().strip()
    if t not in VALID_ORDER_TYPES:
        raise ValueError(f"Order type must be MARKET or LIMIT, got: '{order_type}'")
    return t


def validate_quantity(qty_str: str, symbol: str = None) -> float:
    """
    Parses and validates the quantity string.

    We raise an error (rather than just a warning) if the quantity is below
    Binance's minimum — there's no point sending a request we know will be
    rejected. The min values are approximate; if you hit -1111 errors with a
    quantity that should be fine, the exchange's lot size rules may have changed.
    """
    try:
        qty = float(qty_str)
    except (ValueError, TypeError):
        raise ValueError(f"Quantity must be a number, got: '{qty_str}'")

    if qty <= 0:
        raise ValueError(f"Quantity must be greater than zero, got: {qty}")

    min_qty = MIN_QTY.get(symbol, DEFAULT_MIN_QTY) if symbol else DEFAULT_MIN_QTY
    if qty < min_qty:
        raise ValueError(
            f"Quantity {qty} is below the minimum for {symbol or 'this pair'} "
            f"({min_qty}). Binance will reject the order with a LOT_SIZE error."
        )

    return qty


def validate_price(price_str: str) -> float:
    """Parses and validates the price string for LIMIT orders."""
    try:
        price = float(price_str)
    except (ValueError, TypeError):
        raise ValueError(f"Price must be a number, got: '{price_str}'")

    if price <= 0:
        raise ValueError(f"Price must be greater than zero, got: {price}")

    return price


def validate_all(symbol, side, order_type, qty_str, price_str=None):
    """
    Runs every validator in sequence and returns clean, normalised values.
    Raises ValueError on the first problem it finds — one error at a time
    is easier to act on than a dump of everything wrong at once.

    Returns: (symbol, side, order_type, quantity, price)
    """
    symbol = validate_symbol(symbol)
    side = validate_side(side)
    order_type = validate_order_type(order_type)
    quantity = validate_quantity(qty_str, symbol)

    price = None
    if order_type == "LIMIT":
        if not price_str:
            raise ValueError("--price is required for LIMIT orders.")
        price = validate_price(price_str)
    elif price_str:
        # Not an error — just silently ignore the price for MARKET orders
        # and let the user know so they're not confused when it doesn't appear
        # in the response.
        print("  ⚠️  Note: --price is ignored for MARKET orders.\n")

    return symbol, side, order_type, quantity, price