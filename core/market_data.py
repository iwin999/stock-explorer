"""Fetching prices and company names from Yahoo Finance (via yfinance).

Every function here catches its own errors and returns None on failure, so the
screen code can show a friendly message instead of crashing. (The senior's code
used `lambda: show_error(f"...{e}")` - by the time the lambda ran, Python had
already deleted `e`, which caused a second error. We avoid lambdas completely.)
"""
import json
import logging
import os

import pandas as pd
import yfinance as yf

log = logging.getLogger(__name__)

# Folder holding the pre-downloaded backup files (made by scripts/download_offline_data.py)
OFFLINE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "offline")


def get_quote(symbol):
    """Latest price and previous close as {"price": x, "previous_close": y}, or None.

    Yahoo's quick "fast_info" gives both numbers in one light request (the keys are
    camelCase: lastPrice, previousClose). If that fails we fall back to the last two
    DAILY candles. The senior's version downloaded 2 days of 1-MINUTE candles just to
    read one number.
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.fast_info
        price, prev = info.get("lastPrice"), info.get("previousClose")
        if price and price > 0:
            return {"price": float(price), "previous_close": float(prev) if prev else None}
        hist = ticker.history(period="5d", interval="1d")
        if not hist.empty:
            closes = hist["Close"]
            return {"price": float(closes.iloc[-1]),
                    "previous_close": float(closes.iloc[-2]) if len(closes) > 1 else None}
    except Exception:
        log.exception("Could not fetch quote for %s", symbol)
    return None


def get_latest_price(symbol):
    """Latest price as a float, or None if unavailable."""
    quote = get_quote(symbol)
    return quote["price"] if quote else None


def get_company_name(symbol):
    """Full company name, or the ticker itself if Yahoo doesn't give one.

    Senior's version read 'longName' from fast_info, which never contains it -
    that's why names always showed N/A. The name lives in ticker.info.
    """
    try:
        info = yf.Ticker(symbol).info
        name = info.get("longName") or info.get("shortName")
        if name:
            return name
    except Exception:
        log.exception("Could not fetch name for %s", symbol)
    return symbol


def get_history(symbol, period="5y"):
    """Daily price history (Open/High/Low/Close/Volume) as a DataFrame, or None.

    We fetch 5 years once and slice it later: the 200-day average needs about
    200 days of 'warm-up' data before the 1-year chart even starts, and the
    backtest (a later step) needs 5 years anyway.
    """
    try:
        hist = yf.Ticker(symbol).history(period=period, interval="1d")
        if hist is not None and not hist.empty:
            hist.index = hist.index.tz_localize(None)  # drop timezone for simpler maths
            return hist[["Open", "High", "Low", "Close", "Volume"]].dropna()
    except Exception:
        log.exception("Could not fetch history for %s", symbol)
    return None


# ---------------- offline backup (feature 7) ----------------
def offline_path(symbol, folder=None):
    """File name for a ticker. '&' is not safe in file names (M&M.NS), so we swap it."""
    return os.path.join(folder or OFFLINE_DIR, symbol.replace("&", "_and_") + ".csv")


def save_offline(symbol, hist, folder=None):
    """Write one stock's history to its backup file."""
    folder = folder or OFFLINE_DIR
    os.makedirs(folder, exist_ok=True)
    hist.to_csv(offline_path(symbol, folder))


def load_offline(symbol, folder=None):
    """Read a stock's backup file, or None if we don't have one / it is damaged."""
    try:
        df = pd.read_csv(offline_path(symbol, folder), index_col=0, parse_dates=True)
        return df.dropna() if not df.empty else None
    except Exception:
        return None


def get_history_with_source(symbol, period="7y"):
    """Try the internet first; if that fails, use the saved backup.

    Returns (DataFrame or None, source, last_date) where source is "online" or "offline".
    The screen uses `source` to warn visitors when they are seeing saved data.
    """
    hist = get_history(symbol, period)
    if hist is not None:
        return hist, "online", hist.index[-1]
    saved = load_offline(symbol)
    if saved is not None:
        log.warning("Using offline backup for %s", symbol)
        return saved, "offline", saved.index[-1]
    return None, "none", None
