# Binance Futures Testnet — Trading Bot

A Python application for placing **MARKET** and **LIMIT** orders on the **Binance Futures Testnet (USDT-M)** via a clean command-line interface.

The project is split into two parts:
- **`cli.py`** — the main deliverable: a manual order placer with validation, logging, and formatted output
- **`trading_bot.py`** — a bonus automated strategy bot with RSI/EMA signals and a Flask dashboard

Everything runs against the testnet. No real money is touched.

---

## Project Structure

```
trading_bot/
│
├── bot/
│   ├── __init__.py
│   ├── client.py          # REST client: signing, HTTP, error handling
│   ├── orders.py          # Order flow: request/response display + placement
│   ├── validators.py      # Input validation for CLI arguments
│   └── logging_config.py  # File + console logging setup
│
├── cli.py                 # CLI entry point (argparse)
├── trading_bot.py         # Automated strategy bot (bonus)
│
├── logs/                  # Auto-created on first run
├── .env.example           # Copy to .env and fill in your keys
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Setup

### Step 1 — Get Testnet API Keys

1. Go to [testnet.binancefuture.com](https://testnet.binancefuture.com) and log in (GitHub login works)
2. Click **API Management** in the top-right
3. Generate a new key pair — copy both immediately, the secret is only shown once

### Step 2 — Clone and Install

```bash
git clone https://github.com/your-username/trading-bot.git
cd trading-bot

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt
```

### Step 3 — Add Your Credentials

```bash
cp .env.example .env
```

Open `.env` and paste your keys:

```
BINANCE_API_KEY=your_testnet_key_here
BINANCE_API_SECRET=your_testnet_secret_here
```

> ⚠️ Never commit `.env` to version control. It's already in `.gitignore`.

---

## Usage

### Basic Syntax

```bash
python cli.py --symbol <SYMBOL> --side <BUY|SELL> --type <MARKET|LIMIT> --qty <QTY> [--price <PRICE>]
```

### Examples

**Market Buy — 0.001 BTC**
```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --qty 0.001
```

**Limit Sell — 0.01 ETH at $3,200**
```bash
python cli.py --symbol ETHUSDT --side SELL --type LIMIT --qty 0.01 --price 3200.00
```

**Market Sell — 0.5 SOL**
```bash
python cli.py --symbol SOLUSDT --side SELL --type MARKET --qty 0.5
```

**Help**
```bash
python cli.py --help
```

### What the Output Looks Like

```
──────────────────────────────────────────────────
  ORDER REQUEST
──────────────────────────────────────────────────
  Symbol     : BTCUSDT
  Side       : BUY
  Type       : MARKET
  Quantity   : 0.001
──────────────────────────────────────────────────

──────────────────────────────────────────────────
  ORDER RESPONSE
──────────────────────────────────────────────────
  Order ID     : 3928471234
  Client OID   : web_abc123...
  Symbol       : BTCUSDT
  Side         : BUY
  Type         : MARKET
  Status       : FILLED
  Exec Qty     : 0.001
  Avg Price    : 67842.30
  Orig Qty     : 0.001
──────────────────────────────────────────────────

  ✅  Order placed successfully!
```

---

## Logging

Logs are written to `logs/trading_YYYYMMDD.log` on every run.

- **File**: captures everything — DEBUG level, including raw API payloads
- **Terminal**: INFO and above only, so the output stays readable

Sample log output:

```
2024-01-15 14:23:01 | INFO     | Logging initialised — writing to logs/trading_20240115.log
2024-01-15 14:23:01 | INFO     | Testnet connectivity confirmed
2024-01-15 14:23:01 | INFO     | Order request | MARKET BUY 0.001 BTCUSDT
2024-01-15 14:23:02 | INFO     | Order placed | orderId=3928471234 status=FILLED execQty=0.001 avgPrice=67842.30
```

---

## Automated Strategy Bot (Bonus)

`trading_bot.py` runs a continuous loop across BTC, ETH, and SOL using:

- **Polymarket odds** — uses probability spikes as leading indicators
- **RSI** — detects oversold/overbought conditions
- **200-period EMA** — filters trades to align with the macro trend
- **ATR trailing stops** and partial profit-taking
- **Flask dashboard** at `http://127.0.0.1:5000`

```bash
pip install "ccxt[pro]" aiohttp aiodns
python trading_bot.py
```

Then open `http://127.0.0.1:5000` to view the live dashboard.

---

## Troubleshooting

| Error | Likely Cause | Fix |
|---|---|---|
| `Missing API credentials` | `.env` file missing or incomplete | Create `.env` with both keys |
| `Cannot reach testnet` | Network issue or testnet is down | Check connection; testnet occasionally has downtime |
| `Binance API error -2019` | Insufficient margin | Reset testnet balance from the testnet dashboard |
| `Binance API error -1121` | Invalid symbol | Use format like `BTCUSDT`, not `BTC-USDT` |
| `Binance API error -1111` | Quantity below lot size | Increase `--qty` (BTC minimum is 0.001) |
| `Timestamp` errors | System clock out of sync | Sync your system clock |

---

## Assumptions

- Only **USDT-margined perpetual futures** are supported (`BTCUSDT`, `ETHUSDT`, `SOLUSDT`, etc.)
- All traffic goes to `testnet.binancefuture.com` — mainnet is never touched
- LIMIT orders use `timeInForce=GTC` (Good Till Cancelled)
- Testnet balances are virtual; reset them on the testnet site if they run out
- The automated bot (`trading_bot.py`) uses its own ccxt-based client, separate from the CLI