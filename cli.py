"""
cli.py — Entry point for the Binance Futures Testnet order placer.

This is the only script you need to run manually. It ties together argument
parsing, credential loading, input validation, connectivity checks, and
order placement — in that order, so failures are caught as early as possible.

Usage:
  python cli.py --symbol BTCUSDT --side BUY  --type MARKET --qty 0.001
  python cli.py --symbol ETHUSDT --side SELL --type LIMIT  --qty 0.01 --price 3200.00
  python cli.py --symbol SOLUSDT --side BUY  --type MARKET --qty 0.5
"""

import argparse
import os
import sys

from dotenv import load_dotenv
load_dotenv()

from bot.client import BinanceClient
from bot.logging_config import setup_logging
from bot.orders import place_order
from bot.validators import validate_all


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description=(
            "Binance Futures Testnet — Manual Order Placer\n"
            "All orders go to the testnet. No real money is involved."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  Market buy:  python cli.py --symbol BTCUSDT --side BUY  --type MARKET --qty 0.001\n"
            "  Limit sell:  python cli.py --symbol ETHUSDT --side SELL --type LIMIT  --qty 0.01 --price 3200.00\n"
        ),
    )

    parser.add_argument(
        "--symbol",
        required=True,
        metavar="SYMBOL",
        help="Trading pair, e.g. BTCUSDT, ETHUSDT, SOLUSDT",
    )
    parser.add_argument(
        "--side",
        required=True,
        choices=["BUY", "SELL", "buy", "sell"],
        metavar="SIDE",
        help="Direction: BUY or SELL",
    )
    parser.add_argument(
        "--type",
        dest="order_type",
        required=True,
        choices=["MARKET", "LIMIT", "market", "limit"],
        metavar="TYPE",
        help="Order type: MARKET or LIMIT",
    )
    parser.add_argument(
        "--qty",
        required=True,
        metavar="QTY",
        help="Amount in base currency (e.g. 0.001 for BTC)",
    )
    parser.add_argument(
        "--price",
        required=False,
        default=None,
        metavar="PRICE",
        help="Limit price in USDT — required for LIMIT orders, ignored for MARKET",
    )

    return parser


def load_credentials():
    """
    Reads API keys from the .env file. Exits immediately with a clear message
    if either key is missing — better to fail here than get a cryptic 401 later.
    """
    load_dotenv()
    api_key = os.getenv("BINANCE_API_KEY", "").strip()
    api_secret = os.getenv("BINANCE_API_SECRET", "").strip()

    if not api_key or not api_secret:
        print(
            "\n  ❌  Missing API credentials.\n"
            "  Create a .env file in this directory with:\n\n"
            "      BINANCE_API_KEY=your_key_here\n"
            "      BINANCE_API_SECRET=your_secret_here\n"
        )
        sys.exit(1)

    return api_key, api_secret


def main():
    logger = setup_logging()

    parser = build_parser()
    args = parser.parse_args()

    api_key, api_secret = load_credentials()

    # Validate + normalise all inputs before touching the network
    try:
        symbol, side, order_type, quantity, price = validate_all(
            args.symbol, args.side, args.order_type, args.qty, args.price
        )
    except ValueError as e:
        print(f"\n  ❌  Input error: {e}\n")
        logger.error(f"Validation failed: {e}")
        sys.exit(1)

    # Quick connectivity check — fail fast before signing anything
    client = BinanceClient(api_key, api_secret)
    if not client.ping():
        print("\n  ❌  Cannot reach testnet.binancefuture.com — check your internet connection.\n")
        logger.error("Testnet ping failed")
        sys.exit(1)

    logger.info("Testnet connectivity confirmed")

    try:
        place_order(client, symbol, side, order_type, quantity, price)
    except Exception:
        # Error details already logged and printed inside place_order
        sys.exit(1)


if __name__ == "__main__":
    main()