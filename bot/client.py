"""
client.py

This is the low-level Binance Futures REST client. Everything that talks
to the API lives here — signing requests, setting headers, handling HTTP
errors, and interpreting Binance's slightly quirky error format.

I chose to use raw `requests` calls instead of ccxt or python-binance because
it makes it much clearer what's happening at the HTTP level. When something
breaks (and it will), you can read the logs and know exactly what was sent.
"""

import hashlib
import hmac
import logging
import time

import requests

BASE_URL = "https://testnet.binancefuture.com"

logger = logging.getLogger("trading_bot")


class BinanceClient:
    """
    A thin wrapper around the Binance Futures REST API.

    Handles the boring stuff (auth headers, HMAC signing, error parsing)
    so the rest of the code can focus on what it's actually trying to do.
    """

    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret

        # Reuse a single session across requests — faster than creating a new
        # connection every time, and keeps the API key header in one place.
        self.session = requests.Session()
        self.session.headers.update({
            "X-MBX-APIKEY": self.api_key,
        })

    # ─── Auth / Signing ────────────────────────────────────────────────────────

    def _sign(self, params: dict) -> dict:
        """
        Binance requires every authenticated request to include:
          - a `timestamp` (milliseconds since epoch)
          - a `signature` (HMAC-SHA256 of all query params)

        Requests more than 5 seconds old are rejected outright, which is
        worth knowing if you're ever debugging a 'timestamp' error.
        """
        params["timestamp"] = int(time.time() * 1000)

        # Build the raw query string that we'll sign
        query_string = "&".join(f"{k}={v}" for k, v in params.items())

        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        params["signature"] = signature
        return params

    # ─── Public Methods ────────────────────────────────────────────────────────

    def ping(self) -> bool:
        """
        Hits the lightweight /ping endpoint to confirm the testnet is reachable.
        Used before every CLI run so we fail fast with a clear message rather
        than timing out mid-order.
        """
        try:
            resp = self.session.get(f"{BASE_URL}/fapi/v1/ping", timeout=5)
            return resp.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def get_account_info(self) -> dict:
        """
        Returns your testnet account state — balances, positions, margin info.
        Mostly useful for sanity checks while debugging, not called by the CLI.
        """
        params = self._sign({})
        resp = self.session.get(
            f"{BASE_URL}/fapi/v2/account",
            params=params,
            timeout=10,
        )
        self._raise_for_api_error(resp)
        return resp.json()

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float = None,
    ) -> dict:
        """
        Places a MARKET or LIMIT order and returns the raw API response.

        A few Binance quirks worth knowing:
          - LIMIT orders need `timeInForce`. We always use GTC (Good Till Cancelled).
          - For MARKET orders, omit `price` entirely — passing it causes an error.
          - `avgPrice` in the response may come back as '0' for MARKET orders that
            haven't fully settled yet. That's normal, not a bug.

        Raises requests.HTTPError on any Binance API error (negative `code` field).
        Raises requests.exceptions.Timeout or ConnectionError on network problems.
        """
        endpoint = f"{BASE_URL}/fapi/v1/order"

        params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
        }

        if order_type == "LIMIT":
            params["price"] = price
            params["timeInForce"] = "GTC"

        params = self._sign(params)
        logger.debug(f"POST {endpoint} | params={params}")

        try:
            resp = self.session.post(endpoint, data=params, timeout=10)
            logger.debug(f"Response {resp.status_code}: {resp.text}")
            self._raise_for_api_error(resp)
            return resp.json()

        except requests.exceptions.Timeout:
            logger.error("Request timed out — testnet may be overloaded or unreachable")
            raise

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Network error while placing order: {e}")
            raise

    # ─── Internal Helpers ──────────────────────────────────────────────────────

    def _raise_for_api_error(self, resp: requests.Response):
        """
        Binance has an unusual error format — they return HTTP 200 even for
        logical failures (e.g. insufficient margin, bad symbol), and signal
        the problem via a negative `code` field in the JSON body.

        This method checks for both that pattern and actual HTTP error codes,
        so callers don't have to think about either case.
        """
        try:
            body = resp.json()
        except Exception:
            resp.raise_for_status()
            return

        if isinstance(body, dict) and body.get("code", 0) < 0:
            error_msg = f"Binance API error {body['code']}: {body.get('msg', 'unknown error')}"
            logger.error(error_msg)
            raise requests.HTTPError(error_msg, response=resp)

        if not resp.ok:
            resp.raise_for_status()