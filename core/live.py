"""Live price lookups shared by all visitors.

st.cache_data(ttl=15) means: if anyone asked for this company in the last 15 seconds,
reuse that answer instead of calling Yahoo again. That keeps the page fast and
stops many visitors from flooding Yahoo with requests.
"""
import streamlit as st

from core import derivatives as dv
from core.market_data import get_history_with_source, get_quote

REFRESH_SECONDS = 15


@st.cache_data(ttl=REFRESH_SECONDS, show_spinner=False)
def live_quote(symbol):
    return get_quote(symbol)


# ---------------- prices used by futures, options and the portfolio dashboard ----------------

@st.cache_data(ttl=3600, show_spinner=False)
def _closes(symbol):
    """Daily closing prices (a pandas Series) from the internet or the saved backup, or None."""
    hist, _, _ = get_history_with_source(symbol, "1y")
    return hist["Close"] if hist is not None else None


def spot_price(symbol):
    """Best available price: the live quote, else the last saved closing price, else None."""
    quote = live_quote(symbol)
    if quote:
        return quote["price"]
    closes = _closes(symbol)
    return float(closes.iloc[-1]) if closes is not None else None


def vol_estimate(symbol):
    """Last-year volatility used to price options on this underlying."""
    closes = _closes(symbol)
    return dv.volatility_for_pricing(closes) if closes is not None else None


def close_on(symbol, expiry):
    """The closing price on a given date (or the last close before it). Used to settle expired contracts."""
    closes = _closes(symbol)
    if closes is None:
        return None
    upto = closes[closes.index <= str(expiry)]
    return float(upto.iloc[-1]) if len(upto) else None
